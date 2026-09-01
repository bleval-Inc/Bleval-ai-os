# Axiom AI OS

**AI Operating System** — coordinate executives, departments, workflows, and agents across any number of organizations.

Axiom OS is a general-purpose runtime for autonomous AI agents. It provides:

- **Executive agents** — strategic AI leaders that monitor, prioritize, and delegate
- **Department workflows** — structured multi-step processes for sales, marketing, development, finance, and operations
- **Event bus** — publish-subscribe messaging for inter-agent coordination
- **Memory system** — layered knowledge (global → org → department → agent) with upward-learning
- **Intelligence engine** — provider-agnostic model routing (Anthropic Claude, OpenAI GPT, or mock)
- **REST API + CLI** — dual interface for control and observability

---

## Quick Start

### Prerequisites

- **Python 3.11+** (tested on 3.11.15)
- **pip** (comes with Python)
- **Git** (for cloning)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url> axiom-ai-os
cd axiom-ai-os

# 2. Create and activate a Python virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate

# 3. Install runtime dependencies
pip install -r requirements.txt
```

### Start the API Server

```bash
# From the backend/ directory with .venv activated
uvicorn main:app --reload
```

The server starts at **http://localhost:8000**.

- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- System status: [http://localhost:8000/](http://localhost:8000/)

### Using the CLI

```bash
# Optional: install the CLI globally
pip install -e .

# Then use from anywhere
axiom status
axiom workflows
axiom agents
axiom organisations

# Or run directly without installation
python -m axiom.cli.main status
```

---

## Project Structure

```
backend/
├── main.py                  # FastAPI entry point (uvicorn)
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Dev/test dependencies
├── pyproject.toml           # Package metadata & build config
│
├── axiom/                   # Core Python package
│   ├── config.py            # Path resolution & environment settings
│   ├── models/              # Pydantic data models
│   ├── registry/            # YAML configuration loaders
│   ├── engine/              # Core platform engines
│   └── runtime/             # Execution layer
│
├── .venv/                   # Virtual environment (gitignored)
└── runtime/                 # Runtime state (gitignored, created at startup)
    ├── state/               #   Persisted workflow instances
    ├── events/              #   Persisted event log
    └── logs/                #   Structured runtime logs

agents/                       # Agent definitions (YAML + Markdown)
capabilities/                 # Capability catalog & search index
core/                         # Executive definitions
departments/                  # Department definitions
events/                       # Event bus config, types, schemas, subscriptions
memory/                       # Layered memory files
organizations/                # Organization definitions
workflows/                    # Workflow definitions
```

---

## Configuration

Axiom OS reads environment variables from a `.env` file in the repo root or backend directory.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | No | — | Enables Anthropic Claude providers |
| `OPENAI_API_KEY` | No | — | Enables OpenAI GPT providers (fallback) |
| `RUFLO_ENV` | No | `development` | Environment label |

If neither API key is set, the system runs in **mock mode** — all intelligence operations return structured canned responses. This is useful for testing the orchestration layer without consuming API tokens.

---

## Verification

After starting the server, verify everything is working:

```bash
# Root endpoint
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# List registered executives
curl http://localhost:8000/api/v1/executives

# List registered workflows
curl http://localhost:8000/api/v1/workflows

# List organizations
curl http://localhost:8000/api/v1/organisations
```

Expected root response:

```json
{
  "service": "Axiom OS",
  "version": "3.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Install as editable package (syncs `axiom` CLI command)
pip install -e .
```

---

## License

MIT


<!-- 
PS C:\Users\byagi> & ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.ps1")))

==> Checking for running Free Claude Code processes

==> Choosing coding agents
Install or verify Claude Code for fcc-claude? [Y/n]: y
Install or verify Codex for fcc-codex? [Y/n]: y
Install or verify Pi for fcc-pi? [Y/n]: y
Install or verify OpenCode for fcc-opencode? [Y/n]: y
Install or verify Cline CLI for fcc-cline? [Y/n]: y
Install or verify Hermes Agent for fcc-hermes? [Y/n]: y
Install or verify DeepSeek Harness for fcc-dsh? [Y/n]: y
Install or verify Grok Build for fcc-grok? [Y/n]: y
Install or verify Muse Code for fcc-muse? [Y/n]: y
Enable RTK token optimization globally for the selected coding agents? [y/N]: y

==> Ensuring Claude Code is installed
+ irm https://claude.ai/install.ps1 -OutFile C:\Users\byagi\AppData\Local\Temp\fcc-install-12745a16243a40b58e807818109a69d3.ps1
+ C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\byagi\AppData\Local\Temp\fcc-install-12745a16243a40b58e807818109a69d3.ps1
Setting up Claude Code...

✔ Claude Code successfully installed!

  Version: 2.1.246

  Location: C:\Users\byagi\.local\bin\claude.exe


  Next: Run claude --help to get started

✅ Installation complete!

+ C:\Users\byagi\.local\bin\claude.exe --version
2.1.246 (Claude Code)

==> Ensuring Codex is installed
+ irm https://chatgpt.com/codex/install.ps1 -OutFile C:\Users\byagi\AppData\Local\Temp\fcc-install-9b78a118b4584ef981c303c553d169a5.ps1
+ C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\byagi\AppData\Local\Temp\fcc-install-9b78a118b4584ef981c303c553d169a5.ps1
==> Installing Codex CLI
==> Detected platform: Windows (x64)
==> Resolved version: 0.149.1
==> Downloading Codex CLI
==> PATH updated for future PowerShell sessions.
==> Current PowerShell session: codex
==> Future PowerShell windows: open a new PowerShell window and run: codex
Codex CLI 0.149.1 installed successfully.
+ C:\Users\byagi\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe --version
codex-cli 0.149.1

==> Checking or installing Pi
+ irm https://pi.dev/install.ps1 -OutFile C:\Users\byagi\AppData\Local\Temp\fcc-install-66bc45effe884d48b64d1dbfed83cf5a.ps1
+ C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\byagi\AppData\Local\Temp\fcc-install-66bc45effe884d48b64d1dbfed83cf5a.ps1



  ██████
  ██  ██
  ████  ██
  ██    ██



  Pi Installer
  There are many coding agents, but this one is mine.

Install command:

  npm.cmd install -g --ignore-scripts --min-release-age=0 @earendil-works/pi-coding-agent

Choose an action:

  y    Install Pi (default)
  n    Do nothing


Will install Pi.
This will take a while. We're sorry.

  ok npm install complete

Pi was installed successfully.

Run it with: pi
+ C:\Users\byagi\AppData\Roaming\npm\pi.cmd --version
0.84.3

==> Ensuring OpenCode is installed
+ irm https://github.com/anomalyco/opencode/releases/latest/download/opencode-windows-x64-baseline.zip -OutFile C:\Users\byagi\AppData\Local\Temp\fcc-opencode-0034ab4af433411d9fb70c79c43cce7a\opencode-windows-x64-baseline.zip
+ C:\Users\byagi\.opencode\bin\opencode.exe --version
1.18.23

==> Ensuring Cline CLI is installed
+ 'C:\Program Files\nodejs\npm.cmd' install -g cline
npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead

added 328 packages in 3m

46 packages are looking for funding
  run `npm fund` for details
+ C:\Users\byagi\AppData\Roaming\npm\cline.cmd --version
3.0.60

==> Ensuring Hermes Agent is installed
+ irm https://hermes-agent.nousresearch.com/install.ps1 -OutFile C:\Users\byagi\AppData\Local\Temp\fcc-install-68f7e2bbdcbc423d9a50d87add5cac4f.ps1
+ C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\byagi\AppData\Local\Temp\fcc-install-68f7e2bbdcbc423d9a50d87add5cac4f.ps1 -NonInteractive -SkipSetup
[hermes] long profile root: C:\Users\byagi

+---------------------------------------------------------+
|             * Hermes Agent Installer                    |
+---------------------------------------------------------+
|  An open source AI agent by Nous Research.              |
+---------------------------------------------------------+

-> Installing managed uv into C:\Users\byagi\AppData\Local\hermes\bin ...
-> uv installer succeeded via astral.sh
[OK] Managed uv installed (uv 0.12.5 (210d1f678 2026-08-14 x86_64-pc-windows-msvc)) -->


 
==> Checking for running Free Claude Code processes

==> Choosing coding agents
Install or verify Claude Code for fcc-claude? [Y/n]: y
Install or verify Codex for fcc-codex? [Y/n]: u
Please answer Y or N.
Install or verify Codex for fcc-codex? [Y/n]: y
Install or verify Pi for fcc-pi? [Y/n]: y
Install or verify OpenCode for fcc-opencode? [Y/n]: y
Install or verify Cline CLI for fcc-cline? [Y/n]: y
Install or verify Hermes Agent for fcc-hermes? [Y/n]: y
Install or verify DeepSeek Harness for fcc-dsh? [Y/n]: y
Install or verify Grok Build for fcc-grok? [Y/n]: y
Install or verify Muse Code for fcc-muse? [Y/n]: y
Enable RTK token optimization globally for the selected coding agents? [y/N]: y