# Axiom OS — Executive Engine

## Overview

The Executive Engine manages executive agent coordination, agent discovery, department management, and task delegation.

## Key Operations

- `list_executives()` — Return all executive definitions
- `list_all_agents()` — Return all agents across all organizations
- `get_agent_detail(agent_id)` — Full agent definition with capabilities
- `list_capabilities()` — Return all registered capabilities
- `search_capabilities(query)` — Search capabilities by keyword
- `get_departments(org_id)` — List departments for an organization
- `get_organization_detail(org_id)` — Full organization definition

## Executive Details

Each executive has:
- Unique ID (jenson, valta_prime, yamako)
- Organization assignment
- Department oversight
- Capabilities for strategic work

## Agent Discovery

Agents are discovered by scanning the `agents/` directory tree. Each agent YAML registers the agent, and detail files (identity, instructions, memory, permissions) provide operational context.