# Axiom OS — Workflows

## Overview

Workflows are multi-step processes executed by the WorkflowEngine. Each workflow has a trigger event or manual launch, a series of steps, and completion/failure states.

## Lifecycle

```
PENDING → RUNNING → [AWAITING_APPROVAL] → COMPLETED
                        ↓                    ↓
                     FAILED               CANCELLED
```

## Workflow Definitions

| ID | Department | Steps | Description |
|----|-----------|-------|-------------|
| sales/prospect-research | sales | 2 | Research sales prospects |
| sales/outreach-campaign | sales | 3 | Execute outreach campaigns |
| marketing/content-production | marketing | 2 | Create and publish content |
| development/feature-development | development | 3 | Develop new features |

## Workflow Steps

Each step has:
- **agent_id**: The agent that executes the step
- **action**: What the agent should do
- **config**: Optional parameters (timeout, retry, approvals)

## Key API Endpoints
- `GET /api/v1/workflows` — List all workflow definitions
- `GET /api/v1/workflows/{id}` — Get workflow detail
- `POST /api/v1/workflows/launch` — Create and start instance
- `GET /api/v1/instances` — List instances
- `GET /api/v1/instances/{id}` — Get instance detail
- `POST /api/v1/instances/{id}/advance` — Advance to next step
- `POST /api/v1/instances/{id}/cancel` — Cancel instance