"""Report templates for MASAT (EASM oriented).

Principles:
- Executive summary first (what changed / what matters)
- Engineer appendix with evidence + remediation
- Deterministic, easy to diff

Keep it lightweight: markdown + minimal HTML wrapper.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _sev_bucket(sev: int) -> str:
    if sev >= 8:
        return "high"
    if sev >= 4:
        return "medium"
    return "low"


@dataclass(frozen=True)
class RunForReport:
    id: int
    ts: int
    target: str
    scans: list[str]
    results: dict[str, Any]
    findings: list[dict[str, Any]]


def run_to_markdown(run: RunForReport) -> str:
    dt = datetime.fromtimestamp(int(run.ts), tz=timezone.utc).isoformat()
    findings = list(run.findings or [])
    findings.sort(key=lambda f: int(f.get("severity", 0)), reverse=True)

    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[_sev_bucket(int(f.get("severity", 0)))] += 1

    lines: list[str] = []
    lines.append(f"# MASAT Report — Run #{run.id}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Target:** {run.target}")
    lines.append(f"- **Timestamp (UTC):** {dt}")
    lines.append(f"- **Scans:** {', '.join(run.scans) if run.scans else '(none)'}")
    lines.append(
        f"- **Findings:** {len(findings)} (High: {counts['high']}, Medium: {counts['medium']}, Low: {counts['low']})"
    )
    lines.append("")

    if not findings:
        lines.append("No findings.")
        lines.append("")
        return "\n".join(lines)

    # Top findings summary
    lines.append("## Top findings")
    lines.append("")
    for f in findings[:10]:
        sev = int(f.get("severity", 0))
        title = str(f.get("title", "(untitled)"))
        cat = str(f.get("category", ""))
        lines.append(f"- **[{sev}]** {title}" + (f" ({cat})" if cat else ""))
    if len(findings) > 10:
        lines.append(f"- …and {len(findings) - 10} more")
    lines.append("")

    # Engineer appendix
    lines.append("## Findings (detailed)")
    lines.append("")
    for i, f in enumerate(findings, 1):
        sev = int(f.get("severity", 0))
        bucket = _sev_bucket(sev).upper()
        title = str(f.get("title", "(untitled)"))
        cat = str(f.get("category", ""))
        details = str(f.get("details", "") or "").strip()
        remediation = str(f.get("remediation", "") or "").strip()

        lines.append(f"### {i}. [{bucket}:{sev}] {title}" + (f" ({cat})" if cat else ""))
        lines.append("")
        if details:
            lines.append(details)
            lines.append("")
        if remediation:
            lines.append("**Remediation:**")
            lines.append("")
            lines.append(remediation)
            lines.append("")

    return "\n".join(lines)


def run_to_html(run: RunForReport) -> str:
    md = run_to_markdown(run)
    # Minimal HTML wrapper; markdown is embedded in <pre> for now.
    # (We can render markdown properly later if we add a renderer.)
    esc = (
        md.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>MASAT Report — Run #{run.id}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 32px; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f6f6f6; padding: 16px; border-radius: 10px; }}
  </style>
</head>
<body>
  <pre>{esc}</pre>
</body>
</html>"""


def run_to_json(run: RunForReport) -> str:
    payload = {
        "id": run.id,
        "ts": run.ts,
        "target": run.target,
        "scans": run.scans,
        "results": run.results,
        "findings": run.findings,
    }
    return json.dumps(payload, indent=2, sort_keys=True)
