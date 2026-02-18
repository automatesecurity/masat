"""SQLite run history for MASAT."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any


def default_db_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".masat")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "masat.db")


def _connect(db_path: str) -> sqlite3.Connection:
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
