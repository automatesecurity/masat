"""Notification helpers (EASM).

Send notifications only on meaningful change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NotifyDecision:
    should_notify: bool
    reasons: list[str]


def should_notify(diff: dict[str, Any], *, high_sev_threshold: int = 8) -> NotifyDecision:
    reasons: list[str] = []

    exposure = diff.get("exposure") or {}
    added_ports = exposure.get("added_ports") or []
    removed_ports = exposure.get("removed_ports") or []

    if added_ports:
        reasons.append(f"New open ports: {len(added_ports)}")
    if removed_ports:
        reasons.append(f"Ports closed: {len(removed_ports)}")

    if exposure.get("server_header"):
        reasons.append("Server fingerprint changed")

    new_findings = diff.get("new_findings") or []
    high_new = [f for f in new_findings if int(f.get("severity", 0)) >= high_sev_threshold]
    if high_new:
        reasons.append(f"New high-severity findings: {len(high_new)}")

    return NotifyDecision(should_notify=bool(reasons), reasons=reasons)


def format_slack_message(diff: dict[str, Any], decision: NotifyDecision) -> str:
    target = diff.get("target")
    old_id = diff.get("old_run_id")
    new_id = diff.get("new_run_id")

    lines: list[str] = []
    lines.append(f"MASAT EASM change detected for *{target}*")
    lines.append(f"Old run: #{old_id} → New run: #{new_id}")
    lines.append("")

    if decision.reasons:
        lines.append("*Reasons:*")
        for r in decision.reasons:
            lines.append(f"• {r}")
        lines.append("")

    exposure = diff.get("exposure") or {}
    added = exposure.get("added_ports") or []
    if added:
        lines.append("*Added ports:* " + ", ".join(added[:20]) + (" …" if len(added) > 20 else ""))

    return "\n".join(lines)
