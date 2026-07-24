# Axiom OS — Failure Recovery

## Overview

The system handles failures at multiple levels: task retry, workflow recovery, and system restart recovery.

## Failure Modes

| Level | Failure | Recovery |
|-------|---------|----------|
| Task | Handler raises exception | Exponential backoff retry (up to 3x) |
| Workflow | Step execution fails | Retry step, then mark workflow FAILED |
| Approval | Workflow paused | Resume on approve/reject |
| System | Process crash | Persisted state reload on restart |
| Component | Engine failure | Health Monitor detects, Recovery handles |

## Task Retry

When a task handler fails:
1. Task status: FAILED
2. If `retry_count < max_retries`: increment, sleep `2^retry` seconds, re-queue
3. If max retries exceeded: task stays FAILED

## Workflow Recovery

- Failed workflows remain in FAILED status
- `recover_all_failed()` retries all failed instances
- Failed steps are re-dispatched with retry counter reset

## Restart Recovery

On `recover_after_restart()`:
1. Scan `backend/runtime/state/` for persisted instance files
2. Load each instance's state
3. Re-queue incomplete steps
4. Finalize completed/failed instances

## Health Monitor

The Health Monitor periodically checks all components. Unhealthy components are reported via `get_summary()`. The `is_healthy()` check returns False if any component is unhealthy.