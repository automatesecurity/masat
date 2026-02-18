"""Target parsing and classification."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class TargetInfo:
    raw: str
    kind: str  # url|host|ip|cidr
    host: str | None
    scheme: str | None
    port: int | None


def parse_target(target: str) -> TargetInfo:
    t = (target or "").strip()
    parsed = urlparse(t)

    if parsed.scheme and parsed.hostname:
        host = parsed.hostname
        return TargetInfo(raw=t, kind="url", host=host, scheme=parsed.scheme, port=parsed.port)

    # CIDR?
    try:
        ipaddress.ip_network(t, strict=False)
        if "/" in t:
            return TargetInfo(raw=t, kind="cidr", host=None, scheme=None, port=None)
    except Exception:
        pass

    # IP?
    try:
        ipaddress.ip_address(t)
        return TargetInfo(raw=t, kind="ip", host=t, scheme=None, port=None)
    except Exception:
        pass

    # host[:port]
    host = t
    port = None
    if ":" in t and t.count(":") == 1:
        h, p = t.split(":", 1)
        if h and p.isdigit():
            host = h
            port = int(p)

    return TargetInfo(raw=t, kind="host", host=host, scheme=None, port=port)
