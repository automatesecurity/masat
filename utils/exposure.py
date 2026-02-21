"""Utilities to extract exposure signals from scan results.

These helpers are intentionally best-effort and should not be treated as strict
parsers of every scanner's output. They exist primarily to power UI summaries.
"""

from __future__ import annotations

import re
from typing import Any


def extract_open_ports_from_results(results: dict[str, Any]) -> list[dict[str, str]]:
    """Return a structured list of open ports from Nmap scanner output.

    Output items: {"port": "80/tcp", "service": "http", "version": "..."}
    """

    try:
        nmap = results.get("Nmap Scan") or {}
        open_ports = nmap.get("\nOpen Ports") or nmap.get("Open Ports") or {}
        details = open_ports.get("details")
        if not isinstance(details, str) or not details.strip():
            return []

        lines = details.splitlines()
        out: list[dict[str, str]] = []

        # If it's the formatted table from our scanner, the first two lines are header + separator.
        for line in lines:
            s = line.strip()
            if not s or s.lower().startswith("port") or set(s) == {"-"}:
                continue

            # Try to parse formatted table columns: "80/tcp  http  nginx ..."
            parts = re.split(r"\s{2,}", s)
            if len(parts) >= 2 and re.match(r"^\d{1,5}/tcp$", parts[0]):
                port = parts[0]
                service = parts[1] if len(parts) >= 2 else ""
                version = parts[2] if len(parts) >= 3 else ""
                out.append({"port": port, "service": service, "version": version})
                continue

            # Fallback parse: any line starting with 80/tcp
            m = re.match(r"^(\d{1,5}/tcp)\s+(\S+)(?:\s+(.*))?$", s)
            if m:
                out.append({"port": m.group(1), "service": m.group(2), "version": (m.group(3) or "").strip()})

        # Dedupe by port
        seen = set()
        deduped = []
        for r in out:
            p = r.get("port")
            if not p or p in seen:
                continue
            seen.add(p)
            deduped.append(r)

        return deduped
    except Exception:
        return []
