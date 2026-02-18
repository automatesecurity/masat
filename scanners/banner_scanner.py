#!/usr/bin/env python3
"""Lightweight banner grabbing for common services.

This scanner is intentionally conservative:
- TCP connect + read a small amount of data with short timeouts
- Optional protocol-aware nudge for SMTP (EHLO) and HTTP(S) (HEAD)

It is meant for quick service fingerprinting and exposure discovery.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from urllib.parse import urlparse

SCAN_ID = "banners"
DESCRIPTION = "Banner grabbing for common TCP services (ssh/smtp/ftp/http)."


@dataclass(frozen=True)
class TargetEndpoint:
    host: str
    port: int
    scheme: str | None = None


def parse_target(target: str) -> tuple[str, str | None, int | None]:
    """Return (host, scheme, port). Port may be None if not specified."""
    parsed = urlparse(target)
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname
        scheme = parsed.scheme
        port = parsed.port
        return host, scheme, port

    # host[:port]
    if ":" in target and target.count(":") == 1:
        host, p = target.split(":", 1)
        try:
            return host, None, int(p)
        except ValueError:
            return target, None, None

    return target, None, None


async def grab_tcp_banner(host: str, port: int, send: bytes | None = None) -> str:
    """Connect and read up to 1KB."""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3)
        try:
            if send:
                writer.write(send)
                await writer.drain()
            data = await asyncio.wait_for(reader.read(1024), timeout=3)
            return data.decode(errors="replace").strip()
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
    except Exception as e:
        return f"<error: {e}>"


async def grab_http_banner(url: str) -> str:
    """Send a HEAD request and capture the status line + a few headers."""
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return "<error: invalid URL>"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query

    # Basic HTTP/1.1 HEAD
    req = (
        f"HEAD {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"User-Agent: masat/0.x\r\n"
        f"Connection: close\r\n\r\n"
    ).encode("utf-8")

    # NOTE: This does not implement TLS. For https targets, we still attempt
    # a plaintext HEAD to the port (will typically fail). Keeping this minimal
    # avoids adding heavy deps. TLS details should come from tls_scanner.
    banner = await grab_tcp_banner(host, port, send=req)

    # Return only the first few lines for signal.
    lines = banner.splitlines()
    return "\n".join(lines[:10]).strip()


async def scan(target: str, verbose: bool = False) -> dict:
    host, scheme, port = parse_target(target)

    endpoints: list[TargetEndpoint] = []
    if port:
        endpoints.append(TargetEndpoint(host=host, port=port, scheme=scheme))
    else:
        # Common ports
        for p in (21, 22, 25, 80, 110, 143, 443):
            endpoints.append(TargetEndpoint(host=host, port=p, scheme=None))

    findings = {}

    async def one(ep: TargetEndpoint) -> tuple[str, str]:
        if ep.port in (25,):
            # SMTP servers usually speak first; EHLO gets more.
            banner = await grab_tcp_banner(ep.host, ep.port, send=b"EHLO masat.local\r\n")
        elif ep.port in (80,):
            banner = await grab_http_banner(f"http://{ep.host}/")
        else:
            banner = await grab_tcp_banner(ep.host, ep.port)
        return f"{ep.host}:{ep.port}", banner

    results = await asyncio.gather(*(one(ep) for ep in endpoints))

    banner_map = {k: v for k, v in results if v and v != "<error: >"}

    # Trim very noisy banners
    trimmed = {}
    for k, v in banner_map.items():
        vv = v.strip()
        if len(vv) > 800:
            vv = vv[:800] + "\n<trimmed>"
        trimmed[k] = vv

    if verbose:
        print(f"[BANNER SCANNER] Grabbed {len(trimmed)} banners")

    findings["Banner Grabbing"] = {
        "Service banners": {
            "severity": 0,
            "remediation": "Review exposed services and ensure they are expected, hardened, and monitored.",
            "details": "\n\n".join([f"{k}\n{v}" for k, v in trimmed.items()]) if trimmed else "None",
        }
    }

    return findings
