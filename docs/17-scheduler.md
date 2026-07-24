# Axiom OS — Scheduler

## Overview

The Scheduler manages cron-based event scheduling. It runs a background polling loop that fires scheduled events at the configured times.

## Key Operations

- `add_schedule(event_type, cron_expression, payload)` — Register a new schedule
- `remove_schedule(event_type)` — Remove a schedule
- `list_schedules()` — List all registered schedules
- `start()` — Start the background cron loop
- `stop()` — Stop the cron loop

## Cron Format

Standard 5-field cron: `minute hour day-of-month month day-of-week`

Example: `*/3600 * * * *` fires every 3600 minutes.

## Background Loop

The scheduler runs as an async background task. Every 60 seconds it checks which schedules need to fire and publishes events via the Event Engine.

## Integration

Schedules are wired during runtime startup (`await scheduler.start()`) and cleaned up during shutdown (`await scheduler.stop()`).

## API Endpoints
- No direct API endpoints — schedules are managed through executive loop schedules