# Axiom OS — Deployment

## Requirements

- **Python**: 3.8+ (tested on Python 3.8, 3.11)
- **Dependencies**: See `backend/requirements.txt` and `backend/requirements-dev.txt`
- **No database required** — all state is file-based

## Production Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000

# With auto-reload (development)
uvicorn main:app --reload --port 8000
```

## Health Check

```bash
# Root endpoint
curl http://localhost:8000/

# Status
curl http://localhost:8000/api/v1/status

# Health
curl http://localhost:8000/api/v1/health
```

## Mock Mode

If no `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set, the Intelligence Engine falls back to MockProvider, returning canned responses. The full system operates without external AI providers.

## Runtime Directories

Created automatically by `AxiomSettings.ensure_dirs()`:
- `backend/runtime/state/` — Workflow instance persistence
- `backend/runtime/events/` — Event log persistence
- `backend/runtime/logs/` — Runtime logs