"""MASAT API server (for the future UI portal).

This is a minimal job API:
- POST /scan  {target, scans?, smart?}
- GET  /runs

It stores completed runs in the same SQLite DB used by CLI --store.

Run:
  pip install -r requirements.txt -r requirements-api.txt
  uvicorn api.app:app --reload
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "FastAPI dependencies are not installed. Install with: pip install -r requirements-api.txt"
    ) from e

from scanners.registry import discover_scanners
from utils.targets import parse_target
from utils.workflows import plan_scans
from utils.schema import normalize_findings
from utils.expand import expand_domain
from utils.history import (
    default_db_path,
    store_run,
    list_runs,
    count_runs,
    count_runs_since,
    list_latest_runs_per_target,
    list_latest_runs_per_target_asof,
    list_runs_matching_host,
    get_run,
)
from utils.assets import default_assets_db_path, list_assets, count_assets, upsert_asset, Asset
from utils.dashboard import build_dashboard_metrics
from utils.exposure import extract_open_ports_from_results
from utils.ports_summary import summarize_open_ports_by_asset
from utils.issues import (
    Issue,
    default_issues_db_path,
    fingerprint_issue,
    list_issues,
    count_issues,
    upsert_issue,
    update_issue_status,
    now_ts,
)


app = FastAPI(title="MASAT API", version="0.1")

# Allow browser-based UI (Next.js) to call the API during local development.
# For production, restrict origins.
try:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"]
        ,
        allow_headers=["*"],
    )
except Exception:
    pass


class ScanRequest(BaseModel):
    target: str
    scans: str | None = None
    smart: bool = True
    store: bool = True
    db: str | None = None


class SeedRequest(BaseModel):
    domain: str
    use_ct: bool = True
    use_common: bool = True
    use_live_tls: bool = False
    resolve: bool = True
    max_hosts: int = 500
    max_dns_lookups: int = 2000
    dns_concurrency: int = 50


class AssetsImportRequest(BaseModel):
    assets: list[str]
    assets_db: str | None = None
    tags: list[str] = ["seeded"]
    owner: str = ""
    environment: str = ""


class IssueUpdateRequest(BaseModel):
    fingerprint: str
    status: str | None = None
    owner: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _asset_filter_rows(
    assets_rows: list[dict[str, Any]],
    *,
    env: str | None = None,
    owned: bool | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in assets_rows or []:
        if env:
            if str(a.get("environment") or "").strip().lower() != env.strip().lower():
                continue
        if owned is True:
            tags = [str(t).strip().lower() for t in (a.get("tags") or []) if str(t).strip()]
            if "owned" not in tags and "in-scope" not in tags:
                continue
        out.append(a)
    return out


def _run_host(target: str) -> str:
    return (parse_target(target).host or target).strip().lower().rstrip(".")


@app.get("/dashboard")
def dashboard(env: str | None = None, owned: int | None = None) -> dict[str, Any]:
    """Return high-level dashboard metrics.

    This endpoint intentionally returns a single aggregated object so the UI can
    render an enterprise-style dashboard without multiple round trips.
    """

    assets_db = default_assets_db_path()
    runs_db = default_db_path()

    assets_total = count_assets(assets_db)
    # For now, we load at most 5000 assets for metrics breakdown.
    assets_rows_all = [a.to_dict() for a in list_assets(assets_db, limit=min(5000, max(30, assets_total)), offset=0)]

    owned_bool = True if owned == 1 else False if owned == 0 else None
    assets_rows = _asset_filter_rows(assets_rows_all, env=env, owned=owned_bool)
    allowed_hosts = {str(a.get("value") or "").strip().lower().rstrip(".") for a in assets_rows if str(a.get("value") or "").strip()}

    total_runs = count_runs(runs_db)
    now = int(time.time())
    runs_24h = count_runs_since(runs_db, now - 24 * 3600)
    runs_7d = count_runs_since(runs_db, now - 7 * 24 * 3600)

    latest_runs_all = list_latest_runs_per_target(runs_db, limit_targets=300)
    latest_runs = (
        [r for r in latest_runs_all if _run_host(str(r.get("target") or "")) in allowed_hosts]
        if allowed_hosts
        else latest_runs_all
    )

    # Load details for latest runs (cap to keep it snappy)
    run_details_by_id: dict[int, dict[str, Any]] = {}
    for r in latest_runs[:200]:
        rid = int(r.get("id") or 0)
        if rid:
            d = get_run(runs_db, rid)
            if d:
                run_details_by_id[rid] = d

    # Keep issues table in sync with the latest evidence (global view only).
    # If the user is filtering by env/owned, we do not mutate the canonical issues DB.
    if env is None and owned is None:
        try:
            _sync_issues_from_latest_runs(assets_rows=assets_rows_all, latest_runs=latest_runs_all, run_details_by_id=run_details_by_id)
        except Exception:
            pass

    metrics = build_dashboard_metrics(
        assets=assets_rows,
        latest_runs=latest_runs,
        run_details_by_id=run_details_by_id,
        total_runs=total_runs,
        runs_24h=runs_24h,
        runs_7d=runs_7d,
    )

    # Trend snapshots (score as-of 7d/30d/90d)
    def snapshot(asof_ts: int) -> dict[str, Any] | None:
        runs_all = list_latest_runs_per_target_asof(runs_db, asof_ts, limit_targets=300)
        if not runs_all:
            return None

        runs = [r for r in runs_all if _run_host(str(r.get("target") or "")) in allowed_hosts] if allowed_hosts else runs_all
        details: dict[int, dict[str, Any]] = {}
        for r in runs[:200]:
            rid = int(r.get("id") or 0)
            if not rid:
                continue
            d = get_run(runs_db, rid)
            if d:
                details[rid] = d

        m2 = build_dashboard_metrics(
            assets=assets_rows,
            latest_runs=runs,
            run_details_by_id=details,
            total_runs=total_runs,
            runs_24h=runs_24h,
            runs_7d=runs_7d,
        )
        return {
            "ts": asof_ts,
            "score": m2.score,
            "score_categories": m2.score_categories,
            "open_ports_total": m2.open_ports_total,
            "findings_by_sev": m2.findings_by_sev,
            "coverage_30d_pct": m2.coverage_30d_pct,
        }

    snap_7d = snapshot(now - 7 * 24 * 3600)
    snap_30d = snapshot(now - 30 * 24 * 3600)
    snap_90d = snapshot(now - 90 * 24 * 3600)

    narrative: list[str] = []
    if snap_7d:
        delta = int(metrics.score) - int(snap_7d.get("score") or 0)
        if delta != 0:
            narrative.append(f"Score change vs 7d: {delta:+d}.")
        dp = int(metrics.open_ports_total) - int(snap_7d.get("open_ports_total") or 0)
        if dp != 0:
            narrative.append(f"Open ports (latest evidence) change vs 7d: {dp:+d}.")
        # Findings deltas
        fb_now = metrics.findings_by_sev or {}
        fb_old = snap_7d.get("findings_by_sev") or {}
        for k in ["critical", "high", "medium", "low"]:
            d0 = int(fb_now.get(k) or 0) - int(fb_old.get(k) or 0)
            if d0:
                narrative.append(f"{k.title()} findings change vs 7d: {d0:+d}.")

    return {
        "metrics": metrics.to_dict(),
        "trend": {"asof7d": snap_7d, "asof30d": snap_30d, "asof90d": snap_90d},
        "narrative": narrative,
    }


def _sync_issues_from_latest_runs(
    *,
    assets_rows: list[dict[str, Any]],
    latest_runs: list[dict[str, Any]],
    run_details_by_id: dict[int, dict[str, Any]],
) -> None:
    """Upsert issues for the current evidence window.

    This is intentionally best-effort and only covers normalized findings.
    """

    assets_by_value = {str(a.get("value") or "").strip().lower(): a for a in (assets_rows or [])}

    issues_db = default_issues_db_path()
    now = now_ts()

    for r in latest_runs or []:
        rid = int(r.get("id") or 0)
        target = str(r.get("target") or "")
        detail = run_details_by_id.get(rid) or {}
        findings = detail.get("findings") or []
        if not isinstance(findings, list):
            continue

        # Map to an asset hostname if possible.
        host = parse_target(target).host or target
        key = host.strip().lower()
        asset_meta = assets_by_value.get(key) or {}

        owner = str(asset_meta.get("owner") or "")
        env = str(asset_meta.get("environment") or "")

        for f in findings:
            if not isinstance(f, dict):
                continue
            category = str(f.get("category") or "")
            title = str(f.get("title") or "")
            sev = int(f.get("severity") or 0)
            remediation = str(f.get("remediation") or "")
            details = str(f.get("details") or "")

            if not title:
                continue

            fp = fingerprint_issue(key, category, title)

            # Determine first_seen if exists
            # (read existing row is expensive; we keep it simple: first_seen=now for now)
            # Future: add get_issue() and preserve first_seen.
            issue = Issue(
                fingerprint=fp,
                asset=key,
                category=category,
                title=title,
                severity=sev,
                status="open",
                owner=owner,
                environment=env,
                first_seen_ts=now,
                last_seen_ts=now,
                last_run_id=rid,
                remediation=remediation,
                details=details,
            )

            upsert_issue(issues_db, issue)


@app.get("/scans")
def scans() -> dict[str, Any]:
    reg = discover_scanners()
    return {"scans": [{"id": k, "description": v.description} for k, v in reg.items()]}


@app.post("/seed")
async def seed(req: SeedRequest) -> dict[str, Any]:
    info = parse_target(req.domain)
    domain = info.host or info.raw

    assets = await expand_domain(
        domain,
        use_crtsh=bool(req.use_ct),
        use_common_prefixes=bool(req.use_common),
        use_live_tls=bool(req.use_live_tls),
        resolve=bool(req.resolve),
        max_hosts=int(req.max_hosts),
        max_dns_lookups=int(req.max_dns_lookups),
        dns_concurrency=int(req.dns_concurrency),
    )

    return {
        "domain": domain,
        "assets": [a.to_dict() for a in assets],
    }


@app.get("/issues")
def issues(limit: int = 30, offset: int = 0, status: str | None = None, owner: str | None = None) -> dict[str, Any]:
    db_path = default_issues_db_path()
    lim = max(1, min(200, int(limit)))
    off = max(0, int(offset))

    # Fetch and filter in-process for now (keeps storage simple).
    items = [i.to_dict() for i in list_issues(db_path, limit=5000, offset=0, status=status)]
    if owner:
        o = owner.strip().lower()
        items = [i for i in items if str(i.get("owner") or "").strip().lower() == o]

    total = len(items)
    page = items[off : off + lim]

    return {"issues": page, "total": total, "limit": lim, "offset": off}


@app.post("/issues/update")
def issue_update(req: IssueUpdateRequest) -> dict[str, Any]:
    if not req.fingerprint:
        raise HTTPException(status_code=400, detail="Missing fingerprint")

    if req.status is None and req.owner is None:
        raise HTTPException(status_code=400, detail="Provide status and/or owner")

    update_issue_status(default_issues_db_path(), req.fingerprint, status=req.status, owner=req.owner)
    return {"ok": True}


@app.post("/assets/import")
def assets_import(req: AssetsImportRequest) -> dict[str, Any]:
    db_path = req.assets_db or default_assets_db_path()
    now = int(time.time())

    assets = [a.strip() for a in (req.assets or []) if a and a.strip()]
    assets = assets[:5000]

    stored = 0
    for v in assets:
        upsert_asset(
            db_path,
            Asset(
                kind="host",
                value=v,
                tags=list(req.tags or []),
                owner=req.owner,
                environment=req.environment,
                ts=now,
            ),
        )
        stored += 1

    return {"stored": stored}


@app.post("/scan")
async def scan(req: ScanRequest) -> dict[str, Any]:
    reg = discover_scanners()
    info = parse_target(req.target)

    if req.scans:
        scans_set = {s.strip() for s in req.scans.split(",") if s.strip()}
    elif req.smart:
        scans_set = set(plan_scans(info).scans)
    else:
        raise HTTPException(status_code=400, detail="Provide scans or set smart=true")

    unknown = [s for s in scans_set if s not in reg]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown scans: {unknown}")

    # run scans sequentially for now (simple + predictable)
    results: dict[str, Any] = {}
    for scan_id in sorted(scans_set):
        res = await reg[scan_id].scan(req.target, False)
        results.update(res)

    findings = [f.to_dict() for f in normalize_findings(results, asset=req.target)]

    run_id = None
    if req.store:
        db_path = req.db or default_db_path()
        run_id = store_run(db_path, req.target, sorted(list(scans_set)), results, findings)

    return {"runId": run_id, "target": req.target, "scans": sorted(list(scans_set)), "results": results, "findings": findings}


@app.get("/runs")
def runs(limit: int = 30, offset: int = 0) -> dict[str, Any]:
    db_path = default_db_path()
    lim = max(1, min(200, int(limit)))
    off = max(0, int(offset))
    return {
        "runs": list_runs(db_path, limit=lim, offset=off),
        "total": count_runs(db_path),
        "limit": lim,
        "offset": off,
    }


@app.get("/runs/{run_id}")
def run_detail(run_id: int) -> dict[str, Any]:
    db_path = default_db_path()
    run = get_run(db_path, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run": run}


@app.get("/runs/{run_id}/delta")
def run_delta(run_id: int) -> dict[str, Any]:
    """Return best-effort deltas vs the prior run for the same target.

    Used to power an evidence-first story: what changed, not just what we saw.
    """

    runs_db = default_db_path()
    run = get_run(runs_db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    target = str(run.get("target") or "")
    host = _run_host(target)

    # Find the previous run for the same host (best-effort).
    candidates = list_runs_matching_host(runs_db, host, limit=200)
    candidates = sorted(candidates, key=lambda r: int(r.get("ts") or 0), reverse=True)

    prev = None
    for r in candidates:
        rid = int(r.get("id") or 0)
        ts = int(r.get("ts") or 0)
        if rid and rid != int(run_id) and ts < int(run.get("ts") or 0):
            prev = get_run(runs_db, rid)
            break

    def _finding_key(f: dict[str, Any]) -> str:
        return f"{str(f.get('category') or '').strip().lower()}|{str(f.get('title') or '').strip().lower()}"

    cur_findings = [f for f in (run.get("findings") or []) if isinstance(f, dict)]
    prev_findings = [f for f in (prev.get("findings") or []) if isinstance(f, dict)] if prev else []

    cur_keys = {_finding_key(f) for f in cur_findings}
    prev_keys = {_finding_key(f) for f in prev_findings}

    new_keys = sorted(list(cur_keys - prev_keys))
    gone_keys = sorted(list(prev_keys - cur_keys))

    # Ports delta (derived from raw results).
    cur_ports = {str(p.get("port") or "").strip() for p in extract_open_ports_from_results(run.get("results") or {})}
    prev_ports = {str(p.get("port") or "").strip() for p in extract_open_ports_from_results(prev.get("results") or {})} if prev else set()

    new_ports = sorted([p for p in (cur_ports - prev_ports) if p])
    closed_ports = sorted([p for p in (prev_ports - cur_ports) if p])

    def _pick(keys: list[str], source: list[dict[str, Any]]) -> list[dict[str, Any]]:
        want = set(keys)
        out: list[dict[str, Any]] = []
        for f in source:
            if _finding_key(f) in want:
                out.append({
                    "category": f.get("category") or "",
                    "title": f.get("title") or "",
                    "severity": int(f.get("severity") or 0),
                    "remediation": f.get("remediation") or "",
                })
        out.sort(key=lambda x: int(x.get("severity") or 0), reverse=True)
        return out[:50]

    return {
        "runId": int(run_id),
        "target": target,
        "prevRunId": int(prev.get("id") or 0) if prev else None,
        "newFindings": _pick(new_keys, cur_findings),
        "resolvedFindings": _pick(gone_keys, prev_findings),
        "newPorts": new_ports,
        "closedPorts": closed_ports,
    }


@app.get("/assets")
def assets(
    limit: int = 30,
    offset: int = 0,
    env: str | None = None,
    owned: int | None = None,
    owner: str | None = None,
) -> dict[str, Any]:
    db_path = default_assets_db_path()
    lim = max(1, min(500, int(limit)))
    off = max(0, int(offset))

    rows_all = [a.to_dict() for a in list_assets(db_path, limit=5000, offset=0)]

    owned_bool = True if owned == 1 else False if owned == 0 else None
    rows = _asset_filter_rows(rows_all, env=env, owned=owned_bool)

    if owner:
        o = owner.strip().lower()
        rows = [r for r in rows if str(r.get("owner") or "").strip().lower() == o]

    total = len(rows)
    page = rows[off : off + lim]

    return {"assets": page, "total": total, "limit": lim, "offset": off}


@app.get("/exposure/ports")
def exposure_ports(limit: int = 10, env: str | None = None, owned: int | None = None) -> dict[str, Any]:
    """Top exposed ports across the latest run per target.

    Returns: [{port, assets}] where assets is the count of distinct hosts.
    """

    runs_db = default_db_path()

    assets_db = default_assets_db_path()
    assets_rows_all = [a.to_dict() for a in list_assets(assets_db, limit=5000, offset=0)]
    owned_bool = True if owned == 1 else False if owned == 0 else None
    assets_rows = _asset_filter_rows(assets_rows_all, env=env, owned=owned_bool)
    allowed_hosts = {str(a.get("value") or "").strip().lower().rstrip(".") for a in assets_rows if str(a.get("value") or "").strip()}

    latest_runs_all = list_latest_runs_per_target(runs_db, limit_targets=800)
    latest_runs = (
        [r for r in latest_runs_all if _run_host(str(r.get("target") or "")) in allowed_hosts]
        if allowed_hosts
        else latest_runs_all
    )

    # Load details for latest runs (cap to keep it snappy)
    details: list[dict[str, Any]] = []
    for r in latest_runs[:600]:
        rid = int(r.get("id") or 0)
        if not rid:
            continue
        d = get_run(runs_db, rid)
        if d:
            details.append(d)

    _assets_by_port, counts, risk_points = summarize_open_ports_by_asset(details, max_assets=600)

    lim = max(1, min(50, int(limit)))

    # Default sort: highest risk points, then asset count
    ports_sorted = sorted(
        counts.keys(),
        key=lambda p: (int(risk_points.get(p) or 0), int(counts.get(p) or 0)),
        reverse=True,
    )

    ports_sorted = ports_sorted[:lim]

    return {
        "ports": [
            {"port": p, "assets": int(counts.get(p) or 0), "riskPoints": int(risk_points.get(p) or 0)}
            for p in ports_sorted
        ],
    }


@app.get("/assets/exposed")
def assets_exposed(port: str, limit: int = 30, offset: int = 0, env: str | None = None, owned: int | None = None) -> dict[str, Any]:
    """Return inventory assets that appear exposed on a given port.

    This is derived from latest run evidence. Best-effort only.
    """

    p = (port or "").strip()
    if not p:
        raise HTTPException(status_code=400, detail="Missing port")

    assets_db = default_assets_db_path()
    runs_db = default_db_path()

    assets_rows_all = [a.to_dict() for a in list_assets(assets_db, limit=5000, offset=0)]
    owned_bool = True if owned == 1 else False if owned == 0 else None
    assets_rows = _asset_filter_rows(assets_rows_all, env=env, owned=owned_bool)
    allowed_hosts = {str(a.get("value") or "").strip().lower().rstrip(".") for a in assets_rows if str(a.get("value") or "").strip()}

    latest_runs_all = list_latest_runs_per_target(runs_db, limit_targets=1200)
    latest_runs = (
        [r for r in latest_runs_all if _run_host(str(r.get("target") or "")) in allowed_hosts]
        if allowed_hosts
        else latest_runs_all
    )

    details: list[dict[str, Any]] = []
    for r in latest_runs[:900]:
        rid = int(r.get("id") or 0)
        if not rid:
            continue
        d = get_run(runs_db, rid)
        if d:
            details.append(d)

    assets_by_port, _counts, _risk = summarize_open_ports_by_asset(details, max_assets=900)
    exposed_hosts = assets_by_port.get(p, set())

    # Filter inventory assets to just those hosts (and keep env/owned filters).
    filtered = [a for a in assets_rows if str(a.get("value") or "").strip().lower().rstrip(".") in exposed_hosts]

    lim = max(1, min(200, int(limit)))
    off = max(0, int(offset))
    page = filtered[off : off + lim]

    return {"assets": page, "total": len(filtered), "limit": lim, "offset": off, "port": p}


@app.get("/asset")
def asset(value: str) -> dict[str, Any]:
    """Return asset detail + latest evidence we have.

    - asset metadata from inventory (if present)
    - latest matching stored run (best-effort)
    - extracted exposure signals (e.g., open ports)
    """

    v = (value or "").strip()
    if not v:
        raise HTTPException(status_code=400, detail="Missing value")

    assets_db = default_assets_db_path()
    runs_db = default_db_path()

    # Find the asset row (best-effort: scan current page; inventory is small in early MVP)
    # If we don't find it, we still allow looking up run evidence.
    asset_row = None
    try:
        all_assets = list_assets(assets_db, limit=5000, offset=0)
        for a in all_assets:
            if a.value.strip().lower() == v.lower():
                asset_row = a.to_dict()
                break
    except Exception:
        asset_row = None

    # Find latest run for this asset.
    host = parse_target(v).host or v
    runs = list_runs_matching_host(runs_db, host, limit=1)
    latest = runs[0] if runs else None

    detail = None
    open_ports: list[dict[str, str]] = []
    if latest:
        detail = get_run(runs_db, int(latest["id"]))
        if detail and isinstance(detail.get("results"), dict):
            open_ports = extract_open_ports_from_results(detail.get("results") or {})

    return {
        "asset": asset_row,
        "latestRun": latest,
        "runDetail": detail,
        "openPorts": open_ports,
    }


@app.get("/runs/{run_id}/report")
def run_report(run_id: int, format: str = "md") -> dict[str, Any] | str:
    """Return an on-demand report for a stored run.

    Note: response is plain text/html (not JSON) for easy download.
    """

    from fastapi.responses import PlainTextResponse, HTMLResponse

    db_path = default_db_path()
    run = get_run(db_path, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    from utils.report_templates import RunForReport, run_to_html, run_to_json, run_to_markdown

    r = RunForReport(
        id=int(run["id"]),
        ts=int(run["ts"]),
        target=str(run["target"]),
        scans=list(run.get("scans") or []),
        results=dict(run.get("results") or {}),
        findings=list(run.get("findings") or []),
    )

    if format == "json":
        return PlainTextResponse(
            run_to_json(r),
            media_type="application/json",
            headers={"content-disposition": f"attachment; filename=masat-run-{run_id}.json"},
        )
    if format == "html":
        return HTMLResponse(
            run_to_html(r),
            headers={"content-disposition": f"attachment; filename=masat-run-{run_id}.html"},
        )

    return PlainTextResponse(
        run_to_markdown(r),
        media_type="text/markdown",
        headers={"content-disposition": f"attachment; filename=masat-run-{run_id}.md"},
    )


@app.get("/diff")
def diff(target: str, last: int = 2, format: str = "json"):
    """Diff last N stored runs for a target.

    format: json|md
    """

    from utils.diffing import DiffResult, diff_exposure, diff_findings
    from utils.diff_report import diff_to_json, diff_to_markdown
    from utils.history import list_runs_for_target

    db_path = default_db_path()
    runs = list_runs_for_target(db_path, target, limit=max(2, int(last)))
    if len(runs) < 2:
        raise HTTPException(status_code=400, detail="Not enough stored runs to diff")

    new_run = get_run(db_path, int(runs[0]["id"]))
    old_run = get_run(db_path, int(runs[1]["id"]))
    if not new_run or not old_run:
        raise HTTPException(status_code=500, detail="Unable to load runs")

    added, resolved = diff_findings(old_run.get("findings", []), new_run.get("findings", []))
    exposure = diff_exposure(old_run.get("results", {}) or {}, new_run.get("results", {}) or {})

    out = DiffResult(
        target=target,
        old_run_id=int(old_run["id"]),
        new_run_id=int(new_run["id"]),
        new_findings=added,
        resolved_findings=resolved,
        exposure=exposure,
    )

    from fastapi.responses import PlainTextResponse

    if format == "md":
        return PlainTextResponse(
            diff_to_markdown(out),
            media_type="text/markdown",
            headers={"content-disposition": f"attachment; filename=masat-diff-{out.old_run_id}-{out.new_run_id}.md"},
        )

    return PlainTextResponse(diff_to_json(out), media_type="application/json")
