"""Local asset inventory + scoping helpers (EASM).

Design goals:
- Safe-by-default: explicit allowlist roots + optional denylist
- Minimal dependencies (stdlib)
- SQLite-backed to support UI later

This is a first pass meant to unlock EASM workflows.
"""

from __future__ import annotations

import csv
import fnmatch
import ipaddress
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from utils.targets import parse_target


@dataclass(frozen=True)
class Asset:
    kind: str  # host|ip|url|cidr
    value: str
    tags: list[str]
    owner: str
    environment: str
    ts: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_assets_db_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".masat")
    return os.path.join(base, "assets.db")


def _connect(db_path: str) -> sqlite3.Connection:
    # Treat db_path as untrusted. Only auto-create the default MASAT directory.
    default_dir = os.path.realpath(os.path.dirname(default_assets_db_path()))
    resolved = os.path.realpath(db_path)

    if os.path.commonpath([resolved, default_dir]) == default_dir:
        os.makedirs(default_dir, exist_ok=True)
    else:
        parent = os.path.dirname(resolved)
        if not os.path.isdir(parent):
            raise ValueError("Custom assets DB path directory must already exist")

    conn = sqlite3.connect(resolved)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts INTEGER NOT NULL,
          kind TEXT NOT NULL,
          value TEXT NOT NULL,
          tags TEXT NOT NULL,
          owner TEXT NOT NULL,
          environment TEXT NOT NULL,
          UNIQUE(kind, value)
        )
        """
    )
    conn.commit()
    return conn


def upsert_asset(db_path: str, asset: Asset) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO assets (ts, kind, value, tags, owner, environment) VALUES (?, ?, ?, ?, ?, ?)",
            (
                int(asset.ts),
                asset.kind,
                asset.value,
                ",".join(asset.tags),
                asset.owner,
                asset.environment,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def count_assets(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM assets")
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def list_assets(db_path: str, limit: int = 200, offset: int = 0) -> list[Asset]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, kind, value, tags, owner, environment FROM assets ORDER BY value ASC LIMIT ? OFFSET ?",
            (int(limit), int(offset)),
        )
        rows = cur.fetchall()
        out: list[Asset] = []
        for ts, kind, value, tags, owner, environment in rows:
            out.append(
                Asset(
                    ts=int(ts),
                    kind=str(kind),
                    value=str(value),
                    tags=[t for t in str(tags or "").split(",") if t],
                    owner=str(owner or ""),
                    environment=str(environment or ""),
                )
            )
        return out
    finally:
        conn.close()


def import_assets_csv(
    db_path: str,
    csv_path: str,
    *,
    default_owner: str = "",
    default_environment: str = "",
) -> int:
    """Import assets from CSV.

    CSV columns (case-insensitive):
    - asset (or value)
    - kind (optional; inferred if missing)
    - tags (comma-separated; optional)
    - owner (optional)
    - environment (optional)
    """

    n = 0
    now = int(time.time())

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return 0

        # normalize headers
        def get(row: dict[str, str], *names: str) -> str:
            for name in names:
                for k in row.keys():
                    if k and k.strip().lower() == name:
                        return (row.get(k) or "").strip()
            return ""

        for row in reader:
            value = get(row, "asset") or get(row, "value")
            if not value:
                continue

            kind = get(row, "kind")
            if not kind:
                info = parse_target(value)
                kind = info.kind

            tags_raw = get(row, "tags")
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            owner = get(row, "owner") or default_owner
            env = get(row, "environment") or default_environment

            upsert_asset(
                db_path,
                Asset(kind=str(kind), value=value.strip(), tags=tags, owner=owner, environment=env, ts=now),
            )
            n += 1

    return n


@dataclass(frozen=True)
class ScopeConfig:
    allow_domains: list[str]
    allow_cidrs: list[str]
    deny_patterns: list[str]


def _host_in_allowed_domains(host: str, allow_domains: Iterable[str]) -> bool:
    h = (host or "").strip().lower().rstrip(".")
    if not h:
        return False

    for d0 in allow_domains:
        d = (d0 or "").strip().lower().rstrip(".")
        if not d:
            continue
        if h == d or h.endswith("." + d):
            return True
    return False


def _ip_in_allowed_cidrs(ip: str, allow_cidrs: Iterable[str]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except Exception:
        return False

    for c in allow_cidrs:
        try:
            net = ipaddress.ip_network(str(c), strict=False)
        except Exception:
            continue
        if addr in net:
            return True
    return False


def _matches_any_pattern(value: str, patterns: Iterable[str]) -> bool:
    v = (value or "").strip().lower()
    for p0 in patterns:
        p = (p0 or "").strip().lower()
        if not p:
            continue
        if fnmatch.fnmatch(v, p):
            return True
    return False


def in_scope(target: str, scope: ScopeConfig) -> tuple[bool, str]:
    """Return (allowed, reason)."""

    info = parse_target(target)

    if _matches_any_pattern(info.raw, scope.deny_patterns):
        return False, "Denied by pattern"

    if info.kind == "cidr":
        # only allow CIDR if it is fully within at least one allowed CIDR
        try:
            net = ipaddress.ip_network(info.raw, strict=False)
        except Exception:
            return False, "Invalid CIDR"

        for c in scope.allow_cidrs:
            try:
                allow_net = ipaddress.ip_network(str(c), strict=False)
            except Exception:
                continue
            if net.subnet_of(allow_net):
                return True, "CIDR allowed"

        return False, "CIDR not in allowlist"

    if info.kind == "ip":
        if _ip_in_allowed_cidrs(info.host or "", scope.allow_cidrs):
            return True, "IP allowed"
        return False, "IP not in allowlist"

    # url or host
    host = info.host or ""
    if _host_in_allowed_domains(host, scope.allow_domains):
        return True, "Domain allowed"

    return False, "Domain not in allowlist"
