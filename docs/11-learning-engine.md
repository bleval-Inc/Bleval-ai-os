# Axiom OS — Learning Engine

## Overview

The Learning Engine implements continuous learning: Execute → Observe → Measure → Learn → Improve → Repeat. It observes workflow executions, executive decisions, and agent tasks without direct coupling to those systems.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  LearningEngine                   │
├──────────────┬──────────────┬───────────────────┤
│ ScoreTracker │ Pattern      │ Recommendation    │
│              │ Detector     │ Engine            │
├──────────────┴──────────────┴───────────────────┤
│              KnowledgeConsolidator               │
│              (writes to MemoryEngine)            │
└─────────────────────────────────────────────────┘
```

## Scoring

| Entity | Categories | Weighted Formula |
|--------|-----------|-----------------|
| Workflow | speed(25%), quality(30%), reliability(25%), efficiency(20%) | Weighted average |
| Executive | autonomy(30%), quality(40%), reliability(30%) | Weighted average |
| Agent | speed(30%), reliability(70%) | Weighted average |

## Pattern Detection

| Pattern | Threshold | Severity |
|---------|-----------|----------|
| High failure rate | ≥3 runs, success <60% | CRITICAL |
| Slow execution | ≥3 runs, avg >300s | WARNING |
| Declining trend | ≥5 runs, declining trend | WARNING |
| Consistent success | ≥5 runs, 100% success | LEARNING |

## Recommendation Lifecycle

```
DRAFT → PROPOSED → APPROVED → APPLIED
                → REJECTED
```

Auto-consolidation at confidence ≥ 0.85.

## Key API Endpoints
- `GET /api/v1/learning/status`
- `GET /api/v1/learning/scores`
- `GET /api/v1/learning/analytics/workflows`
- `GET /api/v1/learning/patterns`
- `GET /api/v1/learning/recommendations`
- `GET /api/v1/learning/cycles`
- `POST /api/v1/learning/cycle/run`
- `GET /api/v1/learning/knowledge`
- `GET /api/v1/learning/playbook-evolutions`