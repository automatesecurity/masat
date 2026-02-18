"""Normalize MASAT results into a consistent schema for storage/UI."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Finding:
    category: str
    title: str
    severity: int
    remediation: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_findings(results: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []

    for category, items in (results or {}).items():
        if not isinstance(items, dict):
            findings.append(
                Finding(
                    category=str(category),
                    title="(value)",
                    severity=0,
                    remediation="",
                    details=str(items),
                )
            )
            continue

        for title, det in items.items():
            if isinstance(det, dict):
                sev = det.get("severity", 0)
                # allow non-int severities (e.g., nuclei severity strings)
                try:
                    sev_int = int(sev)
                except Exception:
                    # map common strings
                    sev_int = {"info": 0, "low": 3, "medium": 5, "high": 7, "critical": 10}.get(str(sev).lower(), 0)

                findings.append(
                    Finding(
                        category=str(category),
                        title=str(title),
                        severity=sev_int,
                        remediation=str(det.get("remediation", "")),
                        details=str(det.get("details", "")),
                    )
                )
            else:
                findings.append(
                    Finding(
                        category=str(category),
                        title=str(title),
                        severity=0,
                        remediation="",
                        details=str(det),
                    )
                )

    return findings
