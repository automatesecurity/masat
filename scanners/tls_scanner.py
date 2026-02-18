#!/usr/bin/env python3
"""
Author: Daniel Wood | 2025-03-18
Modular Attack Surface Analysis Tool
License: Apache 2.0 - https://www.apache.org/licenses/LICENSE-2.0
LinkedIn: https://www.linkedin.com/in/danielewood
GitHub: https://github.com/automatesecurity
"""

SCAN_ID = "tls"
DESCRIPTION = "TLS/SSL scan (protocols, ciphers, cert validity)."
import asyncio
import ssl
import logging
from urllib.parse import urlparse, urlunparse
from datetime import datetime
import aiohttp

def extract_hostname(target):
    """Extract hostname from a URL or return target if already a hostname/IP."""
    parsed = urlparse(target)
    return parsed.hostname if parsed.hostname else target

async def ensure_https_target(url, verbose=False):
    """
    Check if the provided HTTP URL supports HTTPS.
    If so, return the HTTPS version; otherwise, return the original URL.
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() == 'https':
        return url  # Already HTTPS

    # Build an HTTPS version of the URL.
    https_url = urlunparse(("https", parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(https_url, timeout=10, allow_redirects=True) as response:
                if response.status in {200, 301, 302}:
                    if verbose:
                        print(f"Upgrading from HTTP to HTTPS: {https_url}")
                    logging.info(f"HTTPS supported for target: {https_url}")
                    return https_url
    except Exception as e:
        logging.info(f"HTTPS check failed for {https_url}: {e}")
    
    return url  # Fallback to original if HTTPS is not supported

async def scan(target, verbose=False):
    """
    Perform an SSL/TLS scan to detect weak configurations and known vulnerabilities.
    
    Connects to the target (preferring HTTPS if available) on port 443, retrieves the TLS protocol version and 
    cipher suite, then checks for deprecated protocols, export-grade ciphers, weak key lengths,
    BEAST vulnerability, and certificate expiry.
    """
    findings = {}
    port = 443  # default port for HTTPS
    vuln_details = {}

    # Ensure the target is HTTPS if available
    target = await ensure_https_target(target, verbose)
    host = extract_hostname(target)

    try:
        ssl_context = ssl.create_default_context()
        # Establish an asynchronous TLS connection with SNI support
        reader, writer = await asyncio.open_connection(
            host=host,
            port=port,
            ssl=ssl_context,
            server_hostname=host
        )
        ssl_object = writer.get_extra_info('ssl_object')
        if ssl_object is None:
            raise Exception("No SSL object found")
        # Retrieve cipher info: (cipher_name, protocol_version, secret_bits)
        cipher = ssl_object.cipher()
        protocol_version = ssl_object.version()
        if verbose:
            print(f"[TLS SCANNER] Connected to {target}:{port} using {protocol_version} and cipher {cipher[0]}")
        logging.info(f"Connected to {target}:{port} using {protocol_version} and cipher {cipher[0]}")

        # Check for certificate expiry
        cert = ssl_object.getpeercert()
        if cert:
            not_after = cert.get("notAfter")
            if not_after:
                try:
                    # Example format: "Jun  1 12:00:00 2024 GMT"
                    expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    days_left = (expiry_date - datetime.utcnow()).days
                    if days_left < 30:
                        vuln_details["Certificate Expiry Warning"] = {
                            "severity": 3,
                            "remediation": "Renew the SSL certificate before it expires.",
                            "details": f"Certificate expires in {days_left} days on {expiry_date.strftime('%Y-%m-%d')}."
                        }
                except Exception as parse_err:
                    logging.warning(f"Failed to parse certificate expiry date: {parse_err}")

        # Initiate connection closure
        writer.close()
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout=5)
        except asyncio.TimeoutError:
            logging.warning("Timeout while waiting for connection to close; aborting connection.")
            writer.transport.abort()
    except Exception as e:
        logging.error(f"TLS scan failed for {host}: {e}")
        findings["TLS Scan"] = {
            "TLS scan error": {
                "severity": 0,
                "remediation": "Ensure the target supports SSL/TLS connections.",
                "details": str(e)
            }
        }
        return findings

    # Check for deprecated TLS protocols (e.g., TLSv1 and TLSv1.1)
    if protocol_version in ['TLSv1', 'TLSv1.1']:
        vuln_details["Deprecated TLS Protocol"] = {
            "severity": 7,
            "remediation": "Disable TLS 1.0 and TLS 1.1; upgrade to TLS 1.2 or TLS 1.3."
        }

    # Check for export cipher suites
    if "EXPORT" in cipher[0]:
        vuln_details["Export Cipher Suite"] = {
            "severity": 8,
            "remediation": "Disable export-grade cipher suites."
        }
    
    # Check for weak cipher key length (example: less than 128 bits)
    if cipher[2] < 128:
        vuln_details["Weak Cipher"] = {
            "severity": 8,
            "remediation": "Upgrade to a cipher suite with a stronger key length."
        }
    
    # Specific check for BEAST vulnerability (TLSv1 is susceptible)
    if protocol_version == 'TLSv1':
        vuln_details["BEAST Vulnerability"] = {
            "severity": 7,
            "remediation": "Upgrade to TLS 1.2 or higher to mitigate BEAST vulnerability."
        }

    if not vuln_details:
        vuln_details["No TLS issues detected"] = {
            "severity": 0,
            "remediation": "No remediation necessary."
        }

    findings["TLS Scan"] = vuln_details
    return findings
