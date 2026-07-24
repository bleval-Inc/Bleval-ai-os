# Axiom OS — Architecture

## System Overview

Axiom OS is a multi-agent orchestration platform. It coordinates executives, departments, workflows, and agents across organizations through an event-driven runtime.

## Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                    AxiomRuntime                      │
├──────────────┬──────────────────┬───────────────────┤
│  7 Engines   │  7 Subsystems    │   Config Layer    │
│              │                  │                   │
│  Memory      │  Scheduler       │  YAML Loader      │
│  Event       │  Dispatcher      │  Path Resolver    │
│  Tool        │  Monitor         │  Env Vars         │
│  Workflow    │  Recovery        │                   │
│  Executive   │  Approval        │                   │
│  Intelligence│  ExecutiveBoard  │                   │
│  Learning    │  Logger          │                   │
└──────────────┴──────────────────┴───────────────────┘
         ▲              │
         │    Events    ▼
         └──────────────┘
```

## Data Flow

1. Configuration loads from YAML files → Registry Loaders
2. Runtime bootstraps all engines in dependency order
3. Event Engine starts first — enables pub/sub
4. Workflows execute steps → Dispatcher routes tasks
5. Completion events → Learning Engine scores and learns
6. Health Monitor checks all components periodically

## Key Design Decisions

- **File-based state**: Runtime state persisted to `backend/runtime/state/`
- **Async-first**: All I/O is async (asyncio). Background processors use event loops.
- **Monkey-patch instrumentation**: Learning Engine observes via wrapped methods — no direct coupling.