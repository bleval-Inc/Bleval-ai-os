# Axiom OS — Approval Manager

## Overview

The Approval Manager handles workflow approval checkpoints. It manages the lifecycle of approval requests, pausing workflows until approved or rejected.

## Approval Lifecycle

```
REQUESTED → APPROVED → workflow continues
         → REJECTED → workflow halted
```

## Key Operations

- `request_approval(workflow_instance_id, step_name, requested_by)` — Create approval
- `approve(approval_id, by, notes)` — Approve and continue workflow
- `reject(approval_id, by, notes)` — Reject and halt workflow
- `get_pending_approvals()` — List all pending approvals
- `list_approvals(status)` — List all approvals with optional filter
- `set_workflow_engine(engine)` — Wire to workflow engine

## Integration

When a workflow step requires approval:
1. Workflow status changes to `awaiting_approval`
2. Approval Manager creates an approval request
3. Workflow pauses until `approve()` or `reject()` is called
4. On approval, workflow auto-advances

## API Endpoints
- `GET /api/v1/approvals` — List approvals
- `POST /api/v1/approvals/{id}/respond` — Approve or reject