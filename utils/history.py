"""SQLite run history for MASAT."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any


def default_db_path() -> str:
    """Return the default DB path (no side effects).

    Note: do not create directories here. Only create the directory when the DB
    is actually used (e.g., when --store is set).
    """

    base = os.path.join(os.path.expanduser("~"), ".masat")
    return os.path.join(base, "masat.db")


def _connect(db_path: str) -> sqlite3.Connection:
    # Ensure parent directory exists at time of use.
    #
    # IMPORTANT: `db_path` can be user-provided (CLI/API). We treat it as untrusted.
    # Restrict DB paths to the MASAT data directory (~/.masat) to avoid path traversal
    # and other unsafe filesystem access patterns.

    default_dir = os.path.realpath(os.path.dirname(default_db_path()))
    resolved = os.path.realpath(db_path)

    # Only auto-create the default MASAT directory. For any custom path, require
    # the directory to already exist (avoid unsafe directory creation).
    if os.path.commonpath([resolved, default_dir]) == default_dir:
        os.makedirs(default_dir, exist_ok=True)
    else:
        parent = os.path.dirname(resolved)
        if not os.path.isdir(parent):
            raise ValueError("Custom DB path directory must already exist")

    conn = sqlite3.connect(resolved)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts INTEGER NOT NULL,
          target TEXT NOT NULL,
          scans TEXT NOT NULL,
          results_json TEXT NOT NULL,
          findings_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def store_run(db_path: str, target: str, scans: list[str], results: dict[str, Any], findings: list[dict[str, Any]]) -> int:
    conn = _connect(db_path)
    try:
        ts = int(time.time())
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs (ts, target, scans, results_json, findings_json) VALUES (?, ?, ?, ?, ?)",
            (ts, target, json.dumps(scans), json.dumps(results), json.dumps(findings)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def count_runs(db_path: str) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM runs")
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def count_runs_since(db_path: str, since_ts: int) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM runs WHERE ts >= ?", (int(since_ts),))
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def list_latest_runs_per_target(db_path: str, limit_targets: int = 200) -> list[dict[str, Any]]:
    """Return the latest run row for each target (id, ts, target, scans).

    Uses MAX(id) as the latest run marker.
    """

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.id, r.ts, r.target, r.scans
            FROM runs r
            INNER JOIN (
              SELECT target, MAX(id) AS max_id
              FROM runs
              GROUP BY target
              ORDER BY max_id DESC
              LIMIT ?
            ) t
            ON r.target = t.target AND r.id = t.max_id
            ORDER BY r.id DESC
            """,
            (int(limit_targets),),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()


def list_latest_runs_per_target_asof(db_path: str, asof_ts: int, limit_targets: int = 200) -> list[dict[str, Any]]:
    """Latest run per target as-of a timestamp (ts <= asof_ts)."""

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.id, r.ts, r.target, r.scans
            FROM runs r
            INNER JOIN (
              SELECT target, MAX(id) AS max_id
              FROM runs
              WHERE ts <= ?
              GROUP BY target
              ORDER BY max_id DESC
              LIMIT ?
            ) t
            ON r.target = t.target AND r.id = t.max_id
            ORDER BY r.id DESC
            """,
            (int(asof_ts), int(limit_targets)),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()


def list_runs(db_path: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts, target, scans FROM runs ORDER BY id DESC LIMIT ? OFFSET ?",
            (int(limit), int(offset)),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()


def get_run(db_path: str, run_id: int) -> dict[str, Any] | None:
    """Fetch a single run including stored results + findings."""
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts, target, scans, results_json, findings_json FROM runs WHERE id = ?",
            (int(run_id),),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "ts": row[1],
            "target": row[2],
            "scans": json.loads(row[3]) if row[3] else [],
            "results": json.loads(row[4]) if row[4] else {},
            "findings": json.loads(row[5]) if row[5] else [],
        }
    finally:
        conn.close()


def list_runs_for_target(db_path: str, target: str, limit: int = 20) -> list[dict[str, Any]]:
    """List recent runs for a specific target."""
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts, target, scans FROM runs WHERE target = ? ORDER BY id DESC LIMIT ?",
            (target, limit),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()


def list_runs_matching_host(db_path: str, host: str, limit: int = 20) -> list[dict[str, Any]]:
    """List recent runs whose target string contains the host.

    This supports cases where stored targets are URLs (e.g., https://host) but
    assets are stored as hostnames.

    Note: this is a best-effort match.
    """

    h = (host or "").strip().lower().rstrip(".")
    if not h:
        return []

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts, target, scans FROM runs WHERE LOWER(target) LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{h}%", int(limit)),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()
