# Axiom OS — Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude models |
| `OPENAI_API_KEY` | — | OpenAI API key for GPT models |
| `RUFLO_ENV` | `development` | Environment name |
| `AXIOM_STATE_DIR` | `backend/runtime/state` | Workflow state persistence |
| `AXIOM_EVENT_LOG_DIR` | `backend/runtime/events` | Event persistence |
| `AXIOM_LOG_DIR` | `backend/runtime/logs` | Runtime logs |

## AxiomSettings

Configuration is managed by the `AxiomSettings` class in `backend/axiom/config.py`:
- Loads from environment variables via `python-dotenv`
- Provides sensible defaults for all paths
- `ensure_dirs()` creates runtime directories on startup

## Path Resolution

All paths resolve from the project root (parent of `backend/axiom/config.py`):
- Config YAML: `agents/`, `workflows/`, `events/`, `capabilities/`, `organizations/`, `departments/`, `core/`
- Runtime state: `backend/runtime/`
- Memory: `memory/`

## .env File

A `.env` file at the project root is loaded automatically by `python-dotenv` in config.py.