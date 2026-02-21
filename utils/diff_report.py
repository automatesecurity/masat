"""Diff report rendering (EASM).

Takes a `DiffResult` (from utils.diffing) and renders it into markdown or JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any


def diff_to_json(diff: Any) -> str:
    return json.dumps(asdict(diff), indent=2, sort_keys=True)


def diff_to_markdown(diff: Any) -> str:
    # `diff` is DiffResult
    exposure = diff.exposure or {}
    added_ports = exposure.get("added_ports") or []
    removed_ports = exposure.get("removed_ports") or []
    server_change = exposure.get("server_header")

    lines: list[str] = []
    lines.append(f"# MASAT Diff Report — {diff.target}")
    lines.append("")
    lines.append(f"- **Old run:** #{diff.old_run_id}")
    lines.append(f"- **New run:** #{diff.new_run_id}")
    lines.append("")

    lines.append("## Exposure changes")
    lines.append("")

    if not added_ports and not removed_ports and not server_change:
        lines.append("No exposure changes detected.")
        lines.append("")
    else:
        if added_ports:
            lines.append(f"### Added ports ({len(added_ports)})")
            for p in added_ports[:200]:
                lines.append(f"- {p}")
            if len(added_ports) > 200:
                lines.append(f"- …and {len(added_ports) - 200} more")
            lines.append("")

        if removed_ports:
            lines.append(f"### Removed ports ({len(removed_ports)})")
            for p in removed_ports[:200]:
                lines.append(f"- {p}")
            if len(removed_ports) > 200:
                lines.append(f"- …and {len(removed_ports) - 200} more")
            lines.append("")

        if server_change:
            lines.append("### Server header")
            lines.append(f"- Old: {server_change.get('old')}")
            lines.append(f"- New: {server_change.get('new')}")
            lines.append("")

    lines.append("## Findings changes")
    lines.append("")

    lines.append(f"### New findings ({len(diff.new_findings)})")
    if diff.new_findings:
        for f in diff.new_findings[:100]:
            lines.append(f"- **[{int(f.get('severity', 0))}]** {f.get('title')} ({f.get('category')})")
        if len(diff.new_findings) > 100:
            lines.append(f"- …and {len(diff.new_findings) - 100} more")
    else:
        lines.append("- None")
    lines.append("")

    lines.append(f"### Resolved findings ({len(diff.resolved_findings)})")
    if diff.resolved_findings:
        for f in diff.resolved_findings[:100]:
            lines.append(f"- **[{int(f.get('severity', 0))}]** {f.get('title')} ({f.get('category')})")
        if len(diff.resolved_findings) > 100:
            lines.append(f"- …and {len(diff.resolved_findings) - 100} more")
    else:
        lines.append("- None")
    lines.append("")

    return "\n".join(lines)
