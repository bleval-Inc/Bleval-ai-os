# Axiom OS — Coding Standards

## Python

- **Python 3.8+** compatible (no walrus operator, no match statements)
- **Async-first**: All I/O uses asyncio
- **Pydantic v2**: All data models are Pydantic BaseModels
- **Type annotations**: All public methods have type hints
- **Docstrings**: All public methods have docstrings (triple-quote format)
- **Line limit**: Keep files under 500 lines

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | AxiomRuntime, MemoryEngine |
| Methods/functions | snake_case | get_status(), list_workflows() |
| Variables | snake_case | instance_id, org_id |
| Constants | UPPER_SNAKE | REPO_ROOT, EXECUTIVE_IDS |
| Modules | snake_case | lifecycle.py, dispatcher.py |
| YAML IDs | kebab-case or snake_case | lead-discovered, valta_prime |
| API endpoints | lowercase with hyphens | /api/v1/learning/patterns |

## Model Patterns

- All models in `backend/axiom/models/` as Pydantic BaseModels
- Enums use Python's Enum with string values
- Optional fields typed as `Optional[Type]` with default `None`

## Error Handling

- Validate input at system boundaries (API layer)
- Engines raise ValueError for invalid operations
- Recovery Manager handles retries, not individual components
- All async routes catch exceptions and return 400/503