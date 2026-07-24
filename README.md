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