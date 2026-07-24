# Axiom OS — Recovery

## Overview

The Recovery Manager handles failure recovery for workflow instances. It provides retry handling for failed steps and workflow recovery after system restarts.

## Key Operations

- `get_max_retries()` — Get the current max retry setting
- `set_max_retries(count)` — Configure max retries
- `recover_after_restart()` — Recover all persisted instances after a restart
- `recover_all_failed()` — Retry all failed workflow instances

## Restart Recovery

On system restart, `recover_after_restart()`:
1. Loads all persisted workflow state from disk
2. Identifies instances that were RUNNING at crash time
3. Re-queues their current step for execution
4. Finalizes any instances that were already COMPLETED/FAILED

## Failed Step Recovery

When a workflow step fails, the Recovery Manager:
1. Increments retry counter
2. Applies exponential backoff
3. Re-dispatches the task
4. If max retries exceeded, marks workflow as FAILED

## Configuration

- Default max retries: 3
- Configurable via `set_max_retries()`
- Persisted to `backend/runtime/state/`