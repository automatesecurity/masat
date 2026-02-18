# MASAT: Modular Attack Surface Analysis Tool
[![GitHub license](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)

MASAT is a modular, Python-based tool designed to automate lightweight **attack surface discovery** and **security signal collection** for web apps and infrastructure.

It consolidates multiple scanners into one workflow so you can point it at a **URL / domain / IP / CIDR** and quickly get actionable findings.

## What MASAT can do today

- **Web checks**: security headers, risky HTTP methods, light dependency fingerprinting
- **TLS checks**: TLS protocol/cipher/cert signal
- **Port & service discovery**: via `nmap` (host/IP/CIDR)
- **Banner grabbing**: quick fingerprints for common services (ssh/smtp/ftp/http)
- **Subdomain enumeration (passive)**: via Certificate Transparency (`crt.sh`)
- **CVE / misconfig / exposure detection**: **ProjectDiscovery Nuclei** integration (if `nuclei` is installed)
- **Reporting**: `text`, `json`, `csv`, `html`
- **Smart workflows**: auto-select sensible scans based on target type (`--smart`, `--plan`)
- **Run history**: optional local SQLite persistence (foundation for a future UI portal)
- **API server scaffold**: optional FastAPI app (foundation for a future UI portal)

## Installation

### Prerequisites
- Python 3.11+ recommended
- `pip`
- Optional: `nmap`
- Optional: `nuclei` (ProjectDiscovery)

### Clone
```bash
git clone git@github.com:automatesecurity/masat.git
cd masat
```

### Install dependencies
```bash
pip install -r requirements.txt
```

Optional dev dependencies:
```bash
pip install -r requirements-dev.txt
```

Optional API dependencies:
```bash
pip install -r requirements-api.txt
```

## Usage

### List available scans
```bash
python3 scanner.py --list-scans
```

### Smart mode (recommended)
MASAT chooses a scan plan automatically and explains why.

Show the plan only:
```bash
python3 scanner.py --target https://example.com --plan
```

Run the plan:
```bash
python3 scanner.py --target https://example.com --smart --verbose
```

### Explicit scan selection
Run a specific set of scanners:
```bash
python3 scanner.py --target example.com --scans web,tls,nmap,banners
```

Legacy flags still work:
```bash
python3 scanner.py --target http://example.com --web --tls --verbose
```

### Nuclei CVE detection
The `nuclei` scanner shells out to the `nuclei` binary.

```bash
python3 scanner.py --target https://example.com --scans nuclei --verbose
```

Install nuclei: https://github.com/projectdiscovery/nuclei

### Output formats
Text (default):
```bash
python3 scanner.py --target https://example.com --smart
```

JSON:
```bash
python3 scanner.py --target https://example.com --smart --output json --output-file results.json
```

CSV:
```bash
python3 scanner.py --target https://example.com --web --output csv --output-file report.csv
```

HTML:
```bash
python3 scanner.py --target https://example.com --web --output html --output-file report.html
```

### Store run history (SQLite)
Persist runs locally (raw results + normalized findings) for later UI / diffing.

```bash
python3 scanner.py --target https://example.com --smart --output json --store
```

Override DB path:
```bash
python3 scanner.py --target https://example.com --smart --store --db /tmp/masat.db
```

### Slack notifications (optional)
Slack notifications are **skipped** unless configured.

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python3 scanner.py --target https://example.com --web
```

Or pass a webhook explicitly:
```bash
python3 scanner.py --target https://example.com --web --slack-webhook https://hooks.slack.com/services/...
```

### Generate a safe follow-up playbook
This does **not** exploit anything. It generates recommended next steps/commands.

```bash
python3 scanner.py --target https://example.com --smart --output json --playbook
```

## API server (foundation for UI portal)
A minimal FastAPI app is included to support the long-term UI portal goal.

Run it:
```bash
pip install -r requirements.txt -r requirements-api.txt
uvicorn api.app:app --reload
```

Endpoints:
- `GET /health`
- `GET /scans`
- `POST /scan` (runs scans; optionally stores to SQLite)
- `GET /runs`

## Testing & CI
Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

CI:
- GitHub Actions runs pytest + coverage on PRs and pushes.

## Contributing
See [CONTRIBUTING.md](https://github.com/automatesecurity/masat/blob/main/CONTRIBUTING.md).

## Roadmap (next-level MASAT)
The long-term goal is a UI portal where a user enters a domain/IP/CIDR and MASAT expands and scans the target’s attack surface intelligently.

Near-term additions:
- Better target expansion (DNS brute wordlists, resolving + dedupe)
- CIDR strategies with safety limits (host discovery + scoped scanning)
- Job queue + scan status for the API server
- Normalize all scanners to a consistent finding schema (in progress)
- Deeper Nuclei mapping (asset linkage + references + confidence)
