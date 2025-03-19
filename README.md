# MASAT: Modular Attack Surface Analysis Tool
[![GitHub license](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

MASAT is a modular, Python-based tool designed to automate the reconnaissance and vulnerability assessment process for web applications and network infrastructure. It consolidates multiple scanners into one platform, enabling you to:

- **Web Vulnerability Scanning:** Check for missing security headers (e.g., X-XSS-Protection, HSTS, X-Frame-Options, CSP) and risky HTTP methods.
- **Port and Service Scanning:** Leverage nmap to discover open ports, services, and service version information in a human-readable format.
- **TLS/SSL Scanning:** Analyze SSL/TLS configurations to detect weak protocols, vulnerable cipher suites, certificate expiry issues, and more. The tool even upgrades HTTP targets to HTTPS when available.
- **Web Crawling:** (Optional module) Identify sensitive files and directories to further map your target's attack surface.

MASAT follows a modular, asynchronous design that makes it easy to add custom scanner modules in the future.

## Features

- **Modular Architecture:** Easily extend or modify individual scanner modules.
- **Asynchronous Execution:** Uses Python's asyncio to run multiple scans concurrently, reducing overall scan time.
- **Detailed Reporting:** Generates a summary including synthesis of findings, prioritized vulnerabilities, and actionable remediation recommendations.
- **Human-Readable Output:** Formats open port results in a clear, tabular layout.
- **Flexible Output Options:** Command-line flags to run individual scans or the entire suite (`--scan-all`).
- **HTTPS Upgrade:** Automatically detects if a target supports HTTPS and upgrades accordingly to ensure accurate TLS/SSL scans.

## Installation

### Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/en/stable/)

### Clone the Repository

```bash
git clone git@github.com:automatesecurity/masat.git
cd masat
```

### Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage
Run the tool from the command line with various flags:

To run all scanners on a target:
```bash
python3 scanner.py --target http://example.com --scan-all --verbose
```
To run specific modules:
```bash
python3 scanner.py --target http://example.com --web --tls --verbose
```

Command-Line Flags
- **--target**: The URL or IP address of the target.
- **--scan-all**: Run all scanner modules.
- **--web**: Run only the web vulnerability scanner.
- **--nmap**: Run only the port/service scanner (nmap).
- **--crawler**: Run only the web crawler.
- **--tls**: Run only the SSL/TLS scanner.
- **--verbose**: Enable verbose output to show progress messages.

## Testing & Code Coverage
MASAT includes a comprehensive suite of unit tests to ensure reliability and maintainability. The project uses **pytest** for test execution and **pytest-asyncio** for testing asynchronous functions. Code coverage is measured using **pytest-cov** to track test effectiveness and identify untested areas of the codebase.

**Running Tests**
To run the test suite, execute:
```bash
pytest
```
To check code coverage:
```bash
pytest --cov=masat --cov-report=term-missing
```
This will provide a detailed report of covered and uncovered code paths. A higher coverage percentage indicates a well-tested codebase.

**Continuous Integration**
MASAT is designed for extensibility, and new scanner modules should include accompanying test cases. The project follows Test-Driven Development (TDD) principles where applicable, ensuring stability and catching regressions early. Future CI/CD pipeline integration will automate test execution and enforce coverage thresholds.

## Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.
Create a feature branch (git checkout -b feature/my-new-feature).
Commit your changes (git commit -am 'Add new feature').
Push to your branch (git push origin feature/my-new-feature).
Create a new Pull Request.
See CONTRIBUTING.md for more details.

## License
This project is licensed under the Apache License 2.0. See the LICENSE file for details.

Author: Daniel Wood

## Future Improvements
- **Enhanced Recon**: Integrate subdomain enumeration and additional OSINT modules.
- **Expanded Banner Grabbing**: Support additional protocols beyond HTTP, such as FTP, SSH, and SMTP.
- **Automated Exploitation**: Develop service-specific exploitation chaining based on identified vulnerabilities.
- **Multiple Output Formats**: Add support for JSON, CSV, and HTML reports.
- **Plugin Architecture**: Allow third-party modules to be dynamically loaded for further extensibility.