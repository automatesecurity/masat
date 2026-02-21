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
- Python **3.11+**
- `pip`
- Optional: `nmap`
- Optional: `nuclei` (ProjectDiscovery)
- Optional (UI): Node.js 18+

### Clone
```bash
git clone git@github.com:automatesecurity/masat.git
cd masat
```

### Install (recommended)
MASAT is packaged as a Python module with a `masat` CLI.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Optional dev extras:
```bash
pip install -e ".[dev]"
```

Optional API extras:
```bash
pip install -e ".[api]"
```

### Makefile shortcuts
```bash
make venv
make install-dev
make test
```

## Usage

### EASM quickstart (recommended flow)
1) **Expand** a root domain into concrete assets (safe-by-default):
```bash
masat expand example.com --output json > assets.json
```

Safe defaults:
- CT expansion enabled (crt.sh)
- DNS resolution enabled
- Hard limits (`--max-hosts`, `--max-dns-lookups`)

2) **Plan** (dry-run) a smart scan for a target:
```bash
masat plan https://example.com
```

3) **Scan + store** results to local history:
```bash
masat scan https://example.com --smart --store --output json > run.json
```

4) **Diff** what changed between the last two stored runs for a target:
```bash
masat diff https://example.com
```

5) **Browse** results in the UI:
```bash
pip install -e ".[api]"
masat serve --reload
# in another terminal:
cd ui && npm install && npm run dev
```

### List available scans
```bash
masat scans
```

### Smart mode (recommended)
MASAT chooses a scan plan automatically and explains why.

Show the plan only:
```bash
masat plan https://example.com
```

Run the plan:
```bash
masat scan https://example.com --smart --verbose
```

### Explicit scan selection
Run a specific set of scanners:
```bash
masat scan example.com --scans web,tls,nmap,banners
```

Legacy flags still work:
```bash
masat scan http://example.com --web --tls --verbose
```

### Nuclei CVE detection
The `nuclei` scanner shells out to the `nuclei` binary.

```bash
masat scan https://example.com --scans nuclei --verbose
```

Install nuclei: https://github.com/projectdiscovery/nuclei

### Output formats
Text (default):
```bash
masat scan https://example.com --smart
```

JSON:
```bash
masat scan https://example.com --smart --output json --output-file results.json
```

CSV:
```bash
masat scan https://example.com --web --output csv --output-file report.csv
```

HTML:
```bash
masat scan https://example.com --web --output html --output-file report.html
```

### Store run history (SQLite)
Persist runs locally (raw results + normalized findings) for later UI / diffing.

```bash
masat scan https://example.com --smart --output json --store
```

Override DB path:
```bash
masat scan https://example.com --smart --store --db /tmp/masat.db
```

### Slack notifications (optional)
Slack notifications are **skipped** unless configured.

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
masat scan https://example.com --web
```

Or pass a webhook explicitly:
```bash
masat scan https://example.com --web --slack-webhook https://hooks.slack.com/services/...
```

### Generate a safe follow-up playbook
This does **not** exploit anything. It generates recommended next steps/commands.

```bash
masat scan https://example.com --smart --output json --playbook
```

## API server (optional)
A minimal FastAPI app is included (and used by the UI).

Run it:
```bash
pip install -e ".[api]"
masat serve --reload
```

Endpoints:
- `GET /health`
- `GET /scans`
- `POST /scan` (runs scans; optionally stores to SQLite)
- `GET /runs`

## UI (optional)
A simple Next.js UI is included under `ui/`.

Dev mode:
```bash
cd ui
npm install
npm run dev
```

By default it talks to the API server at `http://localhost:8000`. Copy `ui/.env.local.example` to `ui/.env.local` to override.

---

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
- CI also includes a FastAPI import smoke test (API remains optional for core usage).

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
