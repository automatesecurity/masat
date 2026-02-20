from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import Sequence


def _run_scanner_passthrough(args: Sequence[str]) -> int:
    """Run legacy scanner.py with the provided args."""
    cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "..", "scanner.py"), *args]
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(prog="masat", description="MASAT: Modular Attack Surface Analysis Tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Run a scan")
    scan.add_argument("target", help="Target URL/domain/IP/CIDR")
    scan.add_argument("--smart", action="store_true", help="Auto-select scans based on target")
    scan.add_argument("--plan", action="store_true", help="Print scan plan and exit")
    scan.add_argument("--scans", default=None, help="Comma-separated scan ids")
    scan.add_argument("--scan-all", action="store_true", help="Run all scans")
    scan.add_argument("--verbose", action="store_true")
    scan.add_argument("--output", choices=["text", "json", "csv", "html"], default="text")
    scan.add_argument("--output-file", default=None)
    scan.add_argument("--playbook", action="store_true")
    scan.add_argument("--store", action="store_true")
    scan.add_argument("--db", default=None)
    scan.add_argument("--slack-webhook", default=None)

    list_scans = sub.add_parser("list-scans", help="List available scan modules")

    serve = sub.add_parser("serve", help="Run the MASAT API server (requires extras: api)")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default="8000")
    serve.add_argument("--reload", action="store_true")

    ns = parser.parse_args(argv)

    if ns.cmd == "list-scans":
        return _run_scanner_passthrough(["--list-scans"])

    if ns.cmd == "scan":
        passthrough: list[str] = ["--target", ns.target]
        if ns.smart:
            passthrough.append("--smart")
        if ns.plan:
            passthrough.append("--plan")
        if ns.scans:
            passthrough += ["--scans", ns.scans]
        if ns.scan_all:
            passthrough.append("--scan-all")
        if ns.verbose:
            passthrough.append("--verbose")
        if ns.playbook:
            passthrough.append("--playbook")
        if ns.store:
            passthrough.append("--store")
        if ns.db:
            passthrough += ["--db", ns.db]
        if ns.slack_webhook:
            passthrough += ["--slack-webhook", ns.slack_webhook]

        passthrough += ["--output", ns.output]
        if ns.output_file:
            passthrough += ["--output-file", ns.output_file]

        return _run_scanner_passthrough(passthrough)

    if ns.cmd == "serve":
        # Avoid importing FastAPI at CLI import time.
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.app:app",
            "--host",
            ns.host,
            "--port",
            str(ns.port),
        ]
        if ns.reload:
            cmd.append("--reload")
        return subprocess.call(cmd)

    parser.error("unknown command")
    return 2
