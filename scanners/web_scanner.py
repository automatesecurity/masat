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
import aiohttp
import re
from packaging import version

SCAN_ID = "web"
DESCRIPTION = "Web vulnerability scan (headers, risky methods, library fingerprints)."

# Define vulnerability checks grouped by category.
VULN_CHECKS = {
    "Security Header Misconfigurations": {
        "Missing HSTS": {
            "header": "Strict-Transport-Security",
            "severity": 7,
            "remediation": "Enable HSTS to force HTTPS connections."
        },
        "Missing X-Frame-Options": {
            "header": "X-Frame-Options",
            "severity": 6,
            "remediation": "Implement X-Frame-Options header to prevent clickjacking."
        },
        "Missing CSP": {
            "header": "Content-Security-Policy",
            "severity": 8,
            "remediation": "Use Content Security Policy to mitigate cross-site scripting attacks."
        },
        "Missing X-Content-Type-Options": {
            "header": "X-Content-Type-Options",
            "severity": 6,
            "remediation": "Set X-Content-Type-Options: nosniff to reduce MIME-sniffing attacks."
        },
        "Missing Referrer-Policy": {
            "header": "Referrer-Policy",
            "severity": 5,
            "remediation": "Set a Referrer-Policy to control referrer leakage (e.g., strict-origin-when-cross-origin)."
        },
        "Missing Permissions-Policy": {
            "header": "Permissions-Policy",
            "severity": 5,
            "remediation": "Set a Permissions-Policy to explicitly allow/deny powerful browser features."
        }
    }
}

async def check_header(session, url, header):
    """Check for the presence of a specific header in the target's response."""
    try:
        async with session.get(url, timeout=10) as response:
            return response.headers.get(header)
    except Exception as e:
        logging.error(f"Error checking {header} on {url}: {e}")
        return None

async def check_server(session, url):
    """Check for the Server header in the target's response."""
    try:
        async with session.get(url, timeout=10) as response:
            return response.headers.get("Server")
    except Exception as e:
        logging.error(f"Error checking Server header on {url}: {e}")
        return None

async def check_http_methods(session, url):
    """
    Send an HTTP OPTIONS request to determine which HTTP methods are allowed.
    Returns a list of allowed methods.
    """
    try:
        async with session.options(url, timeout=10) as response:
            allow_header = response.headers.get("Allow")
            if allow_header:
                return [method.strip().upper() for method in allow_header.split(",")]
            return []
    except Exception as e:
        logging.error(f"Error checking HTTP methods on {url}: {e}")
        return []

async def check_third_party_libs(session, url, verbose=False):
    """
    Check the HTML content of the target for references to JQuery and AngularJS,
    and determine if the versions are outdated or vulnerable.
    """
    vulns = {}
    try:
        async with session.get(url, timeout=10) as response:
            html = await response.text()
    except Exception as e:
        logging.error(f"Error retrieving HTML content for third party libs check on {url}: {e}")
        return vulns
    
    # Check for jQuery: search for script tags referencing jquery (e.g., jquery.min.js or jquery.js)
    jquery_match = re.search(r'jquery(?:\.min)?\.js.*?(\d+\.\d+\.\d+)', html, re.IGNORECASE)
    if jquery_match:
        jquery_version = jquery_match.group(1)
        if version.parse(jquery_version) < version.parse("3.5.0"):
            vulns["Outdated jQuery Version"] = {
                "severity": 7,
                "remediation": "Update jQuery to version 3.5.0 or later.",
                "details": f"Detected jQuery version: {jquery_version}"
            }
            if verbose:
                print(f"[WEB SCANNER] Outdated jQuery Version detected: {jquery_version}")
            logging.info(f"Outdated jQuery Version detected: {jquery_version}")
    
    # Check for AngularJS: search for script tags referencing angular (e.g., angular.min.js or angular.js)
    angularjs_match = re.search(r'angular(?:\.min)?\.js.*?(\d+\.\d+\.\d+)', html, re.IGNORECASE)
    if angularjs_match:
        angular_version = angularjs_match.group(1)
        if angular_version.startswith("1."):
            vulns["Outdated AngularJS Version"] = {
                "severity": 7,
                "remediation": "Upgrade AngularJS to the latest supported version or migrate to Angular.",
                "details": f"Detected AngularJS version: {angular_version}"
            }
            if verbose:
                print(f"[WEB SCANNER] Outdated AngularJS Version detected: {angular_version}")
            logging.info(f"Outdated AngularJS Version detected: {angular_version}")
    
    return vulns

async def check_wordpress(session, url, verbose=False):
    """
    Check the HTML content of the target for evidence of WordPress.
    It looks for a meta generator tag (e.g., <meta name="generator" content="WordPress 5.8.1" />)
    or for common WordPress directories (wp-content, wp-includes) as a fallback.
    """
    vulns = {}
    try:
        async with session.get(url, timeout=10) as response:
            html = await response.text()
    except Exception as e:
        logging.error(f"Error retrieving HTML content for WordPress check on {url}: {e}")
        return vulns
    
    # Look for meta generator tag indicating WordPress.
    wp_generator_match = re.search(
        r'<meta\s+name=["\']generator["\']\s+content=["\']WordPress\s*([\d\.]+)?["\']',
        html, re.IGNORECASE
    )
    if wp_generator_match:
        wp_version = wp_generator_match.group(1)
        if wp_version:
            vulns["WordPress Detected"] = {
                "severity": 0,
                "remediation": "This is informational. Ensure your WordPress is kept up-to-date.",
                "details": f"WordPress version {wp_version} detected."
            }
            if verbose:
                print(f"[WEB SCANNER] WordPress detected: version {wp_version}")
            logging.info(f"WordPress detected: version {wp_version}")
        else:
            vulns["WordPress Detected"] = {
                "severity": 0,
                "remediation": "This is informational. Ensure your WordPress is kept up-to-date.",
                "details": "WordPress detected but version could not be determined."
            }
    else:
        # Fallback: check for evidence of WordPress directories.
        if "wp-content" in html or "wp-includes" in html:
            vulns["WordPress Likely Detected"] = {
                "severity": 0,
                "remediation": "This is informational. Ensure your WordPress is kept up-to-date.",
                "details": "Evidence of WordPress structure found (wp-content or wp-includes)."
            }
    return vulns

async def scan(target, verbose=False):
    """
    Perform a web vulnerability scan for missing security headers, risky HTTP methods,
    outdated third party dependencies, WordPress detection, and detect web server technology.
    """
    findings = {}
    category_results = {}

    async with aiohttp.ClientSession() as session:
        # Check for missing security headers.
        tasks = []
        if verbose:
            print(f"[WEB SCANNER] Checking headers for {target}...")
        for finding, details in VULN_CHECKS["Security Header Misconfigurations"].items():
            header_name = details["header"]
            tasks.append(check_header(session, target, header_name))
        headers_results = await asyncio.gather(*tasks)
        for idx, (finding, details) in enumerate(VULN_CHECKS["Security Header Misconfigurations"].items()):
            header_value = headers_results[idx]
            if header_value is None:
                category_results[finding] = {
                    "severity": details["severity"],
                    "remediation": details["remediation"]
                }
                if verbose:
                    print(f"[WEB SCANNER] {finding} detected on {target}")
                logging.info(f"{finding} detected on {target}")
        if category_results:
            findings["Web Vulnerabilities"] = category_results
        else:
            findings["Web Vulnerabilities"] = {
                "No issues detected": {"severity": 0, "remediation": "None"}
            }
        
        # Check for risky HTTP methods.
        if verbose:
            print(f"[WEB SCANNER] Checking for risky HTTP methods...")
        risky_methods = {"PUT", "DELETE", "TRACE", "CONNECT"}
        allowed_methods = await check_http_methods(session, target)
        enabled_risky_methods = [method for method in allowed_methods if method in risky_methods]
        if enabled_risky_methods:
            findings["Risky HTTP Methods"] = {
                "Risky HTTP Methods Enabled": {
                    "severity": 7,
                    "remediation": "Disable unnecessary HTTP methods (PUT, DELETE, TRACE, CONNECT) if not required.",
                    "details": "Enabled methods: " + ", ".join(enabled_risky_methods)
                }
            }

        # Check for outdated third party dependencies (jQuery, AngularJS).
        if verbose:
            print(f"[WEB SCANNER] Checking for vulnerable and EOL libraries and dependecies...")
        outdated_libs = await check_third_party_libs(session, target, verbose)
        if outdated_libs:
            findings["Outdated Third Party Dependencies"] = outdated_libs

        # Check for WordPress detection.
        wp_vulns = await check_wordpress(session, target, verbose)
        if wp_vulns:
            findings["WordPress Detection"] = wp_vulns

        # Detect web server technology using the Server header.
        if verbose:
            print(f"[WEB SCANNER] Fingerprinting {target}...")
        server_header = await check_server(session, target)
        if server_header:
            findings["Web Server Technology"] = {
                "Detected Server": {
                    "severity": 0,
                    "remediation": "This is informational. Verify that the server software is up to date.",
                    "details": f"Server header: {server_header}"
                }
            }
        else:
            findings["Web Server Technology"] = {
                "No Server header found": {
                    "severity": 0,
                    "remediation": "The target did not return a Server header. It might be obscured for security reasons.",
                    "details": ""
                }
            }
    return findings
