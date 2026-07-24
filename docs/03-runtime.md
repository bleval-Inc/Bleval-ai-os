# Axiom OS — Runtime

## AxiomRuntime

The central orchestrator. Manages initialization, background processors, and graceful shutdown.

## Lifecycle

```
bootstrap() → start() → running... → shutdown()
```

### bootstrap()
Initializes in strict order:
1. Logger
2. MemoryEngine, ToolEngine, ExecutiveEngine
3. IntelligenceEngine (depends on memory + tool)
4. EventEngine (created before WorkflowEngine)
5. WorkflowEngine (needs event ref)
6. Scheduler, Dispatcher, Monitor, Recovery, Approval
7. Wire cross-references (workflow ↔ dispatcher, approval ↔ workflow)
8. ExecutiveBoard
9. LearningEngine

### start()
After bootstrap, starts background processors:
1. EventEngine.start() — background pub/sub
2. Event → workflow auto-launch subscriptions
3. Scheduler.start() — cron loop
4. Dispatcher.start() — task processing
5. _wire_learning_engine() — event subscriptions + monkey patches
6. LearningEngine.start() — consolidation loop
7. Monitor.start() — health checks
8. Load persisted workflow state from disk
9. ExecutiveBoard.start_all() — autonomous executive loops

### shutdown()
Reverse order — stops executive loops first, then:
1. Monitor → Learning → Scheduler → Dispatcher → Event