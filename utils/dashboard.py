"""Dashboard metrics aggregation.

We keep this intentionally lightweight and dependency-free. The goal is to
summarize what MASAT *currently* knows (assets + stored runs) into a set of
enterprise-style metrics.

The scoring is best-effort and should be treated as an internal heuristic.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Any

from utils.targets import parse_target


_SEV_BUCKETS = [
    (9, "critical"),
    (7, "high"),
    (4, "medium"),
    (1, "low"),
    (0, "info"),
]


def _sev_bucket(sev: int) -> str:
    s = int(sev)
    for threshold, name in _SEV_BUCKETS:
        if s >= threshold:
            return name
    return "info"


def _extract_host(target: str) -> str:
    info = parse_target(target)
    return (info.host or info.raw or "").strip().lower().rstrip(".")


def _count_open_ports(results: dict[str, Any]) -> int:
    """Best-effort parse of open ports from Nmap scanner results."""

    try:
        nmap = results.get("Nmap Scan") or {}
        open_ports = nmap.get("\nOpen Ports") or nmap.get("Open Ports") or {}
        details = open_ports.get("details")
        if not isinstance(details, str):
            return 0

        # Look for patterns like: 80/tcp  open  http  ...
        ports = set()
        for line in details.splitlines():
            m = re.match(r"^(\d{1,5})/tcp\b", line.strip())
            if m:
                ports.add(int(m.group(1)))
        return len(ports)
    except Exception:
        return 0


def _score_from_buckets(b: dict[str, int]) -> int:
    """Convert severity bucket counts into a 0-100 score."""

    critical = int(b.get("critical") or 0)
    high = int(b.get("high") or 0)
    med = int(b.get("medium") or 0)
    low = int(b.get("low") or 0)

    penalty = critical * 18 + high * 8 + med * 3 + low * 1
    return max(0, min(100, 100 - penalty))


def _score_exposed_services(open_ports_total: int, assets_scanned_30d: int) -> int:
    """0-100 score for exposed services.

    Uses open port count as a coarse proxy. We normalize by assets_scanned_30d
    to avoid penalizing large inventories too much.
    """

    denom = max(1, int(assets_scanned_30d))
    ports_per_asset = float(open_ports_total) / float(denom)

    # Heuristic thresholds.
    if ports_per_asset <= 0.5:
        return 95
    if ports_per_asset <= 1.0:
        return 88
    if ports_per_asset <= 2.0:
        return 78
    if ports_per_asset <= 4.0:
        return 62
    if ports_per_asset <= 7.0:
        return 45
    return 30


def _score_coverage(coverage_pct: int) -> int:
    c = max(0, min(100, int(coverage_pct)))
    if c >= 95:
        return 95
    if c >= 80:
        return 85
    if c >= 60:
        return 72
    if c >= 40:
        return 58
    if c >= 20:
        return 45
    return 30


def _score_activity(runs_7d: int) -> int:
    r = int(runs_7d)
    if r >= 50:
        return 92
    if r >= 20:
        return 85
    if r >= 10:
        return 78
    if r >= 4:
        return 65
    if r >= 1:
        return 52
    return 35


def _weighted_score(parts: dict[str, tuple[int, int]]) -> int:
    """parts: name -> (score, weight)."""

    total_w = sum(w for _s, w in parts.values())
    if total_w <= 0:
        return 0
    acc = 0.0
    for s, w in parts.values():
        acc += float(max(0, min(100, int(s)))) * float(w)
    return int(round(acc / float(total_w)))


@dataclass(frozen=True)
class DashboardMetrics:
    ts: int

    # inventory
    total_assets: int
    assets_by_env: dict[str, int]

    # run activity
    total_runs: int
    runs_24h: int
    runs_7d: int
    latest_run_ts: int | None

    # coverage
    targets_seen: int
    assets_scanned_30d: int
    coverage_30d_pct: int

    # risk/exposure
    findings_by_sev: dict[str, int]
    open_ports_total: int

    # scoring
    score: int
    score_categories: dict[str, int]
    score_weights: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dashboard_metrics(
    *,
    assets: list[dict[str, Any]],
    latest_runs: list[dict[str, Any]],
    run_details_by_id: dict[int, dict[str, Any]],
    total_runs: int,
    runs_24h: int,
    runs_7d: int,
) -> DashboardMetrics:
    now = int(time.time())

    # Inventory
    assets_by_env: dict[str, int] = {}
    for a in assets:
        env = str(a.get("environment") or "").strip() or "unspecified"
        assets_by_env[env] = assets_by_env.get(env, 0) + 1

    # Coverage: compare asset hostnames with latest run targets
    asset_hosts = {
        str(a.get("value") or "").strip().lower().rstrip(".")
        for a in assets
        if str(a.get("kind") or "") in {"host", "url"} or True
    }

    latest_run_ts = None
    targets_seen = 0

    findings_by_sev: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    open_ports_total = 0

    scanned_30d: set[str] = set()
    cutoff_30d = now - 30 * 24 * 3600

    for r in latest_runs:
        targets_seen += 1
        rts = int(r.get("ts") or 0)
        if rts and (latest_run_ts is None or rts > latest_run_ts):
            latest_run_ts = rts

        host = _extract_host(str(r.get("target") or ""))
        if rts >= cutoff_30d and host:
            scanned_30d.add(host)

        rid = int(r.get("id") or 0)
        detail = run_details_by_id.get(rid) or {}
        findings = detail.get("findings") or []
        if isinstance(findings, list):
            for f in findings:
                if not isinstance(f, dict):
                    continue
                sev = int(f.get("severity") or 0)
                findings_by_sev[_sev_bucket(sev)] = findings_by_sev.get(_sev_bucket(sev), 0) + 1

        results = detail.get("results") or {}
        if isinstance(results, dict):
            open_ports_total += _count_open_ports(results)

    # only count assets we can match by hostname
    assets_scanned_30d = 0
    for h in scanned_30d:
        if h in asset_hosts:
            assets_scanned_30d += 1

    total_assets = len(assets)
    coverage_30d_pct = int(round((assets_scanned_30d / total_assets) * 100)) if total_assets else 0

    # Category scores (0-100)
    score_vuln = _score_from_buckets(findings_by_sev)
    score_exposure = _score_exposed_services(open_ports_total, assets_scanned_30d)
    score_cov = _score_coverage(coverage_30d_pct)
    score_act = _score_activity(runs_7d)

    # Weights: bias toward vuln + exposure, then coverage.
    weights = {
        "vulnerability": 45,
        "exposure": 30,
        "coverage": 15,
        "activity": 10,
    }

    score = _weighted_score(
        {
            "vulnerability": (score_vuln, weights["vulnerability"]),
            "exposure": (score_exposure, weights["exposure"]),
            "coverage": (score_cov, weights["coverage"]),
            "activity": (score_act, weights["activity"]),
        }
    )

    return DashboardMetrics(
        ts=now,
        total_assets=total_assets,
        assets_by_env=dict(sorted(assets_by_env.items(), key=lambda x: (-x[1], x[0]))),
        total_runs=int(total_runs),
        runs_24h=int(runs_24h),
        runs_7d=int(runs_7d),
        latest_run_ts=latest_run_ts,
        targets_seen=targets_seen,
        assets_scanned_30d=assets_scanned_30d,
        coverage_30d_pct=coverage_30d_pct,
        findings_by_sev=findings_by_sev,
        open_ports_total=int(open_ports_total),
        score=int(score),
        score_categories={
            "vulnerability": int(score_vuln),
            "exposure": int(score_exposure),
            "coverage": int(score_cov),
            "activity": int(score_act),
        },
        score_weights={k: int(v) for k, v in weights.items()},
    )
