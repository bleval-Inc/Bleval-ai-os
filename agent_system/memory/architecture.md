# Bleval AI OS — System Architecture

**Version:** 3.0.0

## Core Principles

1. **Event-driven orchestration** — All workflows, executive cycles, and agent tasks are driven by events
2. **Layered memory** — Global → Organization → Department → Agent (knowledge flows down, learning flows up)
3. **Autonomous executives** — Jenson (bleval), Valta Prime (hov), Yamako (personal) run independent runtime loops
4. **Continuous learning** — Every execution produces scores, patterns, recommendations, and knowledge

## Component Architecture

- **AxiomRuntime** — Central orchestrator (lifecycle.py)
- **7 Engines** — Memory, Event, Tool, Workflow, Executive, Intelligence, Learning
- **7 Subsystems** — Scheduler, Dispatcher, Monitor, Recovery, Approval, ExecutiveBoard, Logger
- **4-layer Memory** — File-based, YAML-indexed, Markdown-stored
- **3 Executives** — 14+ agents, 5 departments, 10+ workflows, 20 event types, 46 capabilities