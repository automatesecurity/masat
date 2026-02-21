"""Aggregate port exposure across latest runs.

This powers a "top exposed ports" widget.

Best-effort only: depends on nmap output being present in stored run results.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from utils.exposure import extract_open_ports_from_results
from utils.ports_risk import port_risk_weight
from utils.targets import parse_target


def summarize_open_ports_by_asset(
    latest_run_details: list[dict[str, Any]],
    *,
    max_assets: int = 500,
) -> tuple[dict[str, set[str]], Counter[str], Counter[str]]:
    """Return (assets_by_port, counts_by_port, risk_points_by_port).

    - assets_by_port maps port ("22/tcp") -> set(hosts)
    - counts_by_port counts distinct hosts exposed on that port
    - risk_points_by_port is counts_by_port * weight(port)
    """

    assets_by_port: dict[str, set[str]] = defaultdict(set)
    counts: Counter[str] = Counter()

    for run in (latest_run_details or [])[: max(0, int(max_assets))]:
        target = str(run.get("target") or "")
        host = (parse_target(target).host or target).strip().lower().rstrip(".")
        if not host:
            continue

        results = run.get("results")
        if not isinstance(results, dict):
            continue

        ports = extract_open_ports_from_results(results)
        for p in ports:
            port = str(p.get("port") or "").strip()
            if not port:
                continue
            assets_by_port[port].add(host)

    risk_points: Counter[str] = Counter()
    for port, hosts in assets_by_port.items():
        counts[port] = len(hosts)
        risk_points[port] = len(hosts) * port_risk_weight(port)

    return dict(assets_by_port), counts, risk_points
