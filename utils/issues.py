"""Issue tracking for MASAT (very lightweight).

Goal: turn scan findings into an actionable queue with ownership + status.

We store issues in SQLite so that triage state persists across scans.
Issues are keyed by a stable fingerprint: (asset, category, title).
"""

from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Issue:
    fingerprint: str
    asset: str
    category: str
    title: str
    severity: int
    status: str  # open|triaged|in_progress|fixed|accepted|false_positive
    owner: str
    environment: str
    first_seen_ts: int
    last_seen_ts: int
    last_run_id: int

    # Remediation workflow fields
    status_updated_ts: int
    resolved_ts: int  # 0 when unresolved; ts when marked fixed/accepted/false_positive
    reopened_count: int

    remediation: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_issues_db_path() -> str:
    base = os.path.join(os.path.expanduser("~"), ".masat")
    return os.path.join(base, "issues.db")


def _connect(db_path: str) -> sqlite3.Connection:
    default_dir = os.path.realpath(os.path.dirname(default_issues_db_path()))
    resolved = os.path.realpath(db_path)

    if os.path.commonpath([resolved, default_dir]) == default_dir:
        os.makedirs(default_dir, exist_ok=True)
    else:
        parent = os.path.dirname(resolved)
        if not os.path.isdir(parent):
            raise ValueError("Custom issues DB path directory must already exist")

    conn = sqlite3.connect(resolved)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
          fingerprint TEXT PRIMARY KEY,
          asset TEXT NOT NULL,
          category TEXT NOT NULL,
          title TEXT NOT NULL,
          severity INTEGER NOT NULL,
          status TEXT NOT NULL,
          owner TEXT NOT NULL,
          environment TEXT NOT NULL,
          first_seen_ts INTEGER NOT NULL,
          last_seen_ts INTEGER NOT NULL,
          last_run_id INTEGER NOT NULL,

          status_updated_ts INTEGER NOT NULL DEFAULT 0,
          resolved_ts INTEGER NOT NULL DEFAULT 0,
          reopened_count INTEGER NOT NULL DEFAULT 0,

          remediation TEXT NOT NULL,
          details TEXT NOT NULL
        )
        """
    )

    # Best-effort lightweight migrations.
    # SQLite doesn't support IF NOT EXISTS for ADD COLUMN; ignore failures.
    for stmt in [
        "ALTER TABLE issues ADD COLUMN status_updated_ts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE issues ADD COLUMN resolved_ts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE issues ADD COLUMN reopened_count INTEGER NOT NULL DEFAULT 0",
    ]:
        try:
            conn.execute(stmt)
        except Exception:
            pass

    conn.commit()
    return conn


def get_issue(db_path: str, fingerprint: str) -> Issue | None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT fingerprint, asset, category, title, severity, status, owner, environment,
                   first_seen_ts, last_seen_ts, last_run_id,
                   status_updated_ts, resolved_ts, reopened_count,
                   remediation, details
            FROM issues
            WHERE fingerprint=?
            """,
            (fingerprint,),
        )
        r = cur.fetchone()
        if not r:
            return None
        return Issue(
            fingerprint=str(r[0]),
            asset=str(r[1]),
            category=str(r[2]),
            title=str(r[3]),
            severity=int(r[4] or 0),
            status=str(r[5] or "open"),
            owner=str(r[6] or ""),
            environment=str(r[7] or ""),
            first_seen_ts=int(r[8] or 0),
            last_seen_ts=int(r[9] or 0),
            last_run_id=int(r[10] or 0),
            status_updated_ts=int(r[11] or 0),
            resolved_ts=int(r[12] or 0),
            reopened_count=int(r[13] or 0),
            remediation=str(r[14] or ""),
            details=str(r[15] or ""),
        )
    finally:
        conn.close()


def upsert_issue(db_path: str, issue: Issue) -> None:
    """Upsert issue while preserving triage fields.

    Preserves:
    - status (unless we auto-reopen)
    - owner
    - environment
    - first_seen_ts

    Auto-reopen behavior:
    - If an issue was marked fixed/accepted/false_positive but is observed again in a new run,
      reopen it (status=open) and increment reopened_count.
    """

    existing = get_issue(db_path, issue.fingerprint)

    first_seen_ts = existing.first_seen_ts if existing else issue.first_seen_ts
    owner = existing.owner if existing and existing.owner else issue.owner
    environment = existing.environment if existing and existing.environment else issue.environment

    now = now_ts()

    if existing:
        was_resolved = existing.status in {"fixed", "accepted", "false_positive"}
        seen_again = int(issue.last_seen_ts) > int(existing.last_seen_ts)

        if was_resolved and seen_again:
            status = "open"
            status_updated_ts = now
            resolved_ts = 0
            reopened_count = int(existing.reopened_count or 0) + 1
        else:
            status = existing.status
            status_updated_ts = int(existing.status_updated_ts or 0)
            resolved_ts = int(existing.resolved_ts or 0)
            reopened_count = int(existing.reopened_count or 0)

        # Backfill missing status_updated_ts for older DBs.
        if not status_updated_ts:
            status_updated_ts = now
    else:
        status = issue.status or "open"
        status_updated_ts = now
        resolved_ts = now if status in {"fixed", "accepted", "false_positive"} else 0
        reopened_count = 0

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO issues (
              fingerprint, asset, category, title, severity, status, owner, environment,
              first_seen_ts, last_seen_ts, last_run_id,
              status_updated_ts, resolved_ts, reopened_count,
              remediation, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              severity=excluded.severity,
              status=excluded.status,
              owner=excluded.owner,
              environment=excluded.environment,
              last_seen_ts=excluded.last_seen_ts,
              last_run_id=excluded.last_run_id,
              status_updated_ts=excluded.status_updated_ts,
              resolved_ts=excluded.resolved_ts,
              reopened_count=excluded.reopened_count,
              remediation=excluded.remediation,
              details=excluded.details
            """,
            (
                issue.fingerprint,
                issue.asset,
                issue.category,
                issue.title,
                int(issue.severity),
                status,
                owner,
                environment,
                int(first_seen_ts),
                int(issue.last_seen_ts),
                int(issue.last_run_id),
                int(status_updated_ts),
                int(resolved_ts),
                int(reopened_count),
                issue.remediation,
                issue.details,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def update_issue_status(db_path: str, fingerprint: str, *, status: str | None = None, owner: str | None = None) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        now = now_ts()

        if status is not None:
            resolved_ts = now if status in {"fixed", "accepted", "false_positive"} else 0
            cur.execute(
                "UPDATE issues SET status=?, status_updated_ts=?, resolved_ts=? WHERE fingerprint=?",
                (status, now, resolved_ts, fingerprint),
            )

        if owner is not None:
            cur.execute("UPDATE issues SET owner=? WHERE fingerprint=?", (owner, fingerprint))

        conn.commit()
    finally:
        conn.close()


def count_issues(db_path: str, *, status: str | None = None) -> int:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        if status:
            cur.execute("SELECT COUNT(1) FROM issues WHERE status=?", (status,))
        else:
            cur.execute("SELECT COUNT(1) FROM issues")
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        conn.close()


def list_issues(db_path: str, *, limit: int = 30, offset: int = 0, status: str | None = None) -> list[Issue]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        if status:
            cur.execute(
                """
                SELECT fingerprint, asset, category, title, severity, status, owner, environment,
                       first_seen_ts, last_seen_ts, last_run_id,
                       status_updated_ts, resolved_ts, reopened_count,
                       remediation, details
                FROM issues
                WHERE status=?
                ORDER BY severity DESC, last_seen_ts DESC
                LIMIT ? OFFSET ?
                """,
                (status, int(limit), int(offset)),
            )
        else:
            cur.execute(
                """
                SELECT fingerprint, asset, category, title, severity, status, owner, environment,
                       first_seen_ts, last_seen_ts, last_run_id,
                       status_updated_ts, resolved_ts, reopened_count,
                       remediation, details
                FROM issues
                ORDER BY severity DESC, last_seen_ts DESC
                LIMIT ? OFFSET ?
                """,
                (int(limit), int(offset)),
            )

        rows = cur.fetchall()
        out: list[Issue] = []
        for r in rows:
            out.append(
                Issue(
                    fingerprint=str(r[0]),
                    asset=str(r[1]),
                    category=str(r[2]),
                    title=str(r[3]),
                    severity=int(r[4] or 0),
                    status=str(r[5] or "open"),
                    owner=str(r[6] or ""),
                    environment=str(r[7] or ""),
                    first_seen_ts=int(r[8] or 0),
                    last_seen_ts=int(r[9] or 0),
                    last_run_id=int(r[10] or 0),
                    status_updated_ts=int(r[11] or 0),
                    resolved_ts=int(r[12] or 0),
                    reopened_count=int(r[13] or 0),
                    remediation=str(r[14] or ""),
                    details=str(r[15] or ""),
                )
            )
        return out
    finally:
        conn.close()


def fingerprint_issue(asset: str, category: str, title: str) -> str:
    a = (asset or "").strip().lower()
    c = (category or "").strip().lower()
    t = (title or "").strip().lower()
    return f"{a}|{c}|{t}"


def now_ts() -> int:
    return int(time.time())
