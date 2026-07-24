# Axiom OS — Memory Engine

## Overview

The Memory Engine provides layered, file-based memory retrieval and persistence. Architecture: Global → Organization → Department → Agent.

## Memory Layers

| Layer | Access | Flow |
|-------|--------|------|
| Global | read_only | Downward to organizations |
| Organization | org_executives_read_write | Downward to departments, upward to global |
| Department | dept_agents_read_write | Downward to agents, upward to organization |
| Agent | agent_owner_read_write | Upward to department learnings |

## Index

Memory structure defined in `memory/memory-index.yaml`:
- Layer definitions with file lists and path locations
- Access control rules
- Flow direction rules

## Key Operations

- `load_global_memory()` — Returns `{filename: content}` dict
- `load_org_memory(org_id)` — Organization-level files
- `load_department_memory(org_id, dept_id)` — Department-level files
- `load_agent_memory(agent_id)` — Agent-level files
- `get_resolved_context(agent_id, org_id, dept_id)` — Merged layers (agent highest priority)
- `get_context_string(agent_id, org_id, dept_id)` — Formatted string for prompts
- `write_agent_memory(agent_id, key, content)` — Write at agent layer

## Resolution Priority

Agent (highest) → Department → Organization → Global (lowest)

## Storage

All memory is stored as Markdown (`.md`) files on disk. The memory root is `memory/` at the project root.