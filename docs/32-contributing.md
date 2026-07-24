# Axiom OS — Contributing

## Development Setup

```bash
# Clone the repository
git clone <repo-url> cd bleval-ai-os

# Set up Python virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file (if exists)
cp .env.example .env

# Start the server
uvicorn main:app --reload --port 8000
```

## Verification

```bash
# Run validation suite
python3 _sprint2_validation.py

# Run stress tests
python3 _sprint2_stress_tests.py

# Run Sprint 1 audit
python3 _sprint1_audit.py
```

## Contribution Workflow

1. Branch from `main`
2. Make changes
3. Run all tests
4. Update documentation if API or behavior changed
5. Submit PR

## Architecture Rules

- Do not add engines without Executive Board approval
- Do not add new runtime subsystems without review
- All config must be YAML + Markdown file-based
- Engines communicate through events, not direct calls
- Learning is observation-only — no direct component coupling
- Keep files under 500 lines
- Add type annotations to all public methods

## Documentation

When adding new features, update:
- `docs/` — Specification documentation
- README.md — Quick start and project overview
- API routes file if new endpoints added