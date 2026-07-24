# Axiom OS — Workflow Engine

## Overview

The Workflow Engine manages workflow instance creation, step execution, persistence, and state transitions. It interacts with the Dispatcher for task routing and the Event Engine for event emission.

## Key Operations

- `create_instance(workflow_id, context)` — Create a new workflow instance
- `start(instance_id)` — Begin execution
- `advance(instance_id, step_output)` — Complete current step, start next
- `cancel(instance_id)` — Cancel execution
- `get_instance(instance_id)` — Get instance state
- `list_instances(status)` — List instances, optionally filtered
- `list_workflows()` — List all workflow definitions
- `load_all_persisted()` — Recover instances from disk after restart

## State Machine

```
PENDING → RUNNING → AWAITING_APPROVAL → RUNNING → COMPLETED
                      ↓                             ↓
                    FAILED                       CANCELLED
```

## Persistence

Workflow instances are persisted to `backend/runtime/state/{instance_id}.json` after each step. On restart, `load_all_persisted()` recovers running instances.

## Integration

- Receives event → workflow triggers from Event Engine
- Sends tasks to Dispatcher for agent execution
- Requests approvals from Approval Manager
- Emits completion/failure events via Event Engine