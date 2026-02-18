#!/usr/bin/env python3
"""Nuclei integration for CVE/exposure/misconfig detection.

This scanner shells out to ProjectDiscovery Nuclei if installed.
- It does not bundle templates.
- It can optionally accept a templates directory.

Output is parsed from JSONL.

Install nuclei:
- https://github.com/projectdiscovery/nuclei
"""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any


_SEVERITY_TO_SCORE = {
    "info": 0,
    "low": 3,
    "medium": 5,
    "high": 7,
    "critical": 10,
}


def _severity_score(sev: Any) -> int:
    if sev is None:
        return 0
    if isinstance(sev, (int, float)):
        try:
            return int(sev)
        except Exception:
            return 0
    return _SEVERITY_TO_SCORE.get(str(sev).strip().lower(), 0)

SCAN_ID = "nuclei"
DESCRIPTION = "CVE/exposure/misconfig detection using ProjectDiscovery Nuclei (if installed)."


def _has_nuclei() -> bool:
    return shutil.which("nuclei") is not None


async def scan(target: str, verbose: bool = False, templates: str | None = None, tags: str | None = None) -> dict[str, Any]:
    if not _has_nuclei():
        return {
            "Nuclei": {
                "nuclei not installed": {
                    "severity": 0,
                    "remediation": "Install nuclei to enable CVE detection (https://github.com/projectdiscovery/nuclei).",
                    "details": "",
                }
            }
        }

    cmd = ["nuclei", "-u", target, "-jsonl", "-silent"]
    if templates:
        cmd += ["-t", templates]
    if tags:
        cmd += ["-tags", tags]

    if verbose:
        print(f"[NUCLEI] Running: {' '.join(cmd)}")

    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    out = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace").strip()

    if proc.returncode != 0:
        return {
            "Nuclei": {
                "nuclei execution failed": {
                    "severity": 0,
                    "remediation": "Fix nuclei invocation (templates/tags/target) and re-run.",
                    "details": err or f"nuclei exited with code {proc.returncode}",
                }
            }
        }

    findings: list[dict[str, Any]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            findings.append(json.loads(line))
        except Exception:
            # ignore parse issues
            continue

    # Map nuclei results into a compact summary
    mapped = []
    max_score = 0
    for f in findings:
        info = f.get("info", {}) if isinstance(f.get("info"), dict) else {}
        severity = info.get("severity", "info")
        score = _severity_score(severity)
        max_score = max(max_score, score)

        name = info.get("name") or f.get("template") or "nuclei finding"
        matched = f.get("matched-at") or f.get("host") or target
        reference = info.get("reference")
        if isinstance(reference, list):
            reference = ", ".join(reference)

        mapped.append(
            {
                "name": name,
                "severity": severity,
                "severity_score": score,
                "matched": matched,
                "template": f.get("template"),
                "reference": reference or "",
            }
        )

    details = "\n".join(
        [
            f"- {m['severity']}: {m['name']} @ {m['matched']} ({m['template']}) {m['reference']}".strip()
            for m in mapped
        ]
    )

    return {
        "Nuclei": {
            "Nuclei findings": {
                "severity": max_score if mapped else 0,
                "remediation": "Review nuclei findings; validate and remediate confirmed exposures/CVEs.",
                "details": details if mapped else "None",
            }
        }
    }
