"""Diff utilities for EASM.

Focused on answering: what changed between two runs?

We diff at two layers:
- Findings: normalized finding tuples
- Exposure-ish signals: attempt to detect open ports changes from raw results when available

This is intentionally basic and evidence-preserving.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable


def _parse_nmap_open_ports_table(details: str) -> set[str]:
    """Parse the human-readable nmap table into stable port identifiers.

    Returns a set of strings like: "22/tcp ssh" or "443/tcp https".
    """

    s = (details or "").strip("\n")
    if not s or "No open ports" in s:
        return set()

    lines = [ln.rstrip() for ln in s.splitlines() if ln.strip()]
    if len(lines) < 3:
        return set()

    # Expect header + separator then data rows.
    data = lines[2:]
    ports: set[str] = set()
    for ln in data:
        parts = ln.split()
        if not parts:
            continue
        port = parts[0]
        service = parts[1] if len(parts) > 1 else ""
        ports.add(f"{port} {service}".strip())

    return ports


def _extract_server_header(results: dict[str, Any]) -> str | None:
    try:
        tech = results.get("Web Server Technology")
        if not isinstance(tech, dict):
            return None
        det = tech.get("Detected Server")
        if not isinstance(det, dict):
            return None
        details = str(det.get("details", ""))
        # e.g. "Server header: nginx"
        if ":" in details:
            return details.split(":", 1)[1].strip() or None
        return details.strip() or None
    except Exception:
        return None


def extract_exposure(results: dict[str, Any]) -> dict[str, Any]:
    """Extract exposure-ish signals from raw scanner results."""

    nmap = (results or {}).get("Nmap Scan") or {}
    ports_entry = (nmap.get("\nOpen Ports") if isinstance(nmap, dict) else {}) or {}
    details = ports_entry.get("details", "") if isinstance(ports_entry, dict) else ""

    exposure: dict[str, Any] = {
        "open_ports": sorted(list(_parse_nmap_open_ports_table(str(details)))),
    }

    server = _extract_server_header(results or {})
    if server:
        exposure["server_header"] = server

    return exposure


def diff_exposure(old_results: dict[str, Any], new_results: dict[str, Any]) -> dict[str, Any]:
    old = extract_exposure(old_results or {})
    new = extract_exposure(new_results or {})

    old_ports = set(old.get("open_ports") or [])
    new_ports = set(new.get("open_ports") or [])

    out: dict[str, Any] = {
        "added_ports": sorted(list(new_ports - old_ports)),
        "removed_ports": sorted(list(old_ports - new_ports)),
    }

    if old.get("server_header") != new.get("server_header"):
        out["server_header"] = {
            "old": old.get("server_header"),
            "new": new.get("server_header"),
        }

    return out


@dataclass(frozen=True)
class DiffResult:
    target: str
    old_run_id: int
    new_run_id: int

    # Findings layer
    new_findings: list[dict[str, Any]]
    resolved_findings: list[dict[str, Any]]

    # Exposure layer (ports/fingerprints)
    exposure: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finding_key(f: dict[str, Any]) -> tuple[str, str, str]:
    # Use stable keys; tolerate schema changes.
    asset = str(f.get("asset", ""))
    category = str(f.get("category", ""))
    title = str(f.get("title", ""))
    return (asset, category, title)


def diff_findings(old: Iterable[dict[str, Any]], new: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    old_map = {_finding_key(f): f for f in (old or [])}
    new_map = {_finding_key(f): f for f in (new or [])}

    new_keys = set(new_map.keys())
    old_keys = set(old_map.keys())

    added = [new_map[k] for k in sorted(new_keys - old_keys)]
    resolved = [old_map[k] for k in sorted(old_keys - new_keys)]
    return added, resolved
