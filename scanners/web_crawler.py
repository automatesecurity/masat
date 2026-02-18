#!/usr/bin/env python3
"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""

SCAN_ID = "crawler"
DESCRIPTION = "Web crawler (discover endpoints and common sensitive paths)."
import asyncio
import logging
import aiohttp

COMMON_PATHS = ["/.git/", "/admin/", "/config.php", "/.env"] # TODO: Expand to active fuzzing based on a dictionary


async def crawl_url(session, target, path):
    """Attempt to access a common sensitive path."""
    try:
        url = target.rstrip("/") + path
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return path, True
            else:
                return path, False
    except Exception:
        return path, False


async def scan(target, verbose=False):
    """Perform a web crawler scan for sensitive files or directories."""
    findings = {}
    sensitive_findings = {}
    async with aiohttp.ClientSession() as session:
        tasks = [crawl_url(session, target, path) for path in COMMON_PATHS]
        results = await asyncio.gather(*tasks)
        for path, found in results:
            if found:
                sensitive_findings[f"Sensitive path found: {path}"] = {
                    "severity": 7,
                    "remediation": f"Restrict access to {path}."
                }
                if verbose:
                    print(f"[WEB CRAWLER] Sensitive path found: {path}")
                logging.info(f"Sensitive path found: {path}")
    if sensitive_findings:
        findings["Web Crawler Findings"] = sensitive_findings
    else:
        findings["Web Crawler Findings"] = {
            "No sensitive files or paths detected": {"severity": 0, "remediation": "None"}
        }
    return findings
