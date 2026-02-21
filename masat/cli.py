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

    expand = sub.add_parser("expand", help="EASM: expand a domain into concrete assets")
    expand.add_argument("domain", help="Root domain to expand (e.g., example.com)")
    expand.add_argument("--no-ct", action="store_true", help="Disable Certificate Transparency (crt.sh) expansion")
    expand.add_argument("--no-resolve", action="store_true", help="Do not resolve hostnames to IPs")
    expand.add_argument("--max-hosts", type=int, default=500, help="Max hostnames to emit (safety limit)")
    expand.add_argument("--max-dns-lookups", type=int, default=2000, help="Max DNS lookups (safety limit)")
    expand.add_argument("--dns-concurrency", type=int, default=50, help="Max concurrent DNS resolutions")
    expand.add_argument("--output", choices=["text", "json", "csv"], default="text")

    diff = sub.add_parser("diff", help="EASM: diff recent stored runs for a target")
    diff.add_argument("target", help="Target to diff (must match stored target string)")
    diff.add_argument("--last", type=int, default=2, help="How many recent runs to diff (default: 2)")
    diff.add_argument("--db", default=None, help="SQLite DB path (default: ~/.masat/masat.db)")
    diff.add_argument("--output", choices=["text", "json"], default="text")

    assets = sub.add_parser("assets", help="EASM: manage local asset inventory")
    assets_sub = assets.add_subparsers(dest="assets_cmd", required=True)

    assets_import = assets_sub.add_parser("import", help="Import assets from CSV")
    assets_import.add_argument("csv", help="Path to CSV (columns: asset/value, kind?, tags?, owner?, environment?)")
    assets_import.add_argument("--db", default=None, help="Assets DB path (default: ~/.masat/assets.db)")
    assets_import.add_argument("--owner", default="", help="Default owner if not present in CSV")
    assets_import.add_argument("--environment", default="", help="Default environment if not present in CSV")

    assets_list = assets_sub.add_parser("list", help="List assets")
    assets_list.add_argument("--db", default=None, help="Assets DB path (default: ~/.masat/assets.db)")
    assets_list.add_argument("--limit", type=int, default=200)

    scope = sub.add_parser("scope", help="EASM: scope controls")
    scope_sub = scope.add_subparsers(dest="scope_cmd", required=True)

    scope_check = scope_sub.add_parser("check", help="Check if a target is in scope")
    scope_check.add_argument("target", help="Target URL/domain/IP/CIDR")
    scope_check.add_argument("--allow-domain", action="append", default=[], help="Allowed root domain (repeatable)")
    scope_check.add_argument("--allow-cidr", action="append", default=[], help="Allowed CIDR (repeatable)")
    scope_check.add_argument("--deny", action="append", default=[], help="Deny patterns (fnmatch), repeatable")

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

    if ns.cmd == "expand":
        import asyncio
        import json

        from utils.expand import expand_domain

        assets = asyncio.run(
            expand_domain(
                ns.domain,
                use_crtsh=not ns.no_ct,
                resolve=not ns.no_resolve,
                max_hosts=ns.max_hosts,
                max_dns_lookups=ns.max_dns_lookups,
                dns_concurrency=ns.dns_concurrency,
            )
        )

        if ns.output == "json":
            print(json.dumps({"domain": ns.domain, "assets": [a.to_dict() for a in assets]}, indent=2, sort_keys=True))
            return 0

        if ns.output == "csv":
            # Simple CSV: hostname, ips, source
            print("hostname,ips,source")
            for a in assets:
                ips = " ".join(a.ips)
                # naive CSV escaping is ok for these fields
                print(f"{a.hostname},{ips},{a.source}")
            return 0

        # text
        for a in assets:
            ip_part = f" -> {', '.join(a.ips)}" if a.ips else ""
            print(f"{a.hostname}{ip_part} ({a.source})")
        return 0

    if ns.cmd == "diff":
        import json

        from utils.diffing import DiffResult, diff_exposure, diff_findings
        from utils.history import default_db_path, get_run, list_runs_for_target

        db_path = ns.db or default_db_path()
        runs = list_runs_for_target(db_path, ns.target, limit=max(2, int(ns.last)))
        if len(runs) < 2:
            print("Not enough stored runs to diff (need at least 2).")
            return 1

        new_meta = runs[0]
        old_meta = runs[1]

        new_run = get_run(db_path, int(new_meta["id"]))
        old_run = get_run(db_path, int(old_meta["id"]))
        if not new_run or not old_run:
            print("Unable to load runs for diff.")
            return 1

        added, resolved = diff_findings(old_run.get("findings", []), new_run.get("findings", []))
        exposure = diff_exposure(old_run.get("results", {}) or {}, new_run.get("results", {}) or {})
        out = DiffResult(
            target=ns.target,
            old_run_id=int(old_run["id"]),
            new_run_id=int(new_run["id"]),
            new_findings=added,
            resolved_findings=resolved,
            exposure=exposure,
        )

        if ns.output == "json":
            print(json.dumps(out.to_dict(), indent=2, sort_keys=True))
            return 0

        print(f"Diff target: {ns.target}")
        print(f"Old run: #{out.old_run_id}  New run: #{out.new_run_id}")
        print("")

        if out.exposure.get("added_ports") or out.exposure.get("removed_ports") or out.exposure.get("server_header"):
            print("Exposure changes:")
            for p in out.exposure.get("added_ports", [])[:100]:
                print(f"+ port {p}")
            for p in out.exposure.get("removed_ports", [])[:100]:
                print(f"- port {p}")
            if out.exposure.get("server_header"):
                sh = out.exposure["server_header"]
                print(f"~ server header: {sh.get('old')} -> {sh.get('new')}")
            print("")

        print(f"New findings: {len(out.new_findings)}")
        for f in out.new_findings[:50]:
            print(f"+ [{f.get('severity', 0)}] {f.get('category')} :: {f.get('title')}")

        if len(out.new_findings) > 50:
            print(f"  ... ({len(out.new_findings) - 50} more)")

        print("")
        print(f"Resolved findings: {len(out.resolved_findings)}")
        for f in out.resolved_findings[:50]:
            print(f"- [{f.get('severity', 0)}] {f.get('category')} :: {f.get('title')}")

        if len(out.resolved_findings) > 50:
            print(f"  ... ({len(out.resolved_findings) - 50} more)")

        return 0

    if ns.cmd == "assets":
        from utils.assets import (
            default_assets_db_path,
            import_assets_csv,
            list_assets,
        )

        db_path = ns.db or default_assets_db_path()

        if ns.assets_cmd == "import":
            n = import_assets_csv(db_path, ns.csv, default_owner=ns.owner, default_environment=ns.environment)
            print(f"Imported {n} assets into: {db_path}")
            return 0

        if ns.assets_cmd == "list":
            assets = list_assets(db_path, limit=ns.limit)
            for a in assets:
                tags = f" tags={','.join(a.tags)}" if a.tags else ""
                owner = f" owner={a.owner}" if a.owner else ""
                env = f" env={a.environment}" if a.environment else ""
                print(f"{a.kind}:{a.value}{tags}{owner}{env}")
            return 0

        parser.error("unknown assets subcommand")

    if ns.cmd == "scope":
        from utils.assets import ScopeConfig, in_scope

        if ns.scope_cmd == "check":
            scope = ScopeConfig(
                allow_domains=list(ns.allow_domain or []),
                allow_cidrs=list(ns.allow_cidr or []),
                deny_patterns=list(ns.deny or []),
            )
            allowed, reason = in_scope(ns.target, scope)
            if allowed:
                print(f"IN SCOPE: {reason}")
                return 0
            print(f"OUT OF SCOPE: {reason}")
            return 2

        parser.error("unknown scope subcommand")

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
