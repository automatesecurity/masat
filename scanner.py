#!/usr/bin/env python3
"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import argparse
import asyncio
import logging
import os
import socket
from urllib.parse import urlparse
from datetime import datetime

# Import Utils and Integrations
from utils.slack_integration import format_findings_for_slack, send_slack_notification

# Import scanner modules
import scanners.web_scanner as web_scanner # TODO: Expand capabilties beyond passive to active checks
import scanners.nmap_scanner as nmap_scanner
import scanners.web_crawler as web_crawler # TODO: Expand crawler capabilities, see roadmap on github
import scanners.tls_scanner as tls_scanner

def resolve_target(target):
    """Extract the hostname from the URL and resolve it to an IP address."""
    parsed = urlparse(target)
    hostname = parsed.hostname if parsed.hostname else target
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        print(f"Could not resolve hostname {hostname}: {e}")
        return hostname  # Fallback to the original target if resolution fails.

def setup_logger(target):
    """Configure logging to a file with a timestamp and sanitized target identifier."""
    # Sanitize the target to remove or replace invalid filename characters
    safe_target = target.replace("://", "_").replace("/", "_").replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"scan_{safe_target}_{timestamp}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    return log_filename

async def run_scans(target, scans, verbose=False):
    """Run selected scan modules asynchronously."""
    results = {}
    tasks = []
    if "web" in scans:
        tasks.append(web_scanner.scan(target, verbose))
    if "crawler" in scans:
        tasks.append(web_crawler.scan(target, verbose))
    if "tls" in scans:
        tasks.append(tls_scanner.scan(target, verbose))
    if "nmap" in scans:
        # Resolve the target to get a valid IP address or hostname for nmap.
        resolved_target = resolve_target(target)
        tasks.append(nmap_scanner.scan(resolved_target, verbose))

    scan_results = await asyncio.gather(*tasks)
    for res in scan_results:
        results.update(res)
    return results

def generate_summary(results):
    """
    Generate a summary of all findings, synthesize the target risk profile,
    and collate remediation guidance.
    """
    summary_lines = []
    vulnerabilities = []
    remediation_guidance = []

    # Process results; here each scanner returns a dict grouped by category.
    for category, findings in results.items():
        summary_lines.append(f"Category: {category}")
        for finding, det in findings.items():
            severity = det.get("severity", 0)
            summary_lines.append(f" - {finding}: Severity {severity}")
            vulnerabilities.append((finding, severity))
            remediation_text = det.get("remediation", "")
            detail_text = det.get("details", "")
            # Merge remediation and details into one line if details exist.
            if detail_text:
                combined = f"{remediation_text} ({detail_text})"
            else:
                combined = remediation_text
            remediation_guidance.append(f"{finding}: {combined}")
    
    # Generate synthesis message.
    if vulnerabilities:
        total = len(vulnerabilities)
        critical = len([v for v in vulnerabilities if v[1] == 10])
        high = len([v for v in vulnerabilities if 7 <= v[1] <= 9])
        medium = len([v for v in vulnerabilities if 5 <= v[1] <= 6])
        synthesis = (
            f"The target contains {total} vulnerabilities "
            f"({critical} Critical, {high} High, {medium} Medium). "
        )
        if critical or high:
            most_severe = [v for v in vulnerabilities if v[1] >= 7]
        else:
            most_severe = [v for v in vulnerabilities if v[1] >= 5]
        synthesis += "Most severe vulnerabilities: " + ", ".join([v[0] for v in most_severe])
    else:
        synthesis = "No vulnerabilities found." # TODO: fix logic issue around low and informational vulnerabilities

    return "\n".join(summary_lines), synthesis, "\n".join(remediation_guidance)

def main():
    parser = argparse.ArgumentParser(
        description="Modular Attack Surface Analysis Tool"
    )
    parser.add_argument("--target", required=True, help="Target URL or IP address")
    parser.add_argument("--scan-all", action="store_true", help="Run all scans")
    parser.add_argument("--web", action="store_true", help="Run web vulnerability scan")
    parser.add_argument("--nmap", action="store_true", help="Run port and service scan")
    parser.add_argument("--crawler", action="store_true", help="Run web crawler scan")
    parser.add_argument("--tls", action="store_true", help="Run SSL/TLS scan")
    parser.add_argument("--verbose", action="store_true", help="Print status to stdout")
    args = parser.parse_args()

    # Determine which scans to run.
    if args.scan_all:
        scans = {"web", "crawler", "tls", "nmap"}
    else:
        scans = set()
        if args.web:
            scans.add("web")
        if args.crawler:
            scans.add("crawler")
        if args.tls:
            scans.add("tls")
        if args.nmap:
            scans.add("nmap")

    if not scans:
        parser.error("No scan type selected. Use --scan-all or specify at least one scan flag.")

    log_file = setup_logger(args.target)
    logging.info(f"Starting scan on target: {args.target}")
    if args.verbose:
        print(f"Logging to file: {log_file}")
        print(f"Starting scan on target: {args.target}")

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(run_scans(args.target, scans, args.verbose))

    summary, synthesis, remediation = generate_summary(results)
    output = (
        "\n=== Scan Summary ===\n" + summary +
        "\n\n=== Synthesis ===\n" + synthesis +
        "\n\n=== Vulnerability Remediation ===\n" + remediation
    )
    print(output)
    logging.info("Scan completed.")
    logging.info(output)

    formatted_message = format_findings_for_slack(results)
    slack_webhook_url = "https://hooks.slack.com/services/your/webhook/url"
    asyncio.run(send_slack_notification(slack_webhook_url, formatted_message, verbose=True))

if __name__ == "__main__":
    main()
