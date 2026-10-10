# Phase 1 Repository Audit Report

## 1. Repository Overview

- **Root**: `C:\Users\byagi\Desktop\Bleval-ai-os`
- **Git Branch**: `main` (ahead of origin/main by 2 commits)
- **Last Commit**: `2da1201 OS-CleanUp`
- **Untracked Files**: `backend/logs/`, `backend/test_config_paths.py`, `dashboard/logs/`, `dashboard/tests/`, `scripts/start-axiom-os.ps1`
- **Modified Files**: 
  - `backend/axiom/config.py`
  - `backend/axiom/runtime/lifecycle.py`
  - `dashboard/components/boot/BootSequence.tsx`
  - `dashboard/lib/voice/speak.ts`
  - `dashboard/package.json`

## 2. Dependency Inventory

### Backend (Python)
- **Python Version**: 3.11.9 (virtual environment at `backend/.venv`)
- **Key Dependencies** (from `requirements.txt`):
  - `fastapi==0.141.1`
  - `uvicorn==0.52.4`
  - `pydantic==2.13.4`
  - `anthropic==1.0.0`
  - `openai==3.3.1`
  - `elevenlabs>=2.65.0`
  - `sqlalchemy==2.0.52`
  - `asyncpg==0.31.0`
  - `faster-whisper==1.0.2`
  - `librosa==0.11.0`
  - `openwakeword==0.6.0`
  - `vosk==0.3.45`
  - `webrtcvad-wheels`
  - `sounddevice==0.5.0`
  - `python-dotenv==1.2.3`
  - `python-multipart==0.0.32`
  - `PyYAML==6.0.3`
  - `rich==15.0.0`
  - `pytest==9.1.1`
- **Editable Install**: `-e git+https://github.com/bleval-Inc/Bleval-ai-os.git@8f7c1c34ae68155b83c6e87258effdf577ea4afb#egg=axiom_os&subdirectory=backend`

### Frontend (Node.js)
- **Node Version**: Not explicitly specified; uses `@types/node "^20"` in devDependencies.
- **Key Dependencies** (from `dashboard/package.json`):
  - `next@16.2.10`
  - `react@19.2.4`
  - `react-dom@19.2.4`
  - `@radix-ui/react-dialog`, `@radix-ui/react-popover`, `@radix-ui/react-tooltip`
  - `framer-motion@12.42.2`
  - `lucide-react@1.27.0`
  - `zustand@5.0.14`
  - `tailwindcss@4`
  - `typescript@5`
- **Scripts**: `dev`, `build`, `start`, `lint`

## 3. Directory Structure

### Backend
```
backend/
├── main.py                 # FastAPI entry point
├── axiom/                  # Core Python package
│   ├── config.py           # Path resolution & environment settings
│   ├── models/             # Pydantic data models
│   ├── registry/           # YAML configuration loaders
│   ├── engine/             # Core platform engines
│   └── runtime/            # Execution layer (lifecycle, scheduler, dispatcher, etc.)
├── integrations/           # Provider integrations (Slack, GitHub, CRM, Email, etc.)
├── data/                   # Database models and repositories
├── cli/                    # CLI command definitions
├── voice_pipeline_routes.py# Voice API routes
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

### Frontend
```
dashboard/
├── app/                    # Next.js 13+ app router
│   ├── axiom/              # Axiom OS dashboard
│   ├── bleval/             # Bleval Inc. workspace
│   ├── personal/           # Personal operations
│   ├── valta/              # House of Valta workspace
│   ├── boardroom/          # Executive boardroom
│   ├── system/             # System monitoring
│   ├── settings/           # System settings
│   ├── AppShell.tsx        # Layout shell
│   ├── globals.css         # Global styles
│   └── layout.tsx          # Root layout
├── lib/                    # Shared libraries
│   ├── api.ts              # API client (Next.js proxy to /api/v1)
│   ├── store/              # Zustand stores (boot-store, axiom-store)
│   ├── voice/              # Voice engine (SpeechSynthesis, ElevenLabs optional)
│   ├── utils.ts
│   ├── api-types.ts
│   └── phase8c-types.ts
├── components/             # Reusable UI components
│   ├── boot/               # BootSequence.tsx (modified)
│   ├── dashboard/          # Workspace-specific data components
│   ├── workspace/          # Workstation components
│   └── ...                 # Other components
├── hooks/                  # Custom React hooks
├── public/                 # Static assets
└── styles/                 # Tailwind CSS (via globals.css)
```

### Agent System Configuration (`agent_system/`)
```
agent_system/
├── organizations/          # Organization definitions (bleval, hov, personal)
├── departments/            # Department definitions
├── core/                   # Executive definitions (Jenson, Valta Prime, Yamako)
├── agents/                 # Specialist agent registry (Atlas, Apollo, Closer, etc.)
├── workflows/              # Workflow definitions (sales, marketing, development, etc.)
├── capabilities/           # Capability definitions
├── memory/                 # Memory layer definitions
├── events/                 # Event type definitions
└── ruflo/                  # Ruflo agent coordination framework (placeholder)
```

### Miscellaneous
- `scripts/start-axiom-os.ps1` – PowerShell startup script (untracked)
- `tests/` – Voice detection and pipeline test files
- `docs/` – Extensive documentation
- `.env` – Environment variables (see Section 4)

## 4. Environment Configuration

The `.env` file contains the following keys (values omitted for security):

- `ANTHROPIC_API_KEY=` **(empty)**
- `OPENAI_API_KEY=` **(empty)**
- `NVIDIA_API_KEY=` **set** (NVIDIA NIM master key)
- `NVIDIA_API_BASE_URL=https://integrate.api.nvidia.com/v1`
- Individual NVIDIA model keys (all set to the master key)
- `NEON_DATABASE_URL=` **set** (PostgreSQL connection string)
- `SLACK_BOT_TOKEN=` **(empty)**
- `SLACK_SIGNING_SECRET=` **(empty)**
- `REAL_PROVIDERS_ONLY=true`
- `DEBUG=false`
- `AXIOM_ENV=production`

## 5. Runtime Initialization

- **Entry Point**: `backend/main.py` (FastAPI with lifespan events)
- **Lifecycle Manager**: `backend/axiom/runtime/lifecycle.py` (modified)
  - Initializes all engines (memory, event, tool, workflow, executive, intelligence, etc.)
  - Registers integration providers (Slack, GitHub, CRM, Email, Calendar, etc.)
  - Sets up cross-component wiring (event → workflow auto-launch, learning engine, QC, founder authority, etc.)
  - Initializes voice pipeline (`backend/axiom.voice.pipeline_orchestrator`)
- **Health Endpoints**:
  - `GET /` → service info
  - `GET /health` → health summary
  - `GET /status` → runtime status
  - `GET /api/v1/health` → detailed health (via Next.js proxy)
- **Voice Pipeline**:
  - Backend orchestrator: `backend/axiom/voice/pipeline_orchestrator.py`
  - Frontend library: `dashboard/lib/voice/speak.ts` (modified)
  - Uses browser SpeechSynthesis (free) with optional ElevenLabs premium
  - Configured wake words: `axiom`, `jenson`, `valta_prime`, `yamako`

## 6. API Routes (Backend)

Exposed via FastAPI under `/api/v1` (proxied by Next.js from `/api/v1`):

- **System**: `/status`, `/health`, `/`
- **Organisations**: `/organisations`
- **Executives**: `/executives`
- **Agents**: `/agents`
- **Workflows**: `/workflows`
- **Instances**: `/instances`
- **Events**: `/events`
- **Capabilities**: `/capabilities`
- **Memory**: `/memory/{agentId}`
- **Approvals**: `/approvals`
- **Learning**: `/learning/*`
- **Quality Control**: `/qc/*`
- **Founder**: `/founder/*`
- **Executive Intelligence**: `/executives/{execId}/intelligence`
- **Voice**: `/voice/*`
- **Board Room**: `/board/*`
- **Communications**: `/communication/*`
- **Axiom Core**: `/axiom/*`
- **Intelligence Layer (Phase 8C)**: `/intelligence/*`
- **Content Hub (Phase 8C)**: `/content/*`
- **Integrations (Phase 8C)**: `/integrations/*`
- **Collaboration (Phase 8C)**: `/collaboration/*`

## 7. Frontend-Backend Connectivity

- Next.js `next.config.ts` rewrites `/api/v1/:path*` to `http://127.0.0.1:8000/api/v1/:path*`
- Frontend API client (`dashboard/lib/api.ts`) uses base `/api/v1`
- No direct backend access; all requests go through Next.js proxy in development.
- In production, the same rewriting would need to be configured (e.g., via Vercel or custom server).

## 8. Observed Issues (from git status and file inspection)

- Modified `backend/axiom/config.py` and `lifecycle.py` suggest recent changes to runtime initialization.
- Modified `dashboard/components/boot/BootSequence.tsx` indicates changes to boot animation/greeting flow.
- Modified `dashboard/lib/voice/speak.ts` indicates voice engine tuning.
- Modified `dashboard/package.json` suggests dependency updates.
- Numerous backup files (`*.bak`, `*.backup`) present in backend (likely safe to remove).
- Duplicate directory `backend/backend/` containing a copy of `voice_pipeline_routes.py` (likely unused).
- Empty API keys for Anthropic and OpenAI; system likely runs in mock mode or relies solely on NVIDIA NIM.
- `REAL_PROVIDERS_ONLY=true` enforces real providers only; with missing Anthropic/OpenAI keys, only NVIDIA NIM is available.

## 9. Conclusion

The repository contains a substantial AI operating system with:
- A modular backend engine architecture (memory, event, tool, workflow, executive, intelligence, etc.)
- A rich agent and workflow definition system (YAML-based)
- A Next.js dashboard with server‑side routing and voice integration
- Integration layers for Slack, GitHub, CRM, Email, Calendar, etc.
- Voice wake‑word detection and speech synthesis (browser‑based, optional ElevenLabs)
- Configuration‑driven organization, department, and executive setup
- Comprehensive documentation

The system appears to be in a working state, but several areas need verification:
- Backend startup and health endpoint responsiveness
- Voice pipeline initialization and wake‑word detection
- Frontend‑backend connectivity (ECONNREFUSED errors previously reported)
- Provider availability (NVIDIA NIM functionality)
- Workflow and agent execution
- Persistence and memory layer operation

These will be investigated in the validation steps.
