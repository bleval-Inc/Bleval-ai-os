# Phase 2 Repair Plan

## Overview
Based on the findings from Phase 1 (repository audit, dependency inventory, architecture mapping, and static validation), Phase 2 will focus on repairing identified issues, integrating subsystems, optimizing performance, and preparing the system for production readiness. The plan follows the sequence prescribed in the original instructions, starting with backend startup and lifecycle and progressing through dashboard connectivity, intelligence providers, executive/agent/workflow execution, memory persistence, voice pipeline, security hardening, observability improvements, regression testing, and final production verification.

Each area includes specific goals, verification steps, and acceptance criteria. Work will be performed in small, auditable increments, with validation after each meaningful batch.

## 1. Backend Startup and Lifecycle

### Goals
- Ensure deterministic configuration loading and validation of required settings before subsystem initialization.
- Guarantee correct initialization order of critical engines (memory, event, tool, intelligence, etc.).
- Handle optional integrations gracefully (e.g., missing Slack or GitHub tokens) without disabling unrelated functionality.
- Expose truthful readiness and liveness information via health endpoints.
- Implement graceful shutdown that releases resources and cancels background tasks.
- Prevent duplicate initialization and competing server processes.
- Report startup failures clearly with actionable logs.

### Activities
- Review `backend/axiom/config.py` and `backend/axiom/runtime/lifecycle.py` for:
  - Proper validation of required settings (e.g., at least one intelligence provider key when `REAL_PROVIDERS_ONLY=true`).
  - Ordered initialization of engines (dependencies respected).
  - Error handling during bootstrap (e.g., log and halt on critical failures).
  - Ensuring `settings.ensure_dirs()` is called before any engine that relies on those directories.
- Add or refine health endpoints:
  - `/health/liveness` – returns 200 if the process is running.
  - `/health/readiness` – returns 200 only when all critical subsystems (memory, event, intelligence, etc.) are initialized and able to serve requests.
  - Possibly `/health/providers` – status of each configured intelligence provider.
- Verify that the lifespan event handler in `backend/main.py` correctly calls `runtime.start()` and `runtime.shutdown()`.
- Ensure that background tasks (scheduler, dispatcher, learning engine, etc.) are properly cancelled on shutdown.
- Test startup failure scenarios (e.g., missing required directory permissions) and verify error messages are logged and visible.

### Acceptance Criteria
- Backend starts successfully when all required configuration is present.
- Health endpoints return appropriate status codes reflecting true system state.
- Shutdown completes without hanging or leaving orphaned processes.
- Startup failures are logged with clear messages and prevent the system from claiming readiness.

## 2. Dashboard–Backend Connectivity

### Goals
- Eliminate `ECONNREFUSED 127.0.0.1:8000` errors in the dashboard.
- Ensure the dashboard waits for backend readiness before attempting API calls.
- Fix any 404 errors during initialization.
- Confirm that API base URLs are correct in both development and production.
- Implement reliable startup orchestration in the PowerShell script (`scripts/start-axiom-os.ps1`).
- Add bounded retries with exponential backoff and jitter to dashboard API requests where appropriate.
- Preserve useful error messages and implement deliberate loading, empty, and recovery states in the UI.

### Activities
- Examine the PowerShell startup script and enhance it to:
  1. Start the backend process (uvicorn) and capture its PID.
  2. Poll the backend health endpoint (`/health`) with a timeout and exponential backoff.
  3. Only start the Next.js dev server after the backend reports ready.
  4. Log startup progress and failures to console and log files.
  5. On termination, stop only the processes started by the script.
- Review `dashboard/next.config.ts` to ensure rewrites are correct for both development and production (consider using environment‑specific config).
- Audit dashboard API client (`dashboard/lib/api.ts`) for:
  - Proper error handling (catching `ApiError` and mapping to UI states).
  - Implementation of retry logic for idempotent requests (e.g., GET requests) with exponential backoff and jitter, respecting HTTP semantics.
  - Distinction between transient errors (network, 5xx) and permanent errors (4xx except 429).
- Verify that each primary dashboard route (axios, bleval, personal, valta, boardroom, system, settings) resolves and that its data‑fetching logic handles loading, error, and empty states.
- Ensure that the boot sequence (`dashboard/components/boot/BootSequence.tsx`) correctly waits for the `system.status()` API call and transitions to greeting only after successful fetch.

### Acceptance Criteria
- Backend starts and becomes reachable within a configurable timeout (e.g., 30 seconds).
- Dashboard does not show 404 or error pages during initialization; it displays a loading state until backend is ready.
- API calls from the dashboard succeed and update the UI with fetched data.
- Retry logic does not cause infinite loops or duplicate non‑idempotent operations.
- UI shows meaningful error messages when backend is down or returns errors.

## 3. Intelligence Providers and Model Routing

### Goals
- Verify that the configured intelligence providers (NVIDIA NIM, with optional Anthropic/OpenAI) are functional.
- Ensure provider registration, model identifiers, base URLs, authentication handling, and request/response schemas are correct.
- Validate timeout handling, retry policies, rate‑limit handling, and fallback behavior.
- Confirm that error classification and logging are adequate.
- Test NVIDIA NIM with authenticated inference requests to ensure it is usable.
- Preserve existing Claude Code and LiteLLM gateway integration where required.

### Activities
- Inspect the provider registry (`backend/axiom/engine/provider_registry.py`) and provider implementations (under `backend/axiom/integrations/`).
- Verify that the NVIDIA NIM provider uses the correct base URL (`https://integrate.api.nvidia.com/v1`) and that API key is taken from environment.
- Check that the provider registration in `lifecycle.py` occurs after the provider registry is initialized.
- Examine the intelligence engine (`backend/axiom/engine/intelligence.py`) for:
  - Model selection logic (capability‑aware routing via `MultiModelEngine`).
  - Timeout settings for provider requests.
  - Retry mechanism (e.g., exponential backoff) and respect for `Retry-After` headers.
  - Rate‑limit handling (e.g., 429 responses).
  - Error classification (distinguish provider errors, network errors, invalid requests).
- Perform a minimal authenticated inference test against a NVIDIA NIM model (e.g., using the master key from `.env`) to confirm:
  - The endpoint is reachable.
  - The request is accepted and returns a non‑empty response.
  - The response format matches the expected schema.
- Verify that if both Anthropic and OpenAI keys are missing, the system does not fall back to mock mode when `REAL_PROVIDERS_ONLY=true` (should error or degrade gracefully).
- Ensure that the fallback to mock mode (when keys are present and `REAL_PROVIDERS_ONLY=false`) is functional for testing.

### Acceptance Criteria
- At least one intelligence provider (NVIDIA NIM) is successfully initialized and can process a test request.
- The intelligence engine logs provider successes and failures with sufficient detail.
- Timeout and retry behavior protect the system from hanging on unresponsive providers.
- Error responses are propagated appropriately to callers (workflows, agents, etc.).
- The system does not claim readiness if no intelligence provider is available and `REAL_PROVIDERS_ONLY=true`.

## 4. Executives, Agents, and Workflows

### Goals
- Validate that registered executives resolve correctly and have appropriate capabilities.
- Confirm that organizations and departments load consistently from YAML.
- Ensure agent capabilities match their declared responsibilities and that the agent registry is consulted dynamically.
- Verify that workflow definitions pass validation (YAML parsing, required fields, step ordering).
- Ensure workflow triggers reach the correct dispatcher and that agents receive the correct context.
- Confirm that tools are authorized and invoked correctly based on agent capabilities.
- Validate that results and failures propagate to callers and that background execution respects concurrency limits.
- Check that approval gates are respected and that recovery/retry logic does not create duplicate or unbounded work.
- Test representative workflows end to end where dependencies are available (e.g., internal workflows that do not require external providers).

### Activities
- Review the YAML loading logic in `backend/axiom/registry/` (organization.py, department.py, executive.py, agent.py, workflow.py).
- Ensure that changes to YAML files are reflected at runtime (hot‑reload not required; but loading occurs at startup).
- Verify that the executive engine (`backend/axiom/engine/executive.py`) correctly maps executive names to IDs and departments.
- Check the agent registry (`backend/axiom/registry/agent.py`) for proper capability lookup and that specialist agents are instantiated with the correct intelligence and tool engines.
- Examine workflow engine (`backend/axiom/engine/workflow.py`) for:
  - Validation of workflow YAML (name, org, department, coordinator, agents, steps).
  - Detection of circular step dependencies.
  - Proper initialization of step inputs/outputs and event emission.
- Inspect the dispatcher (`backend/axiom/runtime/dispatcher.py`) for:
  - Task execution flow (including tool invocation, agent selection, capability checks).
  - Concurrency limits (e.g., max simultaneous tasks per agent type).
  - Handling of task success/failure and event emission (`task-completed`, `task-failed`).
- Review the learning engine (`backend/axiom/engine/learning.py`) to ensure it observes workflow and agent task events for improvement.
- Verify that the approval manager (`backend/axiom/runtime/approval.py`) enforces that certain actions require approval and that approvals are recorded.
- Test a simple internal workflow (e.g., `operations/daily-report` if it exists) that does not require external intelligence or tools, to confirm the end‑to‑end flow:
  - Workflow definition loads.
  - Trigger (manual or event) creates an instance.
  - Dispatcher assigns steps to appropriate agents.
  - Agents execute steps (using mock tools if needed) and produce outputs.
  - Workflow progresses to completion and emits `workflow-completed` event.
- Ensure that recovery manager (`backend/axiom/runtime/recovery.py`) can retry failed workflow steps without duplicating work if the failure is transient.

### Acceptance Criteria
- All executives, departments, and agents listed in the YAML registries are loaded and accessible via the API.
- Workflow definitions are valid and can be instantiated.
- Agents can be dispatched to perform tasks that match their capabilities.
- Tools are invoked only when the agent has the required capability.
- Workflow progression respects step dependencies and emits appropriate events.
- Approval gates block execution until approval is granted (where required).
- Background execution does not exceed configured concurrency limits.
- Recovery retries failed steps but does not create infinite loops on persistent failures.

## 5. Memory, Database, and Data Integrity

### Goals
- Verify the actual memory architecture and persistence layer.
- Test initialization, read/write operations, retrieval, scoping, and isolation.
- Ensure error handling is adequate and that database connections are managed properly.
- Protect existing data; avoid destructive migrations or accidental data loss.
- Confirm that schema and migration consistency are maintained.
- Validate connection pooling and cleanup.

### Activities
- Examine the memory engine (`backend/axiom/engine/memory.py`) and its backing storage (likely SQLite or PostgreSQL via `backend/axiom/data/`).
- Check the database manager (`backend/axiom/data/database.py`) for:
  - Connection pooling (if using asyncpg or SQLAlchemy).
  - Initialization of tables on startup (if using migrations).
  - Proper closing of connections on shutdown.
- Verify that memory scoping (global → org → department → agent) is enforced in the API (`/memory/{agentId}?org=&dept=`).
- Ensure that memory write operations validate input size and sanitize where necessary.
- Check that the system does not perform destructive migrations on startup; if migrations are needed, they should be backward‑compatible and have a clear rollback plan.
- Test memory read and write operations via the API (if possible) or through direct engine calls in a controlled environment.
- Verify that event store (`backend/axiom/engine/event.py`) persists events to disk and can be replayed on restart.
- Confirm that logs are written to the configured log directory and rotated appropriately (if applicable).

### Acceptance Criteria
- Memory engine initializes without errors and creates the configured storage directories.
- Read and write operations succeed and return expected data.
- Scoping rules prevent cross‑org/department/agent leakage (unless explicitly shared via public memory).
- Database connections are properly closed on shutdown; no orphaned connections remain.
- Event logging persists across restarts.
- No data loss occurs during normal startup/shutdown cycles.

## 6. Voice System

### Goals
- Inspect the current voice implementation before making changes.
- Verify each actual stage: microphone acquisition, audio format/configuration, wake‑word model loading, wake‑word detection, speech capture, speech recognition, command interpretation, executive routing, response generation, speech synthesis, playback, and resource cleanup.
- Test all four configured wake words (`axiom`, `jenson`, `valta_prime`, `yamako`) where hardware and models are available.
- Confirm that voice commands invoke the same executive and intelligence pathways used by other interfaces (e.g., API CLI).
- Keep optional premium speech services (ElevenLabs) optional; ensure absence of ElevenLabs key does not disable core functionality.
- Preserve working microphone and speech behavior; do not replace recognition engine, wake‑word framework, or speech synthesis stack without comparative testing and a justified migration plan.

### Activities
- Review the voice pipeline orchestrator (`backend/axiom/voice/pipeline_orchestrator.py`) and its components:
  - Wake word detection (likely using `openwakeword` or `vosk`).
  - Audio capture (using `sounddevice`).
  - Speech recognition (using `faster-whisper` or `vosk`).
  - Text‑to‑speech (browser SpeechSynthesis via frontend, or optionally ElevenLabs).
- Ensure that the voice pipeline is initialized after core components (memory, event, intelligence, etc.) in `lifecycle.py`.
- Verify that the wake word models for the four configured words are present and loadable (check file paths in config or code).
- Test wake‑word detection with a simple script (if possible) to confirm that the models trigger on the correct phrases.
- Verify that detected speech is routed to the intelligence engine via the appropriate executive (based on the wake word: `axiom` → no specific executive? `jenson` → Jenson executive, `valta_prime` → Valta Prime, `yamako` → Yamako).
- Confirm that the frontend voice library (`dashboard/lib/voice/speak.ts`) correctly selects the best available browser voice and optionally uses ElevenLabs if a key is provided.
- Ensure that the voice pipeline does not consume excessive CPU or block the main event loop.
- Check that audio resources are properly released after each interaction (no leaking audio streams).

### Acceptance Criteria
- Voice pipeline starts without errors and logs indicate wake‑word models are loaded.
- Speaking a wake word triggers detection and transitions to listening state.
- Captured speech is transcribed correctly (or at least produces a non‑empty string) for clear speech in a quiet environment.
- The recognized command is routed to the appropriate executive (or defaults to a fallback).
- The executive’s response is generated via the intelligence engine and spoken back through the selected voice.
- Volume, rate, and pitch settings are applied as configured in the frontend voice library.
- Disabling the ElevenLabs key (if present) falls back to browser SpeechSynthesis without breaking core functionality.
- No audio resource leaks are observed after multiple interactions.

## 7. Security and Configuration

### Goals
- Review the complete application for production‑relevant security issues.
- Inspect environment‑variable handling, secret exposure, authentication and authorization, CORS policy, API request validation, injection risks, unsafe tool execution, filesystem access, subprocess execution, dependency vulnerabilities, logging of sensitive information, database credentials, network binding, debug settings, and production error responses.
- Validate configuration at startup and distinguish required settings from optional integrations.
- Use safe defaults and fail closed where unauthorized access or dangerous execution is possible.
- Avoid enabling public network access, weakening authentication, or exposing administrative tools merely to make connectivity tests pass.
- Ensure no live credentials are printed, committed, or included in audit reports.

### Activities
- Audit the CORS middleware configuration in `backend/main.py` (currently `allow_origins=["*"]`); for production, restrict to trusted origins (e.g., the dashboard domain).
- Review API request validation: ensure that incoming JSON is parsed safely and that pydantic models validate input.
- Check for potential injection points:
  - SQL injection (use of ORM/raw queries) – verify use of parameterized queries or ORM.
  - Command injection (subprocess execution) – ensure any use of `subprocess` sanitizes input.
  - Path traversal (file reads) – validate that file paths are constrained to allowed directories.
- Verify that secrets (API keys, database URLs) are not logged anywhere; check that logging utilities sanitize sensitive fields (the `secrets_manager.sanitize_for_logging` method appears to be used).
- Ensure that debug settings (`DEBUG=false`) are respected and that debug endpoints (e.g., `/api/v1/debug/voice`) are either removed or protected in production.
- Confirm that the system does not expose internal configuration via API endpoints (e.g., no endpoint leaks `.env` contents).
- Review dependency versions for known vulnerabilities (via `pip audit` or similar; note that this is an informational step).
- Ensure that file‑system access (e.g., reading YAML configs, writing cache/persistence) is restricted to intended directories.
- Check that subprocess execution (if any, e.g., for wake‑word detection) uses validated arguments and does not expose shell injection.

### Acceptance Criteria
- CORS is restricted to specific origins in production (or at least configurable via environment).
- No sensitive data (API keys, secrets) appears in logs or error messages returned to clients.
- The system fails safely when required secrets are missing (e.g., clear error message rather than silent degradation).
- All external integrations that require authentication have proper credential checks.
- Dependency scan shows no critical unpatched vulnerabilities (or a plan to address them).
- The system does not execute arbitrary commands or read/write files outside of permitted directories.

## 8. Observability, Recovery, and Performance

### Goals
- Improve operational diagnostics where evidence supports the change.
- Ensure structured, actionable logs.
- Consistent error classification.
- Correlation identifiers where useful (e.g., request‑ID tracing).
- Timeouts on external operations.
- Bounded retries.
- Appropriate concurrency limits.
- Graceful shutdown.
- Detection of failed background tasks.
- Health checks for critical dependencies.
- Useful performance measurements (where meaningful and safe).
- Avoid installing an entire monitoring stack merely to expose a few measurements.
- Use the project's existing infrastructure unless there is a strong technical reason to introduce something new.

### Activities
- Review the runtime logger (`backend/axiom/runtime/logging.py`) to ensure it outputs structured logs (e.g., JSON) or at least consistent levels.
- Verify that engines and subsystems include contextual information (e.g., workflow ID, agent ID) in their log messages where relevant.
- Check that the health monitor (`backend/axiom/runtime/monitor.py`) performs periodic checks on critical dependencies (e.g., database connection, intelligence provider connectivity) and exposes results via health endpoints.
- Ensure that the recovery manager logs failed attempts and that repeated failures trigger alerts.
- Verify that background tasks (scheduler, dispatcher, learning engine) have configurable concurrency limits and that they respect them.
- Examine any existing performance counters or metrics (if any) and consider adding lightweight timings for critical paths (e.g., workflow step execution, provider request latency) without overhead.
- Ensure that logs are rotated or size‑limited to prevent unbounded disk growth.
- Verify that the system does not have unbounded queues (e.g., the event engine should have a reasonable max queue size or back‑pressure mechanism).

### Acceptance Criteria
- Logs are readable and contain sufficient context to diagnose issues.
- External operations have timeouts that prevent indefinite hanging.
- Retry policies are bounded and do not exhaust system resources.
- Background tasks respect concurrency limits and do not overwhelm the system.
- Health monitor reports dependency status accurately.
- No evidence of unbounded memory growth or disk usage during typical operation.

## 9. Automated Testing and Regression Prevention

### Goals
- Create or improve tests for verified critical execution paths.
- Prioritize:
  1. Application startup and readiness.
  2. Configuration validation.
  3. API contracts.
  4. Dashboard data fetching.
  5. Provider request and error handling.
  6. Workflow dispatch.
  7. Executive routing.
  8. Memory persistence.
  9. Voice pipeline integration (where testable).
  10. Graceful shutdown and recovery.
- Use unit tests for isolated logic and integration tests for actual component boundaries.
- Accept that mocks are acceptable for isolated unit tests but must not be presented as evidence that external services, hardware, credentials, or real end‑to‑end integrations work.
- Add regression tests for defects discovered during this engagement.
- Avoid disabling existing tests, weakening assertions, or broadening skip conditions simply to obtain a green test suite.

### Activities
- Review existing test files in `tests/` and `backend/` (if any) to understand current coverage.
- Add unit tests for:
  - Configuration validation (e.g., `test_config_validation.py`).
  - Provider registry initialization and model selection.
  - Workflow YAML parsing and validation.
  - Memory read/write and scoping.
  - Voice pipeline initialization (mock microphone input).
- Add integration tests for:
  - API endpoint `/status` and `/health` (requires a running backend).
  - Workflow dispatch from trigger to completion (using a simple test workflow).
  - Dashboard proxy to backend (requires both backend and frontend).
  - Voice pipeline wake‑word detection (requires audio mocking).
- Ensure that tests are isolated and clean up after themselves (e.g., temporary directories, database files).
- Use pytest fixtures to set up and tear down the backend state.
- For frontend, consider using Jest or React Testing Library for component unit tests.
- Integrate tests into a CI‑like workflow (local script) that can be run before committing changes.

### Acceptance Criteria
- New tests pass and catch regressions.
- Existing test suite continues to pass (no new failures introduced).
- Coverage of critical paths increases.
- Tests are fast enough to run frequently during development.
- Test reports are clear and actionable.

## 10. Production‑Readiness Verification

### Goals
- Before declaring the system production‑ready, execute a documented verification process.
- Establish:
  - Reproducible dependency installation.
  - Successful backend startup.
  - Truthful liveness and readiness responses.
  - Successful frontend production build.
  - Correct API connectivity.
  - Correct primary route behavior.
  - Valid configuration handling.
  - No newly introduced test failures.
  - Verified critical execution paths.
  - Correct authentication and authorization boundaries where applicable.
  - Safe secret handling.
  - Appropriate timeout and retry behavior.
  - Database integrity protections.
  - Graceful startup failure and shutdown behavior.
  - Documented operational procedures.
  - Documented unresolved risks and external dependencies.
- Classify the final status accurately:
  - **Verified** – Tested successfully under stated conditions.
  - **Partially verified** – Some behavior works, but important conditions remain untested.
  - **Blocked** – Verification requires unavailable credentials, hardware, services, or permissions.
  - **Failing** – The relevant test was executed and did not pass.

### Activities
- Create a verification checklist that includes all the above items.
- Perform the checks in a controlled environment (e.g., a temporary copy of the repository with test credentials if needed).
- Document each step, the commands used, the output, and whether it passed or failed.
- Collect logs, screenshots, and any relevant artifacts.
- At the conclusion, produce a final production‑readiness assessment report that summarizes the evidence, limitations, and remaining blockers.
- If the system is not fully ready, identify the highest‑priority items to address in a future iteration.

### Acceptance Criteria
- The verification process is transparent and repeatable.
- The final status is justified by empirical evidence.
- Any remaining blockers are clearly documented and have mitigation plans (if applicable).
- The system does not claim production readiness without sufficient verification.

## Conclusion

This repair plan outlines a systematic approach to address the areas identified during Phase 1. Each goal is concrete, verifiable, and aligned with making AXIOM AI OS reliable, secure, and ready for production use. Progress will be tracked through incremental validation, and the plan will be adjusted as new information is discovered.
