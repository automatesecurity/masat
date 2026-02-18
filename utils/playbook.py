"""Generate a safe follow-up playbook (no exploitation).

This implements an "automated exploitation" *adjacent* capability without
actually exploiting anything: it converts findings into recommended next steps
(commands and validation checks) that a human can run.

The goal is to help chain reconnaissance into deeper assessment safely.
"""

from __future__ import annotations

from typing import Any


def generate_playbook(target: str, results: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    # Web header findings
    web_vulns = (results or {}).get("Web Vulnerabilities") or {}
    if isinstance(web_vulns, dict):
        if any(k.startswith("Missing CSP") for k in web_vulns.keys()):
            steps.append(
                {
                    "name": "Review CSP coverage",
                    "type": "manual",
                    "commands": [f"curl -I {target}", f"python3 scanner.py --target {target} --web --verbose"],
                    "notes": "Confirm CSP is present on all relevant endpoints and not overwritten by intermediaries.",
                }
            )

    # Nmap scan output
    nmap = (results or {}).get("Nmap Scan")
    if isinstance(nmap, dict):
        details = None
        for _, v in nmap.items():
            if isinstance(v, dict) and v.get("details"):
                details = v.get("details")
        if details:
            steps.append(
                {
                    "name": "Deepen service enumeration",
                    "type": "manual",
                    "commands": [
                        f"nmap -sV -sC {target}",
                        f"nmap --script banner -sV {target}",
                    ],
                    "notes": "Run additional nmap default scripts and banner collection in a controlled environment.",
                }
            )

    # TLS checks
    if "TLS Scan" in (results or {}):
        steps.append(
            {
                "name": "Validate TLS configuration",
                "type": "manual",
                "commands": [
                    f"python3 scanner.py --target {target} --tls --verbose",
                    f"openssl s_client -connect {target}:443 -servername {target} < /dev/null | head",
                ],
                "notes": "Confirm protocol/cipher guidance and cert chain. Consider running sslyze/sslscan if needed.",
            }
        )

    if not steps:
        steps.append(
            {
                "name": "No playbook steps generated",
                "type": "info",
                "commands": [],
                "notes": "No known mapping for current findings yet.",
            }
        )

    return {"target": target, "steps": steps}
