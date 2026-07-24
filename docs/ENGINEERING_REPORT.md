# Axiom OS — Engineering Report

**Date**: 2026-07-24
**Version**: 3.0.0
**Phase**: 7.9 — Repository Purge & Architecture Lock

---

## Repository Structure

### Production Code (after purge)

| Category | Files | Notes |
|----------|-------|-------|
| Python source (`backend/axiom/`) | 37 | 7 engines, 8 runtime subsystems, API, CLI, models, registry |
| Backend root | 7 | `main.py`, `pyproject.toml`, `requirements.txt`, `*-dev.txt` |
| YAML configs — agents | 78 | 3 executives + 15 department agents with detail files |
| YAML configs — workflows | 5 | Workflow index + 4 definitions |
| YAML configs — events | 12 | Event bus, types, schemas, subscriptions |
| YAML configs — capabilities | 11 | Catalog, search index, 9 categories |
| YAML configs — organizations | 13 | 3 orgs (bleval, hov, personal) |
| YAML configs — departments | 34 | 5 bleval depts + 6 hov/personal depts |
| Core configs | 2 | `executives.yml`, `executive_protocol.md` |
| Memory (non-agent) | 27 | Global, org, dept knowledge layers |
| Memory (agent founder reports) | 81 | 3 executives × 27 reports each |
| Docs | 33 | 32 subsystem docs + Production Readiness Report |
| Dashboard (Next.js skeleton) | 19 | Kept for Sprint 4 frontend work |
| CLAUDE.md, README.md, .gitignore | 3 | Root project files |
| Test/audit scripts | 3 | Sprint 1-2 validation + stress tests |
| **Total** | **~365** | |

### Removed During Purge

| Item | Files | Disk | Reason |
|------|-------|------|--------|
| `ruflo/` | 253 | 3.6 MB | Claude Flow tooling, not part of Axiom OS |
| `backend/runtime/` | ~839 | ~5 MB | Generated runtime artifacts (recreated on boot) |
| `.claude-flow/` | 12 | 64 KB | Claude Flow runtime state |
| `executives/` | 19 | ~50 KB | Duplicate of `agents/` + `core/executives.yml` |
| `dashboard/` | — | — | **Kept** for Sprint 4 (decision override) |
| `.swarm/` | 1 | 4 KB | Swarm model-router state |
| `Tools/` | 4 | ~10 KB | PowerShell launcher scripts |
| `test-install/` | 1 | ~1 KB | Stale pinned requirements |
| `ruvector.db` | 1 | 384 KB | Vector database artifact |
| `config/` | 0 | 0 | Empty directory |
| `integrations/` | 0 | 0 | Empty directory |
| `__pycache__/` | 8 dirs | variable | Python bytecode caches |
| `.venv/` | 3 dirs | variable | Virtual environments |
| `.mcp.json` | 1 | ~1 KB | MCP configuration |
| **Total removed** | **~1,142 items** | **~9 MB** | |

**Net reduction**: ~1,100 files, ~9 MB disk reclaimed.

---

## Packaging Changes

| Before | After |
|--------|-------|
| `requirements.txt` — full dep list (9 deps) | `requirements.txt` → `-e .` (references `pyproject.toml`) |
| `requirements-dev.txt` — full dep list | `requirements-dev.txt` → `-e .[dev]` |
| `test-install/requirements.txt` | Deleted (stale) |
| `pyproject.toml testpaths = ["tests"]` | `testpaths = ["backend"]` (no `tests/` dir exists) |

**`pyproject.toml`** is now the single source of truth for dependencies.

---

## Code Cleanup

### Dead Imports Removed (11 occurrences, 6 files)

| File | Removed |
|------|---------|
| `axiom/engine/memory.py` | `MemoryAccessConfig` |
| `axiom/engine/executive.py` | `ApprovalRequest`, `WorkflowInstance`, `WorkflowStatus`, `datetime`, `timezone` |
| `axiom/engine/tool.py` | `AgentDetail`, `ToolRegistry`, `Optional` |
| `axiom/engine/event.py` | `Path` |
| `axiom/runtime/approval.py` | `datetime`, `timezone` |
| `axiom/runtime/recovery.py` | `datetime`, `timezone`, `Optional`, `StepStatus` |

### Naming Standardized

`organisation` → `organization` in docstrings and comments across 8 source files. API endpoint paths (`/organisations`) **unchanged** to preserve backward compatibility.

---

## Architecture Freeze (Reaffirmed)

The backend architecture is frozen as of Sprint 3. No changes permitted without formal review:

1. **No new engines** — Extend existing engines through configuration
2. **No new runtime subsystems** — Use event-driven patterns for new capabilities
3. **Don't break the API** — Backward-compatible additions only
4. **Document first** — Update `docs/` before implementation
5. **Run validation** — All checks must pass before merge

---

## Remaining Technical Debt

| Item | Severity | Notes |
|------|----------|-------|
| No authentication/authorization on API | **Medium** | Must be added before public deployment |
| API uses `organisation` (British spelling) in route paths | Low | Standardize in Sprint 4 API review |
| Outstanding `_wf_engine` dead attribute in `approval.py:80` | Low | Assigned but never read (setter injected, not used) |
| Empty `_on_workflow_started` handler in `lifecycle.py:349` | Low | Placeholder for future behavior |
| No test coverage in `tests/` directory | Low | Validation scripts serve as regression suite |
| `dashboard/` is a bare Next.js skeleton | Low | No node_modules, no build step |
| File-based state at scale | Low | Works for single-instance; needs DB for horizontal scaling |
| Agent list gap (5 user-named agents not in registry) | Low | Address in feature sprint if needed |

---

*Phase 7.9 complete. Repository purged. Architecture locked. Ready for Sprint 4 (frontend).*