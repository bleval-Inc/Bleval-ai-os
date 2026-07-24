# Axiom OS — Logging

## Overview

The RuntimeLogger provides structured JSON logging to `backend/runtime/logs/`. It is initialized first during bootstrap so all components can use it.

## Log Format

```json
{
  "timestamp": "2026-07-23T16:22:23.871874",
  "level": "INFO",
  "component": "lifecycle",
  "message": "Axiom OS runtime started"
}
```

## Log Levels

- `info` — Normal operational messages
- `error` — Operational errors (workflow failures, task failures)
- `warning` — Degraded conditions

## Usage

```python
self.logger.info("component", "Message here")
self.logger.error("component", "Error: {exc}")
```

## Key Operations

- `RuntimeLogger.info(component, message)` — Info-level log
- `RuntimeLogger.error(component, message)` — Error-level log

## Log Storage

Logs are written to `backend/runtime/logs/` with daily rotation. The log directory is created by `AxiomSettings.ensure_dirs()` during bootstrap.