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
from utils.history import default_db_path, store_run, list_runs, count_runs, count_runs_since, list_latest_runs_per_target, get_run
from utils.assets import default_assets_db_path, list_assets, count_assets, upsert_asset, Asset
from utils.dashboard import build_dashboard_metrics


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard() -> dict[str, Any]:
    """Return high-level dashboard metrics.

    This endpoint intentionally returns a single aggregated object so the UI can
    render an enterprise-style dashboard without multiple round trips.
    """

    assets_db = default_assets_db_path()
    runs_db = default_db_path()

    assets_total = count_assets(assets_db)
    # For now, we load at most 5000 assets for metrics breakdown.
    assets_rows = [a.to_dict() for a in list_assets(assets_db, limit=min(5000, max(30, assets_total)), offset=0)]

    total_runs = count_runs(runs_db)
    now = int(time.time())
    runs_24h = count_runs_since(runs_db, now - 24 * 3600)
    runs_7d = count_runs_since(runs_db, now - 7 * 24 * 3600)

    latest_runs = list_latest_runs_per_target(runs_db, limit_targets=300)

    # Load details for latest runs (cap to keep it snappy)
    run_details_by_id: dict[int, dict[str, Any]] = {}
    for r in latest_runs[:200]:
        rid = int(r.get("id") or 0)
        if rid:
            d = get_run(runs_db, rid)
            if d:
                run_details_by_id[rid] = d

    metrics = build_dashboard_metrics(
        assets=assets_rows,
        latest_runs=latest_runs,
        run_details_by_id=run_details_by_id,
        total_runs=total_runs,
        runs_24h=runs_24h,
        runs_7d=runs_7d,
    )

    return {"metrics": metrics.to_dict()}


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


@app.get("/assets")
def assets(limit: int = 30, offset: int = 0) -> dict[str, Any]:
    db_path = default_assets_db_path()
    lim = max(1, min(500, int(limit)))
    off = max(0, int(offset))
    rows = [a.to_dict() for a in list_assets(db_path, limit=lim, offset=off)]
    return {"assets": rows, "total": count_assets(db_path), "limit": lim, "offset": off}


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
