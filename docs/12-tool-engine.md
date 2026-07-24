# Axiom OS — Tool Engine

## Overview

The Tool Engine handles permission checking, capability resolution, and audit logging. It discovers tools per organization and resolves capabilities to agents.

## Key Operations

- `resolve_capability_to_agents(cap_id)` — Returns list of agents with a capability
- `discover_tools(org_id)` — Returns tool definitions for an organization
- `check_permission(agent_id, action)` — Validates can/cannot rules
- `log_usage(agent_id, tool, duration)` — Audit trail for tool usage

## Capability Resolution

Capabilities are defined in `capabilities/capability-catalog.yaml` with:
- Capability ID and category
- Required skill level
- Associated agents
- Related workflows

## API Endpoints
- `GET /api/v1/capabilities` — List capabilities (with optional search)
- `GET /api/v1/capabilities/{id}` — Get capability detail