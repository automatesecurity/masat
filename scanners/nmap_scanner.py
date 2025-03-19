#!/usr/bin/env python3
"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""
import asyncio
import logging

def format_open_ports(open_ports):
    """Format the open ports list into a human-readable table."""
    if not open_ports:
        return "No open ports found."
    
    # Define header names.
    headers = ["Port", "Service", "Version"]
    
    # Calculate column widths.
    width_port = max(len("Port"), *(len(entry.get("port", "")) for entry in open_ports))
    width_service = max(len("Service"), *(len(entry.get("service", "")) for entry in open_ports))
    width_version = max(len("Version"), *(len(entry.get("version", "")) for entry in open_ports))
    
    # Build the header row.
    header_row = f"{'Port'.ljust(width_port)}  {'Service'.ljust(width_service)}  {'Version'.ljust(width_version)}"
    separator = f"{'-'*width_port}  {'-'*width_service}  {'-'*width_version}"
    
    # Build data rows.
    rows = []
    for entry in open_ports:
        port = entry.get("port", "").ljust(width_port)
        service = entry.get("service", "").ljust(width_service)
        version = entry.get("version", "").ljust(width_version)
        rows.append(f"{port}  {service}  {version}")
    
    return "\n".join([header_row, separator] + rows)

async def scan(target, verbose=False):
    """
    Perform an nmap scan on the target, parse the output to extract open ports,
    associated services, and service version information, then return a structured
    and human-readable summary.
    """
    findings = {}
    try:
        if verbose:
            print(f"[NMAP SCANNER] Scan in progress for {target}...")
        cmd = ["nmap", "-sV", target]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode()

        # Log raw scan results for debugging purposes.
        logging.info(f"Nmap scan raw output: {output}")

        # Parse the raw nmap output to extract open ports, services, and version info.
        open_ports = []
        lines = output.splitlines()
        in_port_section = False
        for line in lines:
            if line.strip().startswith("PORT"):
                in_port_section = True
                continue
            if in_port_section:
                if not line.strip() or "/" not in line:
                    break
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0]
                    service = parts[2]
                    version_info = " ".join(parts[3:]) if len(parts) > 3 else ""
                    open_ports.append({
                        "port": port,
                        "service": service,
                        "version": version_info
                    })
        
        # Format the open ports list into a human-readable table.
        formatted_ports = format_open_ports(open_ports)
        
        findings["Nmap Scan"] = {
            "\nOpen Ports": {
                "severity": 0,
                "remediation": "Review open ports for necessary security controls.\n",
                "details": formatted_ports
            }
        }
    except Exception as e:
        logging.error(f"Nmap scan failed: {e}")
        findings["Nmap Scan"] = {
            "error": str(e),
            "severity": 0,
            "remediation": "Ensure nmap is installed and accessible."
        }
    return findings
