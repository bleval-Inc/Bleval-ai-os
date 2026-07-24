# Bleval AI OS — Global Architecture

## System Overview
The Bleval AI OS is a modular, layered platform for operating autonomous AI-driven organizations.
It separates business architecture (owned by Bleval AI OS) from AI runtime execution (currently Ruflo).

## Architectural Layers
1. **Executive Board** — C-suite AI executives managing organizations
2. **Organization Layer** — Organizational boundaries, identity, and permissions
3. **Department Layer** — Department structure, SOPs, KPIs, and playbooks
4. **Agent Layer** — Individual AI agents with capabilities and memory
5. **Workflow/Event Layer** — Event-driven workflow coordination
6. **Memory/Knowledge Layer** — Layered memory hierarchy
7. **Tool Integration Layer** — Abstracted tool interfaces owned by organizations
8. **AI Runtime** — Replaceable execution engine (currently Ruflo)

## Core Principles
- Runtime agnosticism: Never couple business architecture to execution engine
- Unlimited organizations: New orgs installable without platform changes
- Configuration over hardcoding: Everything discoverable via registries
- Capability-based assignment: Work routes to capabilities, not agent names
- Event-driven coordination: Agents react to events, not polling