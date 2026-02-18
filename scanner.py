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
import json
import logging
import os
import socket
from urllib.parse import urlparse
from datetime import datetime

# Import Utils and Integrations
from utils.slack_integration import format_findings_for_slack, send_slack_notification
from utils.reporting import flatten_findings, to_csv, to_html

from scanners.registry import discover_scanners

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
    registry = discover_scanners()

    results = {}
    tasks = []

    for scan_id in sorted(scans):
        spec = registry.get(scan_id)
        if not spec:
            raise ValueError(f"Unknown scan id: {scan_id}. Use --list-scans to see available scanners.")

        # Resolve the target to get a valid IP address or hostname for nmap.
        if scan_id == "nmap":
            scan_target = resolve_target(target)
        else:
            scan_target = target

        tasks.append(spec.scan(scan_target, verbose))

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
    parser.add_argument("--target", required=False, help="Target URL or IP address")
    parser.add_argument("--scan-all", action="store_true", help="Run all scans")
    parser.add_argument("--list-scans", action="store_true", help="List available scans and exit")

    # Backwards-compatible scan flags
    parser.add_argument("--web", action="store_true", help="Run web vulnerability scan")
    parser.add_argument("--nmap", action="store_true", help="Run port and service scan")
    parser.add_argument("--crawler", action="store_true", help="Run web crawler scan")
    parser.add_argument("--tls", action="store_true", help="Run SSL/TLS scan")

    # Preferred: explicit scan selection
    parser.add_argument(
        "--scans",
        default=None,
        help="Comma-separated list of scans to run (e.g., web,tls,nmap). Overrides individual scan flags.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print status to stdout")
    parser.add_argument(
        "--playbook",
        action="store_true",
        help="Generate a safe follow-up playbook (no exploitation) from findings.",
    )

    parser.add_argument(
        "--output",
        choices=["text", "json", "csv", "html"],
        default="text",
        help="Output format for results.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional path to write output (defaults to stdout).",
    )

    # Integrations
    parser.add_argument(
        "--slack-webhook",
        default=os.getenv("SLACK_WEBHOOK_URL"),
        help="Slack Incoming Webhook URL (or set SLACK_WEBHOOK_URL). If unset, Slack notification is skipped.",
    )
    args = parser.parse_args()

    registry = discover_scanners()

    if args.list_scans:
        print("Available scans:")
        for scan_id, spec in registry.items():
            desc = f" — {spec.description}" if spec.description else ""
            print(f"- {scan_id}{desc}")
        return

    if not args.target:
        parser.error("--target is required unless using --list-scans")

    # Determine which scans to run.
    if args.scans:
        scans = {s.strip() for s in args.scans.split(",") if s.strip()}
    elif args.scan_all:
        scans = set(registry.keys())
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
        parser.error("No scan type selected. Use --scan-all, --scans, or specify at least one scan flag.")

    log_file = setup_logger(args.target)
    logging.info(f"Starting scan on target: {args.target}")
    if args.verbose:
        print(f"Logging to file: {log_file}")
        print(f"Starting scan on target: {args.target}")

    results = asyncio.run(run_scans(args.target, scans, args.verbose))

    summary, synthesis, remediation = generate_summary(results)

    if args.output == "json":
        payload = {
            "target": args.target,
            "scans": sorted(list(scans)),
            "results": results,
            "summary": summary,
            "synthesis": synthesis,
            "remediation": remediation,
        }
        if args.playbook:
            payload["playbook"] = generate_playbook(args.target, results)
        output = json.dumps(payload, indent=2, sort_keys=True)
    elif args.output == "csv":
        rows = flatten_findings(results)
        output = to_csv(rows)
    elif args.output == "html":
        rows = flatten_findings(results)
        output = to_html(title=f"MASAT Report — {args.target}", rows=rows)
    else:
        output = (
            "\n=== Scan Summary ===\n" + summary +
            "\n\n=== Synthesis ===\n" + synthesis +
            "\n\n=== Vulnerability Remediation ===\n" + remediation
        )

    if args.output_file:
        mode = "wb" if args.output == "html" else "w"
        with open(args.output_file, mode, encoding=None if mode == "wb" else "utf-8") as f:
            if mode == "wb":
                f.write(output.encode("utf-8"))
            else:
                f.write(output)
        if args.verbose:
            print(f"Wrote output to: {args.output_file}")
    else:
        print(output)

    logging.info("Scan completed.")
    logging.info(output)

    # Optional Slack notification
    if args.slack_webhook:
        formatted_message = format_findings_for_slack(results)
        asyncio.run(send_slack_notification(args.slack_webhook, formatted_message, verbose=args.verbose))
    else:
        logging.info("Slack webhook not configured; skipping Slack notification.")

if __name__ == "__main__":
    main()
