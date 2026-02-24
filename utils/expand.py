"""EASM-focused target expansion utilities.

Goal: start with a root domain and expand into concrete assets (subdomains),
optionally resolving to IPs, with strict safety limits.

This is intentionally conservative: it is *not* brute-force by default.
"""

from __future__ import annotations

import asyncio
import socket
import ssl
from dataclasses import dataclass, asdict
from typing import Iterable

import aiohttp


@dataclass(frozen=True)
class ExpandedAsset:
    hostname: str
    ips: list[str]
    source: str  # e.g., "crtsh", "input"

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_hostname(name: str) -> str | None:
    n = (name or "").strip().lower().rstrip(".")
    if not n:
        return None
    if " " in n or "/" in n:
        return None
    if n.startswith("*."):
        n = n[2:]
    return n or None


async def expand_via_crtsh(domain: str, *, timeout_s: int = 20, max_names: int = 2000) -> list[str]:
    """Return subdomains for `domain` from crt.sh.

    Note: crt.sh can be rate-limited; callers should handle empty results.
    """

    d = _normalize_hostname(domain)
    if not d:
        return []

    url = f"https://crt.sh/?q=%25.{d}&output=json"

    names: set[str] = set()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout_s) as resp:
            if resp.status != 200:
                return []
            data = await resp.json(content_type=None)

    for row in data:
        nv = row.get("name_value", "")
        for raw in (nv or "").split("\n"):
            n = _normalize_hostname(raw)
            if not n:
                continue
            if n == d or n.endswith("." + d):
                names.add(n)
            if len(names) >= max_names:
                break
        if len(names) >= max_names:
            break

    return sorted(names)


async def _resolve_one(hostname: str, sem: asyncio.Semaphore) -> list[str]:
    async with sem:
        try:
            # getaddrinfo returns tuples; we only keep the IP address.
            infos = await asyncio.get_running_loop().getaddrinfo(hostname, None)
        except Exception:
            return []

    ips: set[str] = set()
    for family, _type, _proto, _canon, sockaddr in infos:
        try:
            ip = sockaddr[0]
        except Exception:
            continue
        if ip:
            ips.add(str(ip))

    return sorted(ips)


async def resolve_hostnames(
    hostnames: Iterable[str],
    *,
    concurrency: int = 50,
    max_lookups: int = 2000,
) -> dict[str, list[str]]:
    """Resolve hostnames to IPs.

    Safety limits:
    - max_lookups: hard ceiling on DNS lookups attempted
    - concurrency: max simultaneous resolutions
    """

    sem = asyncio.Semaphore(max(1, int(concurrency)))

    resolved: dict[str, list[str]] = {}

    hn = [h for h in (_normalize_hostname(x) for x in hostnames) if h]
    hn = hn[: max(0, int(max_lookups))]

    async def run_one(h: str) -> None:
        resolved[h] = await _resolve_one(h, sem)

    await asyncio.gather(*(run_one(h) for h in hn))
    return resolved


def _tls_san_names(hostname: str, *, timeout_s: float = 3.0) -> list[str]:
    """Best-effort TLS certificate SAN extraction (stdlib only).

    Returns DNS names from subjectAltName if we can complete a handshake.
    """

    h = _normalize_hostname(hostname)
    if not h:
        return []

    ctx = ssl.create_default_context()

    # Disallow legacy TLS versions.
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    except Exception:
        # Older Pythons may not support TLSVersion; best-effort.
        pass

    # We are mining cert names; verification isn't the goal.
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((h, 443), timeout=timeout_s) as sock:
            with ctx.wrap_socket(sock, server_hostname=h) as ssock:
                cert = ssock.getpeercert() or {}
    except Exception:
        return []

    out: list[str] = []
    for entry in cert.get("subjectAltName", []) or []:
        try:
            k, v = entry
        except Exception:
            continue
        if str(k).lower() != "dns":
            continue
        n = _normalize_hostname(str(v))
        if n:
            out.append(n)

    return sorted(set(out))


async def expand_via_live_tls(
    hostnames: Iterable[str],
    *,
    concurrency: int = 20,
    max_hosts: int = 150,
) -> list[str]:
    sem = asyncio.Semaphore(max(1, int(concurrency)))
    hn = [h for h in (_normalize_hostname(x) for x in hostnames) if h][: max(0, int(max_hosts))]

    found: set[str] = set()

    async def run_one(h: str) -> None:
        async with sem:
            names = await asyncio.to_thread(_tls_san_names, h)
        for n in names:
            found.add(n)

    await asyncio.gather(*(run_one(h) for h in hn))
    return sorted(found)


async def expand_domain(
    domain: str,
    *,
    include_input: bool = True,
    use_crtsh: bool = True,
    use_common_prefixes: bool = False,
    use_live_tls: bool = False,
    common_prefixes: list[str] | None = None,
    resolve: bool = True,
    max_hosts: int = 500,
    max_dns_lookups: int = 2000,
    dns_concurrency: int = 50,
) -> list[ExpandedAsset]:
    """Expand a root domain into concrete EASM assets.

    Sources:
    - input (the root domain)
    - crt.sh (certificate transparency)
    - common prefixes (small curated list; optional)
    """

    d = _normalize_hostname(domain)
    if not d:
        return []

    names: list[tuple[str, str]] = []
    if include_input:
        names.append((d, "input"))

    if use_crtsh:
        try:
            crt_names = await expand_via_crtsh(d, max_names=max_dns_lookups)
        except Exception:
            crt_names = []
        names.extend((n, "crtsh") for n in crt_names)

    if use_common_prefixes:
        prefixes = common_prefixes or [
            "www",
            "api",
            "app",
            "admin",
            "portal",
            "login",
            "auth",
            "console",
            "dashboard",
            "status",
            "staging",
            "dev",
        ]
        for p in prefixes:
            p2 = (p or "").strip().lower().strip(".")
            if not p2:
                continue
            names.append((f"{p2}.{d}", "common"))

    if use_live_tls:
        # Mine SANs from live TLS endpoints we already discovered.
        # Keep this small and fast; best-effort only.
        seed_hosts = [n for n, _ in names][:150]
        try:
            tls_names = await expand_via_live_tls(seed_hosts, concurrency=min(20, int(dns_concurrency)))
        except Exception:
            tls_names = []

        for n in tls_names:
            if n == d or n.endswith("." + d):
                names.append((n, "tls"))

    # Dedupe with stable ordering.
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for n, src in names:
        if n in seen:
            continue
        seen.add(n)
        ordered.append((n, src))
        if len(ordered) >= max(0, int(max_hosts)):
            break

    if resolve:
        res = await resolve_hostnames((n for n, _ in ordered), concurrency=dns_concurrency, max_lookups=max_dns_lookups)
    else:
        res = {}

    assets: list[ExpandedAsset] = []
    for n, src in ordered:
        assets.append(ExpandedAsset(hostname=n, ips=res.get(n, []), source=src))

    return assets
