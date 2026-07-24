# Axiom OS — Extension Points

## Overview

The platform is designed to be extended through YAML configuration and Python registration. No core code changes needed for most extensions.

## Adding a New Agent

1. Create agent YAML in `agents/{org}/{dept}/{role}/agent.yml`
2. Register in `agents/agent-registry.yaml`
3. Add detail files: `identity.md`, `instructions.md`, `memory.md`, `permissions.md`
4. Assign capabilities in `capabilities/capability-catalog.yaml`
5. Register handler in dispatcher if agent needs custom task processing

## Adding a New Workflow

1. Create workflow YAML in `workflows/{dept}/{name}.yaml`
2. Register in `workflows/workflow-index.yaml`
3. Assign steps with agent+action pairs
4. Optionally configure trigger events and approval steps

## Adding a New Event Type

1. Add event type definition in `events/event-types.yaml`
2. Add schema in `events/schemas/`
3. Optionally add subscriptions in `events/subscriptions/`

## Adding a New Capability

1. Add to `capabilities/capability-catalog.yaml`
2. Assign to agents
3. Optionally create category file in `capabilities/categories/`

## Adding a New Department

1. Create department directory in `departments/{org_id}/{dept}/`
2. Create `department.yaml` with manager, agents, workflows
3. Add mission, metrics, playbook, processes files

## Adding a New Organization

1. Create organization directory in `organizations/{org_id}/`
2. Create `organization.yaml` with executive, departments, boundaries
3. Add memory layer in `memory/{org_id}/`