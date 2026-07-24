# Axiom OS — Registry

## Overview

The Registry system loads all YAML configuration files from disk and validates them against Pydantic models. Each registry handles a specific config domain.

## Registry Loaders

| Loader | File | Purpose |
|--------|------|---------|
| AgentRegistryLoader | `agents/agent-registry.yaml` | Agent definitions + detail files |
| WorkflowRegistryLoader | `workflows/workflow-index.yaml` | Workflow definitions |
| EventRegistryLoader | `events/event-bus.yaml` | Event types + subscriptions |
| CapabilityRegistryLoader | `capabilities/capability-catalog.yaml` | Capability definitions |
| DepartmentRegistryLoader | `departments/departments.yaml` | Department definitions |
| OrganizationRegistryLoader | `organizations/organization.yaml` | Organization definitions |

## YAMLLoader

The core utility class (`backend/axiom/registry/loader.py`) provides:
- `load_yaml(path)` — Parse YAML files with error handling
- `load_markdown(path)` — Read Markdown files as text
- Returns None on missing files instead of raising

## Validation

All YAML files are validated against Pydantic models in `backend/axiom/models/configs.py`. Invalid files produce clear error messages during bootstrap.

## Config Paths

All paths resolved through `backend/axiom/config.py` helpers: `agents_path()`, `workflows_path()`, `events_path()`, `capabilities_path()`, `departments_path()`, `organizations_path()`, `memory_path()`, `core_path()`.