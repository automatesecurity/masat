"""Reporting helpers for MASAT outputs."""

from __future__ import annotations

import csv
import html
import io
from typing import Any


def flatten_findings(results: dict[str, Any]) -> list[dict[str, str]]:
    """Flatten nested findings dicts into rows for CSV/HTML."""
    rows: list[dict[str, str]] = []

    for category, items in (results or {}).items():
        if not isinstance(items, dict):
            rows.append(
                {
                    "category": str(category),
                    "finding": "(value)",
                    "severity": "0",
                    "remediation": "",
                    "details": str(items),
                }
            )
            continue

        for finding, details in items.items():
            if isinstance(details, dict):
                rows.append(
                    {
                        "category": str(category),
                        "finding": str(finding),
                        "severity": str(details.get("severity", 0)),
                        "remediation": str(details.get("remediation", "")),
                        "details": str(details.get("details", "")),
                    }
                )
            else:
                rows.append(
                    {
                        "category": str(category),
                        "finding": str(finding),
                        "severity": "0",
                        "remediation": "",
                        "details": str(details),
                    }
                )

    return rows


def to_csv(rows: list[dict[str, str]]) -> str:
    buf = io.StringIO()
    fieldnames = ["category", "finding", "severity", "remediation", "details"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})
    return buf.getvalue()


def to_html(title: str, rows: list[dict[str, str]]) -> str:
    # very small, dependency-free HTML report
    safe_title = html.escape(title)

    def esc(s: str) -> str:
        return html.escape(s or "")

    tr = []
    for r in rows:
        tr.append(
            "<tr>"
            f"<td>{esc(r.get('category',''))}</td>"
            f"<td>{esc(r.get('finding',''))}</td>"
            f"<td style='text-align:right'>{esc(r.get('severity','0'))}</td>"
            f"<td>{esc(r.get('remediation',''))}</td>"
            f"<td><pre style='white-space:pre-wrap;margin:0'>{esc(r.get('details',''))}</pre></td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>{safe_title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f6f6f6; text-align: left; }}
    pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }}
  </style>
</head>
<body>
  <h1>{safe_title}</h1>
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Finding</th>
        <th>Severity</th>
        <th>Remediation</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
      {''.join(tr)}
    </tbody>
  </table>
</body>
</html>
"""
