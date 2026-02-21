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
    # IMPORTANT: `db_path` can be user-provided (CLI/API). Creating directories
    # for arbitrary paths is an unsafe pattern and is flagged by CodeQL.
    # We only auto-create the default MASAT DB directory; for any custom path,
    # require the directory to already exist.
    parent = os.path.dirname(os.path.abspath(db_path))
    default_parent = os.path.dirname(os.path.abspath(default_db_path()))

    if parent and os.path.commonpath([parent, default_parent]) == default_parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(db_path)
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


def list_runs(db_path: str, limit: int = 20) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, ts, target, scans FROM runs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [
            {"id": r[0], "ts": r[1], "target": r[2], "scans": json.loads(r[3]) if r[3] else []}
            for r in rows
        ]
    finally:
        conn.close()


def get_run(db_path: str, run_id: int) -> dict[str, Any] | None:
    """Fetch a full run (including results + findings)."""

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ts, target, scans, results_json, findings_json FROM runs WHERE id = ?",
            (run_id,),
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
