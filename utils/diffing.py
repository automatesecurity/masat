"""Diff utilities for EASM.

Focused on answering: what changed between two runs?

We diff at two layers:
- Findings: normalized finding tuples
- Exposure-ish signals: attempt to detect open ports changes from raw results when available

This is intentionally basic and evidence-preserving.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass(frozen=True)
class DiffResult:
    target: str
    old_run_id: int
    new_run_id: int
    new_findings: list[dict[str, Any]]
    resolved_findings: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finding_key(f: dict[str, Any]) -> tuple[str, str, str]:
    # Use stable keys; tolerate schema changes.
    asset = str(f.get("asset", ""))
    category = str(f.get("category", ""))
    title = str(f.get("title", ""))
    return (asset, category, title)


def diff_findings(old: Iterable[dict[str, Any]], new: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    old_map = {_finding_key(f): f for f in (old or [])}
    new_map = {_finding_key(f): f for f in (new or [])}

    new_keys = set(new_map.keys())
    old_keys = set(old_map.keys())

    added = [new_map[k] for k in sorted(new_keys - old_keys)]
    resolved = [old_map[k] for k in sorted(old_keys - new_keys)]
    return added, resolved
