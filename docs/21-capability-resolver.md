# Axiom OS — Capability Resolver

## Overview

The Capability Resolver maps capabilities to agents. It provides capability discovery, search, and agent resolution.

## Capability Model

Each capability has:
- **id**: Unique identifier (kebab-case)
- **category**: Functional grouping
- **name**: Human-readable name
- **description**: Purpose and usage
- **level**: Skill level (beginner, intermediate, advanced)
- **agents**: List of agents that possess this capability
- **workflows**: Related workflows

## Categories

46 capabilities across categories: analysis, outreach, closing, research, content, development, coordination, operations, reporting, compliance, testing

## Resolution Logic

`resolve_capability_to_agents(cap_id)` returns all agents registered for a capability. Resolution is direct (YAML-defined), not computed.

## Search

`search_capabilities(query)` performs keyword matching against capability names and descriptions.

## Key Operations

- `resolve_capability_to_agents(cap_id)` — Get agents for capability
- `search_capabilities(query)` — Keyword search
- `list_capabilities()` — All capabilities
- `get_capability(cap_id)` — Single capability detail

## API Endpoints
- `GET /api/v1/capabilities` — List/search capabilities
- `GET /api/v1/capabilities/{id}` — Capability detail