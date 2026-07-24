# Axiom OS — Platform Philosophy

## Core Principles

1. **Event-driven orchestration** — All workflows, executive cycles, and agent tasks are driven by events. Events are the primary communication mechanism between subsystems.
2. **Layered memory** — Knowledge flows downward (Global → Organization → Department → Agent). Learning flows upward (Agent → Department → Organization).
3. **Autonomous executives** — Jenson (bleval), Valta Prime (hov), Yamako (personal) each run independent runtime loops with their own schedules, priorities, and workflows.
4. **Continuous learning** — Every execution produces scores, patterns, recommendations, and knowledge. The Learning Engine observes without direct coupling.
5. **Separation of concerns** — Engines handle capabilities, runtime subsystems handle operations. No engine calls another engine's private methods.

## Architecture Laws (from Law 10)

- Learning is separate from memory. Learning updates memory through controlled interfaces.
- Only executives approve permanent changes to memory.
- Agents operate within department boundaries defined in YAML configs.
- Capabilities resolve to agents — never the reverse.
- Runtime must survive component failures with automatic recovery.

## Design Constraints

- No UI in the backend. All interfaces are REST API + CLI.
- All configuration is file-based (YAML + Markdown). No database required.
- Mock-first intelligence — the system runs fully without external AI providers.