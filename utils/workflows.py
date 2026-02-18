"""Smart scan planning for MASAT.

This is the orchestration layer to help MASAT decide which scans to run for a
given target.

Design:
- Keep it lightweight by default.
- Prefer deterministic, explainable plans.
- Make potentially-expensive expansions (subdomains) opt-in.
"""

from __future__ import annotations

from dataclasses import dataclass

from scanners.registry import discover_scanners
from utils.targets import TargetInfo


@dataclass(frozen=True)
class ScanPlan:
    target: str
    scans: list[str]
    rationale: list[str]


def plan_scans(info: TargetInfo, include_nuclei: bool = True) -> ScanPlan:
    registry = discover_scanners()
    scans: list[str] = []
    rationale: list[str] = []

    def add(scan_id: str, why: str):
        if scan_id in registry and scan_id not in scans:
            scans.append(scan_id)
            rationale.append(f"{scan_id}: {why}")

    if info.kind == "url":
        add("web", "URL target → run web header/method/library checks")
        if info.scheme == "https":
            add("tls", "HTTPS URL → run TLS scan")
        add("banners", "Grab lightweight banners for common ports")
        if include_nuclei:
            add("nuclei", "Run nuclei CVE/misconfig templates (if installed)")

    elif info.kind in ("host", "ip"):
        add("banners", "Host/IP target → quick banner fingerprinting")
        add("nmap", "Host/IP target → ports/services inventory")
        add("tls", "If 443 is open, TLS scan will add signal")
        if include_nuclei:
            add("nuclei", "Run nuclei against host (best-effort)")

    elif info.kind == "cidr":
        add("nmap", "CIDR target → port/service discovery across range (can be expensive)")

    else:
        add("web", "Default to web scan")

    return ScanPlan(target=info.raw, scans=scans, rationale=rationale)
