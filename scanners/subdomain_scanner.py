#!/usr/bin/env python3
"""Passive subdomain enumeration.

Uses Certificate Transparency (crt.sh) as a low-friction source for discovered
subdomains. This is intended as recon/OSINT and is informational.

Note: crt.sh is a public service and may rate-limit. Keep queries small and
handle failures gracefully.
"""

from __future__ import annotations

import aiohttp
from urllib.parse import urlparse

SCAN_ID = "subdomains"
DESCRIPTION = "Passive subdomain enumeration via Certificate Transparency (crt.sh)."


def extract_domain(target: str) -> str:
    """Extract a domain from a URL/hostname/IP target string."""
    parsed = urlparse(target)
    host = parsed.hostname if parsed.hostname else target
    # crude normalization: strip port if user passed host:port without scheme
    if host and ":" in host and host.count(":") == 1:
        host = host.split(":", 1)[0]
    return host


def normalize_crtsh_names(name_value: str) -> list[str]:
    """Split a crt.sh name_value into normalized DNS names."""
    names: list[str] = []
    for raw in (name_value or "").split("\n"):
        n = raw.strip().lower()
        if not n:
            continue
        # crt.sh often returns wildcards.
        if n.startswith("*."):
            n = n[2:]
        names.append(n)
    return names


async def scan(target: str, verbose: bool = False) -> dict:
    domain = extract_domain(target)
    if not domain:
        return {"Subdomain Enumeration": {"No domain provided": {"severity": 0, "remediation": "None"}}}

    url = f"https://crt.sh/?q=%25.{domain}&output=json"

    subdomains: set[str] = set()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                if resp.status != 200:
                    return {
                        "Subdomain Enumeration": {
                            "crt.sh query failed": {
                                "severity": 0,
                                "remediation": "None",
                                "details": f"HTTP {resp.status} from crt.sh",
                            }
                        }
                    }
                data = await resp.json(content_type=None)

        for row in data:
            for n in normalize_crtsh_names(row.get("name_value", "")):
                # keep results within the queried domain.
                if n == domain or n.endswith("." + domain):
                    subdomains.add(n)

    except Exception as e:
        return {
            "Subdomain Enumeration": {
                "crt.sh query exception": {
                    "severity": 0,
                    "remediation": "None",
                    "details": str(e),
                }
            }
        }

    results = sorted(subdomains)
    if verbose:
        print(f"[SUBDOMAIN SCANNER] Found {len(results)} subdomains for {domain}")

    return {
        "Subdomain Enumeration": {
            "Subdomains discovered": {
                "severity": 0,
                "remediation": "Review discovered subdomains for unexpected exposures and ensure they are covered by monitoring.",
                "details": ", ".join(results) if results else "None",
            }
        }
    }
