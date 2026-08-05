# AXIOM OS SPECIFICATION
**Version 3.0.0** — The authoritative system reference for the AXIOM AI Operating System.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Runtime](#2-runtime)
3. [AXIOM Core](#3-axiom-core)
4. [Executive Model](#4-executive-model)
5. [Organizations](#5-organizations)
6. [Workstations](#6-workstations)
7. [Agents](#7-agents)
8. [Workflows](#8-workflows)
9. [Memory](#9-memory)
10. [Events](#10-events)
11. [Tools](#11-tools)
12. [Permissions](#12-permissions)
13. [Authority](#13-authority)
14. [Quality Control](#14-quality-control)
15. [Learning](#15-learning)
16. [Voice](#16-voice)
17. [Board Room](#17-board-room)
18. [Mobile](#18-mobile)
19. [Integrations](#19-integrations)
20. [Deployment](#20-deployment)
21. [Recovery](#21-recovery)
22. [Security](#22-security)
23. [Maintenance](#23-maintenance)
24. [Extension Guidelines](#24-extension-guidelines)

---

## 1. Architecture Overview

### 1.1 Philosophy

AXIOM OS is an **AI Operating System** — not an AI platform, not a chatbot, not an automation tool. It is an intelligent operating environment that manages autonomous executives, departments, workflows, agents, memory, tools, and intelligence across multiple organizations.

**Core Principle**: The Founder focuses on judgment, strategy, and execution. AXIOM handles the operational complexity underneath.

### 1.2 Layered Architecture

```
┌─────────────────────────────────────┐
│           FOUNDER                    │
│    (Judgment • Strategy • Execution) │
└────────────────────┬────────────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│           AXIOM CORE                 │
│  (System Concierge • Intelligence •  │
│   Health Supervisor • Request Router │
│   Research Workspace • Greeting)     │
└────────────────────┬────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│   JENSON     │ │VALTA PR. │ │ YAMAKO  │
│  (Bleval)    │ │  (HoV)   │ │(Personal)│
│  Executive   │ │ Executive│ │ Executive│
└──────┬───────┘ └────┬─────┘ └────┬─────┘
       │              │            │
       ▼              ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│ Departments  │ │Depts     │ │ Depts    │
│ • Sales      │ │• Brand   │ │• Product.│
│ • Marketing  │ │• Creative│ │• Knowl.  │
│ • Development│ │• Research│ │          │
│ • Operations │ │• Content │ │          │
│ • Finance    │ │• Growth  │ │          │
│              │ │• Ops     │ │          │
└──────┬───────┘ └────┬─────┘ └────┬─────┘
       │              │            │
       ▼              ▼            ▼
┌─────────────────────────────────────┐
│          WORKFLOWS                   │
│  (Coordinate agents → executors)     │
└────────────────────┬────────────────┘
                     │
                     ▼
┌─────────────────────────────────────┐
│           AGENTS                     │
│  (Specialist agents with tools)      │
└────────────────────┬────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ MEMORY  │  │ EVENTS  │  │  TOOLS  │
   │(Layered)│  │ (Bus)   │  │(Integr.)│
   └─────────┘  └─────────┘  └─────────┘
```

### 1.3 Key Invariants

1. **Executives NEVER perform work directly** — they only coordinate through workflows
2. **AXIOM sits ABOVE executives** — it is the system concierge, not an executive
3. **Founder retains final authority** over 10 restricted action categories
4. **All work is QC-checked** — bad work is reworked, not escalated to Founder
5. **Memory is layered** — global, org, dept, agent with defined access rules
6. **Everything is auditable** — every decision, approval, and action is recorded

---

## 2. Runtime

### 2.1 AxiomRuntime

The central orchestrator (`backend/axiom/runtime/lifecycle.py:AxiomRuntime`) that initializes all engines and subsystems in dependency order:

**Boot Phases:**
1. **Phase 0**: Logger initialization
2. **Phase A**: Core Engines (Memory → Tool → Executive → Intelligence)
3. **Phase B**: Executive Layer (Board Room, Communication, Executive Board)
4. **Phase C**: Autonomous Workflow + Agent System (Specialist Engine, Autonomous Workflow, Multi-Model, Background Executor, Observer)
5. **Phase D**: Quality Control + Founder Authority (QC Manager, Founder Authority, Founder Gateway, QC Handler)
6. **Phase E**: Executive Intelligence + QC Learning (Executive Intelligence, Executive Greeter, QC→Learning Pipeline)
6. **Phase H**: Platform Integrations (Provider Registry, 8 providers)

**Startup Sequence:**
```python
runtime = AxiomRuntime()
await runtime.bootstrap()  # Initialize all components
await runtime.start()      # Start background processors
```

**Shutdown Sequence:** Reverse order with graceful cleanup.

### 2.2 Component Registry

All engines and subsystems are accessible as properties:
- `runtime.memory` — MemoryEngine
- `runtime.event` — EventEngine
- `runtime.tool` — ToolEngine
- `runtime.workflow` — WorkflowEngine
- `runtime.executive` — ExecutiveEngine
- `runtime.intelligence` — IntelligenceEngine
- `runtime.learning` — LearningEngine
- `runtime.executive_board` — ExecutiveBoard
- `runtime.board_room` — BoardRoom
- `runtime.axiom` — AXIOMCore
- `runtime.qc_manager` — QCManager
- `runtime.founder_authority` — FounderAuthority
- `runtime.founder_gateway` — FounderGateway
- `runtime.provider_registry` — ProviderRegistry
- `runtime.system_monitor` — SystemMonitor
- `runtime.greeting_engine` — GreetingEngine
- `runtime.system_tools` — SystemTools

---

## 3. AXIOM Core

### 3.1 Role

AXIOM Core (`backend/axiom/core/axiom_core.py:AXIOMCore`) is the **top-level intelligence layer** — the JARVIS of the operating system. It sits above all executives and provides:

- **System Awareness**: Live operational model of entire system
- **Conversational Interface**: Founder chat with full system context
- **Request Routing**: Classifies and routes Founder requests
- **Research Workspace Management**: Multi-modal content retrieval
- **Self-Healing Coordination**: Monitors health, triggers recovery
- **Greeting**: Context-aware boot messages with telemetry

### 3.2 System Awareness

`AXIOMCore.get_system_awareness()` returns a `SystemAwareness` object with:
- Overall state (ONLINE, DEGRADED, FAILED, SHUTDOWN)
- Health score (0.0–1.0) with label
- Uptime and boot ID
- Executive statuses (cycle count, health, org)
- Engine health (7 engines monitored)
- Workflow summary (defined, active, pending, failed, awaiting approval)
- Intelligence availability
- Pending approval count

### 3.3 Request Routing

Uses `RequestRouter` to classify Founder messages:
- **system_status** → answered from awareness directly
- **information** → AXIOM capabilities overview
- **executive** → routed to specific executive via ExecutiveBoard
- **research** → initiates research workspace
- **navigation** → routes to dashboard panels

### 3.4 Research Workspaces

Structured workspaces with:
- Conversation history (queries + responses)
- Sources (documents, URLs, references)
- Findings (key insights)
- Notes (Founder annotations)
- Conclusions (synthesis)
- Generated assets (reports, summaries)
- Multi-modal content (documents, images, videos, audio)

### 3.5 Monitoring & Self-Healing

Background loop (30s interval) checks:
- Executive health and cycle completion
- Workflow engine status
- Event bus health
- Memory integrity
- Intelligence provider availability
- System resource usage

Failures trigger `SelfHealer` for automated recovery.

---

## 4. Executive Model

### 4.1 Executive Runtime Loop

Each executive runs an independent `ExecutiveRuntimeLoop` (`backend/axiom/runtime/executive_loop.py`) with the cycle:

```
Morning Review → Check KPIs → Review Memory → Identify Priorities
    ↓
Launch Workflows → Review Results → Report Founder
```

**Cycle Phases:**
1. **Inspect Organization** — departments, agents, capabilities
2. **Inspect Memory** — resolved context for executive
3. **Inspect Active Workflows** — running instances for org
4. **Review Completed Work** — last 5 completed instances
5. **Decide Priorities** — via Intelligence Engine or defaults
4. **Launch Priority Workflows** — top 3 matching workflows
5. **Report** — format cycle report, log to memory
6. **Record Decision** — store in executive memory
7. **Report to Founder** — for daily/official cycles
7. **Publish KPIs** — to Board Room

### 4.2 Three Executives

| Executive | Organization | Role | Departments | Special Capabilities |
|-----------|-------------|------|-------------|---------------------|
| **Jenson** | Bleval Inc | CEO | Sales, Marketing, Development, Operations, Finance | Autonomous development lifecycle, GitHub integration |
| **Valta Prime** | House of Valta | CEO | Brand, Creative, Research, Content, Growth, Operations | POI Monitor (GOLD/US30), market alerts |
| **Yamako** | Personal Operations | Chief of Staff | Productivity, Knowledge | Schedule Coordinator, Morning Routine Manager |

### 4.3 Executive Schedules (Phase I Cadence)

**Jenson**: Tuesday 9am + Friday 9am Founder meetings
- `founder_meeting_tue`: `0 9 * * 1`
- `founder_meeting_fri`: `0 9 * * 4`

**Valta Prime**: Friday 8am + Sunday 8am Market meetings
- `market_meeting_fri`: `0 8 * * 4`
- `market_meeting_sun`: `0 8 * * 6`

**Yamako**: Sunday 9am Weekly Planning + Friday 6pm Personal Review
- `weekly_planning`: `0 9 * * 0`
- `personal_review`: `0 18 * * 5`

All executives also run:
- `morning_review`: Weekdays 8am
- `midday_check`: Weekdays 12pm (except Valta Prime continuous POI monitoring)
- `afternoon_review`: Weekdays 4pm

### 4.4 Executive Communication

- **Board Room**: Asynchronous structured meetings (daily, weekly, monthly)
- **Communication Coordinator**: Real-time inter-executive messaging with urgency levels
- **Direct Founder messaging**: Via AXIOM Core `route_to_executive()`

### 4.5 Executive Intelligence

`ExecutiveIntelligence` (`backend/axiom/engine/executive_intelligence.py`) provides:
- **Pattern Learning**: Learns from workflow outcomes, executive decisions, QC results
- **Decision Support**: Prioritizes work based on historical success patterns
- **Health Assessment**: Computes executive health scores from cycle data
- **Greeting Generation**: Context-aware executive greetings via `ExecutiveGreeter`

---

## 5. Organizations

### 5.1 Organization Registry

Defined in `organizations/organization.yaml` with three active organizations:

```yaml
organizations:
  - id: bleval
    name: Bleval Inc
    executives: [jenson]
    departments: [sales, marketing, development, operations, finance]
    enabled_tools: [slack, github, crm, email, calendly]
    
  - id: hov
    name: House of Valta
    executives: [valta_prime]
    departments: [brand, creative, research, content, growth, operations]
    enabled_tools: [slack, calendly]
    
  - id: personal
    name: Personal Operations
    executives: [yamako]
    departments: [productivity, knowledge]
    enabled_tools: [calendar, email]
```

### 5.2 Organization Detail

Each organization has `organizations/<org_id>/organization.yaml` with:
- Executive definitions with role and scope
- Department configurations (manager, agents, workflows)
- Boundaries (can_control, cannot_control, spending_limit)
- Tool enablement
- Memory access configuration
- Enabled workflows

### 5.3 Memory Isolation

Each organization has dedicated memory locations:
- **Bleval**: `memory/bleval`, `memory/bleval-departments`
- **HoV**: `memory/hov`
- **Personal**: `memory/personal`

Access controls enforced via `MemoryAccessConfig`:
- Global: read
- Organization: read_write
- Departments: read_write
- Agents: read

### 5.4 Provider Initialization

Phase H providers are initialized per-organization via `ProviderRegistry`:
- Each org gets only its enabled tools
- Secrets loaded from environment/secure vault
- Provider health monitored independently

---

## 6. Workstations

### 6.1 Dashboard Architecture

The dashboard (`dashboard/`) provides four workstations:

| Workstation | Purpose | Key Panels |
|-------------|---------|------------|
| **Command Center** | Founder primary interface | System status, approvals, greetings |
| **Executive Board** | Executive oversight | 3 executive loops, cycles, health |
| **Operations** | Workflow/agent monitoring | Workflow instances, agent status |
| **Intelligence** | Research & analysis | Research workspaces, content retrieval |

Each workstation operates independently — closing one doesn't affect background operations.

### 6.2 Navigation

- `WorkspaceSidebar` — primary navigation
- `WorkstationRouter` — route management
- Deep links to specific panels (workflows, agents, memory, etc.)

---

## 7. Agents

### 7.1 Agent Types

| Type | Description | Examples |
|------|-------------|----------|
| **Executive** | Top-level coordinators, never execute work | Jenson, Valta Prime, Yamako |
| **Specialist** | Operational agents with specific capabilities | Atlas, Apollo, Nova, Forge, etc. |

### 7.2 Agent Registry

Defined in `agents/agent-registry.yaml` with 18 total agents:
- 3 Executives (Jenson, Valta Prime, Yamako)
- 15 Specialists (5 Sales, 3 Marketing, 2 Development, 2 Operations, 2 Finance)

### 7.3 Agent Detail

Each agent has `agents/<org>/<dept>/<agent>/agent.yml` with:
- Identity, description, capabilities
- Memory configuration (namespace, layers, persistence)
- Knowledge sources
- Tool interfaces (event subscriptions/emissions)
- Permissions (can/cannot)
- Output expectations

### 7.4 Capability-Based Delegation

Executives use `ExecutiveEngine.delegate_task()` to find best agents:
- Capability search index matches task description to agent capabilities
- Returns ranked list of (agent_id, match_score)
- Used by workflow engine for step assignment

---

## 8. Workflows

### 8.1 Workflow Registry

Defined in `workflows/workflow-index.yaml` with 14 workflows:

**Sales (3):**
- `sales/prospect-research` — Research and qualify prospects (Atlas → Jenson)
- `sales/outreach-campaign` — Design and execute outreach (Apollo)
- `sales/deal-closing` — Prepare proposals and close (Closer)

**Marketing (3):**
- `marketing/content-production` — Research, create, publish (Nova → Creator → Analyst)
- `marketing/campaign-launch` — Plan and launch campaigns (Nova → Creator → Jenson → Analyst)
- `marketing/market-research` — Market trends and competitive analysis (Nova)

**Development (4):**
- `development/feature-development` — Design, build, deliver (Forge → Tester → Jenson)
- `development/code-review` — Quality review (Tester)
- `development/autonomous-cycle-trigger` — Scheduled autonomous trigger (Jenson)
- `development/autonomous-lifecycle` — Full autonomous dev lifecycle (21 steps!)

**Operations (2):**
- `operations/daily-report` — Financial + health metrics (Ledger → Pulse → Jenson)
- `operations/weekly-review` — Weekly summary with recommendations

**Cross-Org (2):**
- `cross-org/executive-sync` — Synchronize all executives
- `cross-org/escalation` — Handle cross-org escalations

### 8.2 Workflow Engine

`WorkflowEngine` (`backend/axiom/engine/workflow.py`) manages:
- Instance creation and lifecycle
- Step execution with agent assignment
- Event-driven auto-launch (via EventEngine)
- Approval integration (via ApprovalManager)
- Persistence (save/load from disk)
- Dispatcher integration for task advancement

### 8.3 Autonomous Workflow Engine

`AutonomousWorkflowEngine` (`backend/axiom/engine/autonomous_workflow.py`) provides:
- Full lifecycle: PLAN → RESEARCH → DESIGN → PREPARE → EXECUTE → TEST → QC → REVIEW → PUBLISH
- Configurable approval policies
- Background monitoring loop
- Failure detection and auto-recovery

### 8.4 Workflow Observer

`WorkflowObserver` (`backend/axiom/runtime/workflow_observer.py`) provides comprehensive observability:
- Real-time metrics per workflow
- Execution timelines
- Agent performance tracking
- Bottleneck identification

---

## 9. Memory

### 9.1 Layered Architecture

`MemoryEngine` (`backend/axiom/engine/memory.py`) implements 4-layer memory:

| Layer | Scope | Access | Purpose |
|-------|-------|--------|---------|
| **Global** | System-wide | Read (all) | System prompts, shared knowledge |
| **Organization** | Per org | Read/Write (org) | Org policies, strategies, KPIs |
| **Department** | Per dept | Read/Write (dept) | Dept procedures, templates |
| **Agent** | Per agent | Read (agent) | Agent-specific context, history |

### 9.2 Memory Index

Defined in `memory/memory-index.yaml` with layer configurations.

### 9.3 Memory Operations

- `get_resolved_context(agent_id, org, dept)` — Returns merged context from all accessible layers
- `write_agent_memory(agent_id, key, content)` — Writes to agent's layer
- `read_agent_memory(agent_id, key)` — Reads from agent's layer
- Persistence to disk with integrity checks

### 9.4 Learning Integration

`LearningEngine` (`backend/axiom/engine/learning.py`) observes all executions:
- Workflow completions (success/failure, steps, retries)
- Agent task outcomes (duration, retries, errors)
- Executive cycles (decisions, outcomes, reasoning)
- Consolidates patterns into executable improvements

---

## 10. Events

### 10.1 Event Engine

`EventEngine` (`backend/axiom/engine/event.py`) provides:
- Publish/subscribe messaging
- Event type registration with schema
- Automatic workflow triggering on events
- Dead letter handling for failed deliveries

### 10.2 Event Types

Defined in `events/event-catalog.yaml` including:
- Workflow lifecycle: `workflow-started`, `workflow-completed`, `workflow-failed`
- Agent events: `agent-task-started`, `agent-task-completed`, `agent-task-failed`
- Executive events: `executive-cycle-completed`, `executive-decision-made`
- Business events: `lead-discovered`, `lead-qualified`, `response-received`, `content-published`
- System events: `system-health-check`, `approval-requested`, `approval-decided`

### 10.3 Auto-Launch Integration

Workflows with `trigger_event` are automatically subscribed:
- Event fires → Workflow instance created → Started automatically
- Event payload becomes workflow context

---

## 11. Tools

### 11.1 Tool Engine

`ToolEngine` (`backend/axiom/engine/tool.py`) manages:
- Tool registration and schema validation
- Execution with timeout and retry
- Result formatting and error handling

### 11.2 System Tools (JARVIS)

`SystemTools` (`backend/axiom/runtime/system_tools.py`) provides OS-level function calling:
- `get_telemetry` — System health and telemetry
- `launch_application` — Launch native applications
- `execute_shell` — Execute shell commands
- `read_file`, `write_file` — File operations
- `get_processes` — Process listing
- `get_network` — Network status

### 11.3 Phase H Platform Integrations

8 providers registered via `ProviderRegistry`:

| Provider | Capabilities | Auth |
|----------|--------------|------|
| **GitHub** | Repos, issues, PRs, actions, webhooks | Token |
| **Market Data** | Real-time quotes, historical data | API Key |
| **MT5** | Trading operations, account info | Login |
| **TradingView** | Charts, alerts, Pine Script | Session |
| **CRM** | Contacts, deals, pipelines | OAuth/API |
| **Email** | IMAP/SMTP, Gmail API, sequences | OAuth/Password |
| **Calendar** | Events, scheduling, availability | OAuth |
| **Slack** | Messages, channels, webhooks | Bot Token |
| **WhatsApp** | Business API messaging | Token |

All providers implement `Provider` interface with health checks, rate limiting, and tool schemas.

---

## 12. Permissions

### 12.1 Agent Permissions

Each agent defines `permissions.md` with:
- `can`: List of allowed actions
- `cannot`: List of forbidden actions

Enforced by `ToolEngine` and `WorkflowEngine` before execution.

### 12.2 Organization Boundaries

Each organization defines boundaries in `organization.yaml`:
```yaml
boundaries:
  can_control: [bleval_systems]
  cannot_control: [hov_systems, personal_systems]
  spending_limit: 0
```

Executives cannot launch workflows or agents outside their organization's boundaries.

### 12.3 Tool Access Control

Organizations define `tools_enabled` — only those providers are initialized and available to agents in that org.

---

## 13. Authority

### 13.1 Founder Authority

`FounderAuthority` (`backend/axiom/runtime/founder_authority.py`) enforces final authority over 10 restricted actions:

| Action | Description | Example |
|--------|-------------|---------|
| **MONEY** | Any financial transaction | Payments, transfers, budgets |
| **TRADES** | Trading execution | GOLD/US30 position changes |
| **CONTRACTS** | Legal agreements | NDAs, service contracts |
| **DELETION** | Irreversible data deletion | Archive removal, account deletion |
| **IRREVERSIBLE** | Actions that cannot be undone | Schema changes, migrations |
| **EXTERNAL_CLIENT_COMMS** | Client-facing communication | Proposals, invoices, support |
| **HIGH_RISK_PROSPECT_COMMS** | High-value prospect outreach | Enterprise deals, partnerships |
| **PUBLIC_PUBLISHING** | Public content release | Blog posts, press releases |
| **PRODUCTION_DEPLOYMENT** | Production system changes | Deployments, config changes |
| **MAJOR_STRATEGIC** | Strategic direction changes | Org restructuring, pivots |

### 13.2 Approval Lifecycle

1. **Request Created** — With full `ApprovalContext` (WHAT, WHY, WHO, EXPECTED_RESULT, RISK, COST, TIMELINE, SOURCE_MATERIAL, FINAL_OUTPUT)
2. **Founder Reviews** — Sees complete context in approval UI
3. **Decision** — APPROVE / REJECT / REQUEST_CHANGES / DISCUSS
4. **Execution** — Only on APPROVE; downstream action fires
5. **Audit** — Full record with timestamp, identity, notes, duration

### 13.3 Audit Trail

Every approval action recorded as `AuthorityRecord`:
- `record_id`, `founder_identity`, `action`, `status`
- `timestamp`, `approval_id`, `restricted_action`
- `artifact_id`, `artifact_version`, `approving_context`
- `downstream_action`, `notes`, `duration_ms`

---

## 14. Quality Control

### 14.1 QC Manager

`QCManager` (`backend/axiom/runtime/qc_engine.py`) provides 18 check types:

| Category | Checks |
|----------|--------|
| **Correctness** | functional_correctness, logic_validation, edge_case_handling |
| **Quality** | code_quality, documentation_completeness, test_coverage |
| **Security** | vulnerability_scan, secret_detection, dependency_audit |
| **Performance** | performance_benchmarks, resource_usage, scalability |
| **Compliance** | license_compliance, regulatory_check, policy_adherence |
| **UX** | usability_review, accessibility_check, design_consistency |

### 14.2 QC Scope

- **Workflow**: Entire workflow output
- **Step**: Individual step output
- **Artifact**: Specific deliverable (code, document, etc.)
- **Agent**: Agent's accumulated output

### 14.3 QC Flow

```
Agent/Workflow Output → QC Check → PASS → Proceed
                            ↓
                          FAIL → Rework (auto) → Re-check
                            ↓
                          (max retries) → Escalate to Executive (not Founder)
```

### 14.4 QC Specialist

`QCSpecialistHandler` integrates QC as a specialist agent type:
- Workflows can include QC steps
- Automatic quality gates in autonomous workflows
- Results fed to `QCtoLearningPipeline`

---

## 15. Learning

### 15.1 Learning Engine

`LearningEngine` (`backend/axiom/engine/learning.py`) continuously:
- Observes workflow executions (event-driven)
- Records agent task outcomes (dispatcher-instrumented)
- Tracks executive decisions (board-instrumented)
- Consolidates patterns nightly

### 15.2 Pattern Types

- **Success Patterns** — What worked, under what conditions
- **Failure Patterns** — What failed, root causes
- **Optimization Patterns** — Performance improvements
- **Preference Patterns** — Founder preferences, executive styles

### 15.3 Executive Intelligence Integration

`ExecutiveIntelligence` consumes learning patterns:
- Feeds priority decisions in executive cycles
- Provides health assessments
- Powers `ExecutiveGreeter` for context-aware greetings

### 15.4 QC-to-Learning Pipeline

`QCtoLearningPipeline` (`backend/axiom/engine/qc_learning_pipeline.py`):
- QC PASS → Reinforce successful patterns
- QC FAIL → Extract failure patterns for learning
- Feeds back into executive intelligence

---

## 16. Voice

### 16.1 Voice Architecture

`VoiceEngine` (`dashboard/components/axiom/VoiceEngine.tsx`) provides:
- **WebSocket** for real-time audio streaming
- **REST API** for command/response
- **Wake Words** per executive:
  - "Hey Jenson" → Bleval operations
  - "Valta" → Market/Trading
  - "Yamako" → Personal/Schedule
  - "Axiom" → System/Founder

### 16.2 Voice Pipeline

1. Audio capture → VAD (Voice Activity Detection)
2. Speech-to-Text (provider: configurable)
3. Intent classification → Route to executive/AXIOM
4. Response generation → Text-to-Speech
5. Audio stream back to client

### 16.3 Integration

- Dashboard voice panel with visual feedback
- Executive-specific voice personalities
- Background listening with privacy controls

---

## 17. Board Room

### 17.1 Purpose

`BoardRoom` (`backend/axiom/runtime/board_room.py`) is an **asynchronous decision-making system** — not real-time meetings. It provides structured coordination via the event bus.

### 17.2 Meeting Cadence

| Meeting | Frequency | Trigger | Purpose |
|---------|-----------|---------|---------|
| **Daily Briefing** | Daily 7-10am | Time-based | KPI snapshots, top priorities |
| **Weekly Executive** | Monday 9-11am | Time-based | Agenda items, decisions, action items |
| **Monthly Review** | 1st of month 9-11am | Time-based | Full KPI review, strategic alignment |
| **Ad-hoc** | On-demand | Founder/Executive | Urgent decisions, escalations |

### 17.3 Board Room Components

- **Meetings** — Scheduled, in-progress, completed with minutes
- **Agenda Items** — Submitted by executives, prioritized
- **KPI Snapshots** — Published by executives each cycle
- **Decisions** — Recorded with votes, approval status
- **Action Items** — Assigned, tracked, deadlined
- **Minutes** — Auto-generated, stored in memory

### 17.4 Executive Integration

Executives automatically:
- Publish KPI snapshots each cycle
- Submit agenda items for weekly/monthly
- Receive action item assignments
- Access board memory for context

---

## 18. Mobile

### 18.1 Mobile Access

Dashboard is a **Progressive Web App** (PWA) with:
- Responsive design for all screen sizes
- Offline capability for core views
- Push notifications for approvals/alerts
- Touch-optimized interactions

### 18.2 Founder Mobile Experience

- Morning greeting with system status
- Critical alerts (POI triggers, escalations)
- Approval queue with one-tap decisions
- Executive message composition
- Schedule view (Yamako integration)

---

## 19. Integrations

### 19.1 Phase H Provider Registry

All integrations managed through `ProviderRegistry` (`backend/axiom/engine/provider_registry.py`):

```python
registry = get_provider_registry()
registry.register_implementation("github", GitHubProvider)
providers = await registry.initialize_providers("bleval")
```

### 19.2 Organization-Scoped Providers

Each organization gets only its enabled providers:
- **Bleval**: GitHub, Market Data, CRM, Email, Calendar, Slack
- **HoV**: Slack, Calendar
- **Personal**: Calendar, Email

### 19.3 Provider Health & Monitoring

- Health checks every 60s
- Automatic reconnection
- Rate limit enforcement per provider
- Structured logging for audit

### 19.4 Adding New Providers

1. Implement `Provider` base class
2. Define `ProviderModel` schema
3. Register in `ProviderRegistry`
4. Add tools to `ProviderToolDefinition`
5. Configure secrets in environment
6. Add to org's `tools_enabled`

---

## 20. Deployment

### 20.1 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Dashboard │     │   Backend   │     │  Providers  │
│  (Next.js)  │────▶│  (FastAPI)  │────▶│  (External) │
│  :3000      │     │  :8000      │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Runtime    │
                    │  (State)    │
                    │ backend/    │
                    │ runtime/    │
                    └─────────────┘
```

### 20.2 Environment Variables

Required:
```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
# Provider-specific:
GITHUB_TOKEN=...
MARKET_DATA_API_KEY=...
MT5_LOGIN=...
# etc.
AXIOM_STATE_DIR=/path/to/state
```

### 20.3 Startup Commands

**Development:**
```bash
# Backend
uvicorn main:app --reload --port 8000

# Dashboard
cd dashboard && npm run dev
```

**Production:**
```bash
# Docker Compose (recommended)
docker-compose up -d

# Or manual
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
cd dashboard && npm run build && npm start
```

### 20.4 Health Checks

- `GET /api/v1/status` — Full system status
- `GET /api/v1/health` — Component health
- `GET /api/v1/executives/board/status` — Executive loops
- `GET /` — Root service info

---

## 21. Recovery

### 21.1 Recovery Manager

`RecoveryManager` (`backend/axiom/runtime/recovery.py`) handles:
- **Workflow Restart Recovery** — Resume from last completed step
- **Executive Loop Recovery** — Restart failed loops with state restoration
- **Event Bus Recovery** — Replay unprocessed events from dead letter
- **Memory Integrity Recovery** — Verify and repair memory layers

### 21.2 Recovery Triggers

- Automatic: Health monitor detects component failure
- Manual: `POST /api/v1/recovery/workflow/{instance_id}/restart`
- Scheduled: Nightly integrity checks

### 21.3 Safe Failure Modes

| Component | Failure Mode | Recovery |
|-----------|--------------|----------|
| Workflow | Step failure | Retry → Rework → Escalate to Executive |
| Executive Loop | Cycle exception | Restart loop, preserve memory |
| Event Bus | Subscription failure | Dead letter → Replay on recovery |
| Provider | Connection loss | Exponential backoff → Alert |
| Memory | Corruption | Read-only → Repair from backup |

---

## 22. Security

### 22.1 Secrets Management

`SecretsManager` (`backend/axiom/config.py:SecretsManager`):
- Priority: Env vars → .env → Secret files → External vault
- Never logged (auto-redacted in logs)
- Cache with rotation support

### 22.2 Authentication & Authorization

- API: Bearer tokens (configurable)
- Dashboard: Session-based with CSRF
- WebSocket: Token authentication
- Provider auth: Per-provider (OAuth, API keys, tokens)

### 22.3 Audit & Compliance

- All approvals audited via `FounderAuthority`
- All executive decisions logged
- All workflow executions traced
- Memory access logged

### 22.4 Data Protection

- Encryption at rest for state directory
- TLS for all external connections
- PII detection in memory (`aidefence_has_pii`)
- Secure deletion on request

---

## 23. Maintenance

### 23.1 Routine Operations

| Task | Frequency | Command |
|------|-----------|---------|
| Health check | Continuous | `GET /health` |
| Log rotation | Daily | Automatic |
| Memory consolidation | Nightly | Learning engine |
| Provider health | Every 60s | Provider registry |
| Backup state | Daily | Cron job |

### 23.2 Monitoring Commands

```bash
# CLI status
python -m backend.axiom.cli.main status

# Workflows
python -m backend.axiom.cli.main workflows
python -m backend.axiom.cli.main instances

# Organizations
python -m backend.axiom.cli.main organizations

# Agents
python -m backend.axiom.cli.main agents

# Health
python -m backend.axiom.cli.main health
```

### 23.3 Debugging

- Structured logging in `backend/runtime/logs/`
- Event log in `backend/runtime/events/`
- Workflow persistence in `backend/runtime/state/workflows/`
- Executive memory in `memory/agents/<exec_id>/`

---

## 24. Extension Guidelines

### 24.1 Adding a New Organization

1. Create `organizations/<org_id>/organization.yaml`
2. Add entry to `organizations/organization.yaml`
3. Define departments in `departments/<org_id>/`
4. Add agents in `agents/<org_id>/`
5. Add workflows in `workflows/`
6. Configure tools in `organizations/<org_id>/tools/tools.yaml`
7. Add identity/permissions markdown files

### 24.2 Adding a New Executive

1. Add agent YAML in `agents/<exec_id>.yml`
2. Register in `agents/agent-registry.yaml`
3. Add to `EXECUTIVE_ORGS` and `EXECUTIVE_DEPTS` in `executive_constants.py`
4. Create executive loop in `ExecutiveBoard.start_all()`
5. Define schedules and special capabilities

### 24.3 Adding a New Department

1. Create `departments/<org_id>/<dept_id>/department.yaml`
2. Add agents to department
3. Define workflows for department
4. Register capabilities
5. Update organization's department list

### 24.4 Adding a New Workflow

1. Create `workflows/<dept>/<name>.yaml` with steps
2. Register in `workflows/workflow-index.yaml`
3. Define trigger_event for auto-launch
4. Add to organization's workflows_enabled
5. Test with `python -m backend.axiom.cli.main launch <workflow_id>`

### 24.5 Adding a New Agent

1. Create `agents/<org>/<dept>/<agent_id>/agent.yml`
2. Add identity.md, instructions.md, permissions.md
3. Register in `agents/agent-registry.yaml`
4. Define capabilities in `capabilities/`
5. Add specialist handler if needed

### 24.6 Adding a New Tool/Provider

1. Implement `Provider` base class
2. Define `ProviderModel` with config schema
3. Create `ProviderToolDefinition` for each capability
4. Register in `ProviderRegistry`
5. Add implementation YAML in `backend/axiom/engine/providers/`
6. Update organization tool enablement

### 24.7 Adding a New QC Check

1. Define new `QCCheckType` in `qc.py`
2. Implement check logic in `QCManager`
3. Add to `QCSpecialistHandler`
4. Integrate with `QCtoLearningPipeline`

---

## Appendix A: File Structure

```
Bleval-ai-os/
├── agents/                    # Agent definitions
│   ├── agent-registry.yaml
│   ├── Jenson.yml
│   ├── valta_prime.yml
│   ├── Yamako.yml
│   └── bleval/...            # Specialist agents
├── backend/
│   ├── axiom/
│   │   ├── config.py          # Paths, settings, secrets
│   │   ├── core/              # AXIOM Core
│   │   ├── engine/            # Core engines
│   │   ├── integrations/      # Phase H providers
│   │   ├── models/            # Pydantic models
│   │   ├── registry/          # Registry loaders
│   │   └── runtime/           # Runtime subsystems
│   └── main.py                # FastAPI entry point
├── capabilities/              # Capability catalog
├── dashboard/                 # Next.js frontend
├── departments/               # Department definitions
├── events/                    # Event catalog
├── memory/                    # Memory layers + agent memory
├── organizations/             # Organization definitions
├── workflows/                 # Workflow definitions
└── docs/                      # Documentation (this file)
```

---

## Appendix B: API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/status` | Full system status |
| GET | `/api/v1/health` | Component health |
| GET | `/api/v1/organisations` | List organizations |
| GET | `/api/v1/organisations/{id}` | Organization detail |
| GET | `/api/v1/executives` | List executives |
| GET | `/api/v1/executives/{id}` | Executive detail |
| GET | `/api/v1/executives/board/status` | Executive board status |
| POST | `/api/v1/executives/board/trigger` | Trigger all exec cycles |
| GET | `/api/v1/executives/{id}/loop/status` | Executive loop status |
| POST | `/api/v1/executives/{id}/loop/trigger` | Trigger exec cycle |
| GET | `/api/v1/agents` | List all agents |
| GET | `/api/v1/agents/{id}` | Agent detail |
| GET | `/api/v1/workflows` | List workflows |
| GET | `/api/v1/workflows/{id}` | Workflow detail |
| POST | `/api/v1/workflows/launch` | Launch workflow |
| GET | `/api/v1/instances` | List instances |
| GET | `/api/v1/instances/{id}` | Instance detail |
| POST | `/api/v1/instances/{id}/advance` | Advance instance |
| POST | `/api/v1/instances/{id}/cancel` | Cancel instance |
| GET | `/api/v1/axiom/awareness` | System awareness |
| POST | `/api/v1/axiom/chat` | Chat with AXIOM |
| POST | `/api/v1/axiom/communicate` | Route to executive |
| POST | `/api/v1/axiom/research` | Create research workspace |

---

## Appendix C: Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-08-05 | Phase I — Production Hardening + Real Operations |
| 2.0.0 | 2026-07-XX | Phase C — Autonomous Workflow + Agent System |
| 1.0.0 | 2026-06-XX | Phase A — Foundation |

---

**End of Specification**

*This document is the authoritative reference for AXIOM OS. All implementation decisions should align with this specification. For questions or proposed changes, consult the Founder.*