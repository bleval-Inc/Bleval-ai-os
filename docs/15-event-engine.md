# Axiom OS — Event Engine

## Overview

The Event Engine is the messaging backbone. It provides async publish-subscribe with channel-based queues, payload validation, retry with exponential backoff, dead-letter queue, file-based persistence, and replay.

## Event Types

20 registered event types across categories:

| Category | Event Types |
|----------|------------|
| Lead | lead-discovered, lead-qualified, lead-lost |
| Opportunity | opportunity-created, opportunity-won, opportunity-lost |
| Workflow | workflow-started, workflow-completed, workflow-failed, workflow-cancelled |
| Task | task-assigned, task-completed, task-failed |
| Executive | executive-cycle-started, executive-cycle-completed |
| System | system-boot, system-shutdown, system-error, system-health-change |
| Memory | memory-updated |

## Architecture

- **Channels**: Events are organized into channels (organization, department, executive)
- **Subscriptions**: Multiple subscribers can listen to the same event type
- **Retry**: Exponential backoff on handler failures (up to 3 retries)
- **DLQ**: Failed events go to a dead-letter queue (10,000 cap)
- **Persistence**: Events written to `backend/runtime/events/` for replay
- **Replay**: Full event replay from persisted logs

## Key Operations

- `publish(event_type, source, payload)` — Fire an event
- `subscribe_to_event(event_type, callback)` — Register a handler
- `get_event_log(event_type, limit)` — Retrieve event history
- `replay_events(event_type)` — Replay all events of a type
- `list_event_types()` — List registered event types
- `list_event_channels()` — List registered channels

## API Endpoints
- `GET /api/v1/events/types` — List event types
- `POST /api/v1/events/publish` — Publish an event