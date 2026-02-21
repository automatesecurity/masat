"""Normalize MASAT results into a consistent schema for storage/UI."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Finding:
    # Core
    asset: str
    scanner: str

    # What / why
    category: str
    title: str

    # Scoring
    severity: int
    confidence: str = "unknown"  # low|medium|high|unknown

    # Actionability
    remediation: str = ""
    details: str = ""
    references: list[str] = None  # type: ignore[assignment]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # normalize None -> [] for JSON/UI convenience
        if d.get("references") is None:
            d["references"] = []
        return d


def normalize_findings(results: dict[str, Any], *, asset: str = "") -> list[Finding]:
    findings: list[Finding] = []

    for category, items in (results or {}).items():
        scanner = str(category)

        if not isinstance(items, dict):
            findings.append(
                Finding(
                    asset=asset,
                    scanner=scanner,
                    category=str(category),
                    title="(value)",
                    severity=0,
                    remediation="",
                    details=str(items),
                    references=[],
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

                refs = det.get("references")
                if isinstance(refs, list):
                    references = [str(x) for x in refs]
                elif isinstance(refs, str):
                    references = [refs]
                else:
                    references = []

                findings.append(
                    Finding(
                        asset=asset,
                        scanner=scanner,
                        category=str(category),
                        title=str(title),
                        severity=sev_int,
                        confidence=str(det.get("confidence", "unknown")),
                        remediation=str(det.get("remediation", "")),
                        details=str(det.get("details", "")),
                        references=references,
                    )
                )
            else:
                findings.append(
                    Finding(
                        asset=asset,
                        scanner=scanner,
                        category=str(category),
                        title=str(title),
                        severity=0,
                        remediation="",
                        details=str(det),
                        references=[],
                    )
                )

    return findings
