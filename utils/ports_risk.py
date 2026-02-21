"""Port risk weights.

Heuristic weights used for exposure scoring/prioritization.

These are opinionated defaults; tune over time.
"""

from __future__ import annotations

import re


def port_risk_weight(port: str) -> int:
    """Return a 1-5 risk weight for a port string like '22/tcp'."""

    p = (port or "").strip().lower()
    m = re.match(r"^(\d{1,5})/tcp$", p)
    if not m:
        return 1

    n = int(m.group(1))

    # High-risk admin/remote mgmt and common ransomware propagation ports.
    if n in {3389, 445, 135, 139}:
        return 5
    if n in {22, 21, 23, 5900, 5985, 5986, 3306, 5432, 6379, 9200, 27017}:
        return 4
    if n in {389, 636, 8080, 8443, 8000, 8008, 8081, 8888, 15672}:
        return 3

    # Web is common but not automatically "bad".
    if n in {80, 443}:
        return 2

    return 1
