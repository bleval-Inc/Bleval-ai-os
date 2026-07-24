# Axiom OS — Dispatcher

## Overview

The Dispatcher manages the task queue and agent routing. It receives tasks from the Workflow Engine, routes them to the appropriate agent handler, and auto-advances workflows on completion.

## Task Lifecycle

```
QUEUED → DISPATCHED → IN_PROGRESS → COMPLETED
                  ↓                   ↓
                FAILED              CANCELLED
```

## Retry Logic

When a handler raises an exception:
1. Task status set to FAILED
2. If `retry_count < max_retries` (default 3): increment retry, re-queue with exponential backoff (`2^retry_seconds` delay)
3. If max retries exceeded: task remains FAILED

## Key Operations

- `register_handler(agent_id, handler)` — Register an async handler for an agent
- `dispatch(agent_id, action, workflow_instance_id)` — Create and enqueue a task
- `get_task(task_id)` — Get task by ID
- `list_tasks(status, agent_id)` — List tasks with optional filters
- `cancel_task(task_id)` — Cancel a queued task
- `start()` — Start background queue processor
- `stop()` — Stop background processor

## Auto-Advance

On task completion, the Dispatcher automatically calls `workflow.advance()` to progress the parent workflow instance to the next step.

## Background Processor

An async task runs continuously, reading from `asyncio.Queue` and executing tasks through registered handlers. Timeout: 1 second queue wait between polls.

## API Endpoints
- No direct API endpoints — dispatcher operates internally