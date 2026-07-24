# Axiom OS — Monitoring

## Overview

The Health Monitor checks all runtime components periodically and reports their health status. It provides a unified view of system health.

## Health Statuses

| Status | Meaning |
|--------|---------|
| healthy | Component operating normally |
| degraded | Component partially functional |
| unhealthy | Component not functional |

## Components Monitored

All runtime components are health-checked:
- MemoryEngine, EventEngine, ToolEngine, WorkflowEngine
- ExecutiveEngine, IntelligenceEngine, LearningEngine
- Scheduler, Dispatcher, Recovery, Approval

## Key Operations

- `_check_all()` — Check health of all components
- `get_all_health()` — Return health for all components
- `get_component_health(component_name)` — Single component health
- `get_summary()` — Aggregate health summary (total, healthy, unhealthy)
- `is_healthy()` — Boolean: are all components healthy?
- `report_health(component, status, details)` — Report component health
- `start()` — Start background health check loop
- `stop()` — Stop health checking

## API Endpoints
- `GET /api/v1/health` — Health summary of all components