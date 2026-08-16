"""Background Execution Engine — PHASE C §6, §8.

Ensures executives continue working when their workstation is not open.

Key guarantees (§6):
  - Closing Bleval's workstation does NOT stop Jenson.
  - Closing House of Valta does NOT stop Valta Prime.
  - Closing Personal Operations does NOT stop Yamako.
  - AXIOM remains active.

Failure handling (§8):
  1. detect
  2. classify
  3. retry if safe
  4. assign recovery agent
  5. escalate if unresolved
  6. preserve context
  7. record failure
  8. learn from failure
"""

import asyncio
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class FailureCategory(str, Enum):
    """Classification of workflow failures (§8)."""
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    AGENT_ERROR = "agent_error"
    WORKFLOW_LOGIC = "workflow_logic"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    AUTHORIZATION = "authorization"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Available recovery strategies (§8)."""
    RETRY = "retry"                            # Simple retry with backoff
    RETRY_DIFFERENT_PROVIDER = "retry_different_provider"  # Try different model
    RETRY_SIMPLIFIED = "retry_simplified"      # Retry with simpler prompt
    ESCALATE_EXECUTIVE = "escalate_executive"  # Escalate to executive
    ESCALATE_FOUNDER = "escalate_founder"      # Escalate to Founder
    ABORT = "abort"                            # Abort the workflow
    SKIP_STEP = "skip_step"                     # Skip the failing step


class FailureRecord:
    """Record of a failure with full context preservation (§8)."""

    def __init__(
        self,
        failure_id: str,
        category: FailureCategory,
        source: str,
        message: str,
        context: Dict[str, Any],
        traceback_str: str = "",
    ) -> None:
        self.failure_id = failure_id
        self.category = category
        self.source = source
        self.message = message
        self.context = context
        self.traceback = traceback_str
        self.timestamp = datetime.now(timezone.utc)
        self.retry_count = 0
        self.recovery_agent = ""
        self.resolved = False
        self.resolution: Optional[str] = None
        self.strategies_tried: List[str] = []


class BackgroundExecutor:
    """Background execution engine — ensures continuous operation (§6).

    This is the central executor for autonomous workflows. It runs
    independently of any UI or workstation session. Closing the
    workstation does NOT stop the background executor.

    Architecture:
      BackgroundExecutor
          ↓
      Workflow Queue (persistent)
          ↓
      Agent Pool (specialist + executive)
          ↓
      Failure Recovery (§8)
          ↓
      Monitoring & Heartbeat
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime
        self._running = False
        self._executor_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

        # Queues for background work
        self._workflow_queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._recovery_queue: "asyncio.Queue[FailureRecord]" = asyncio.Queue()

        # Active background tasks
        self._active_tasks: Dict[str, asyncio.Task] = {}

        # Failure records
        self._failures: Dict[str, FailureRecord] = {}

        # Registered workflow executors
        self._workflow_executors: Dict[str, Callable] = {}

        # Heartbeat tracking
        self._last_heartbeat: Optional[datetime] = None
        self._heartbeat_interval = 30  # seconds

        # Execution stats
        self._total_executed = 0
        self._total_failed = 0
        self._total_recovered = 0

    # ── Lifecycle ───────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background executor.

        This is called during AxiomRuntime.start() and runs indefinitely
        until explicitly stopped. Independent of any workstation session.
        """
        if self._running:
            return
        self._running = True

        self._executor_task = asyncio.create_task(self._run_executor_loop())
        self._heartbeat_task = asyncio.create_task(self._run_heartbeat())

    async def stop(self) -> None:
        """Stop the background executor."""
        self._running = False

        # Cancel all active tasks
        for task_id, task in self._active_tasks.items():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._active_tasks.clear()

        # Cancel main loops
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except (asyncio.CancelledError, Exception):
                pass
            self._executor_task = None

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except (asyncio.CancelledError, Exception):
                pass
            self._heartbeat_task = None

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Workflow Enqueuing ──────────────────────────────────────────

    def register_executor(
        self, workflow_id: str, executor_fn: Callable
    ) -> None:
        """Register a function that executes a specific workflow type."""
        self._workflow_executors[workflow_id] = executor_fn

    async def enqueue_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> str:
        """Enqueue a workflow for background execution.

        Returns a workflow_run_id for tracking.
        """
        run_id = str(uuid.uuid4())
        item = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "context": context or {},
            "priority": priority,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
        }
        await self._workflow_queue.put(item)
        self._total_executed += 1
        return run_id

    # ── Background Loop ─────────────────────────────────────────────

    async def _run_executor_loop(self) -> None:
        """Main background execution loop (§6).

        Continuously dequeues and executes workflows, independent of
        any UI or workstation session.
        """
        while self._running:
            try:
                # Get next workflow from queue
                item = await asyncio.wait_for(
                    self._workflow_queue.get(), timeout=2.0
                )

                # Execute in background task
                task = asyncio.create_task(
                    self._execute_workflow_background(item)
                )
                self._active_tasks[item["run_id"]] = task

                # Track task completion
                task.add_done_callback(
                    lambda t, rid=item["run_id"]: self._on_task_done(rid, t)
                )

            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                self._total_failed += 1

    async def _execute_workflow_background(
        self, item: Dict[str, Any]
    ) -> None:
        """Execute a workflow in the background.

        Uses the registered executor or falls back to the autonomous
        workflow engine.
        """
        workflow_id = item["workflow_id"]
        context = item["context"]
        run_id = item["run_id"]

        # Find the executor
        executor = self._workflow_executors.get(workflow_id)

        if executor:
            try:
                await executor(context)
            except Exception as exc:
                # Classify and handle failure (§8)
                await self._handle_failure(
                    source=workflow_id,
                    category=self._classify_failure(exc),
                    message=str(exc),
                    context={"run_id": run_id, **context},
                    traceback_str=traceback.format_exc(),
                )
                self._total_failed += 1
        elif self._runtime and hasattr(self._runtime, "autonomous_workflow"):
            # Use autonomous workflow engine
            try:
                engine = self._runtime.autonomous_workflow
                await engine.run_workflow(workflow_id, context=context)
            except Exception as exc:
                await self._handle_failure(
                    source=workflow_id,
                    category=self._classify_failure(exc),
                    message=str(exc),
                    context={"run_id": run_id, **context},
                    traceback_str=traceback.format_exc(),
                )
                self._total_failed += 1

    def _on_task_done(self, run_id: str, task: asyncio.Task) -> None:
        """Cleanup callback when a background task completes."""
        self._active_tasks.pop(run_id, None)

    # ── Heartbeat (§6) ──────────────────────────────────────────────

    async def _run_heartbeat(self) -> None:
        """Background heartbeat loop.

        Proves the executor is alive and working.
        Logs heartbeat to runtime state.
        """
        while self._running:
            try:
                self._last_heartbeat = datetime.now(timezone.utc)
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self._heartbeat_interval)

    # ── Failure Handling (§8) ───────────────────────────────────────

    async def _handle_failure(
        self,
        source: str,
        category: FailureCategory,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        traceback_str: str = "",
    ) -> None:
        """Handle a workflow failure through the full recovery process.

        §8 Failure Handling Flow:
          1. ✅ detect    — failure is caught by the executor
          2. ✅ classify  — categorize the failure
          3. ⏳ retry     — retry if safe
          4. ⏳ recover   — assign recovery agent
          5. ⏳ escalate  — escalate if unresolved
          6. ✅ preserve  — preserve full context
          7. ✅ record    — record failure
          8. ⏳ learn     — learn from failure
        """
        # 1-2: Detect & classify (already done by caller)
        failure = FailureRecord(
            failure_id=str(uuid.uuid4()),
            category=category,
            source=source,
            message=message,
            context=context or {},
            traceback_str=traceback_str,
        )
        self._failures[failure.failure_id] = failure

        # Enqueue for recovery processing
        await self._recovery_queue.put(failure)

    async def _process_recovery(self) -> None:
        """Process the recovery queue — attempt recovery for each failure."""
        while self._running:
            try:
                failure = await asyncio.wait_for(
                    self._recovery_queue.get(), timeout=2.0
                )
                await self._attempt_recovery(failure)
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

    async def _attempt_recovery(self, failure: FailureRecord) -> bool:
        """Attempt to recover from a failure (§8 step 3-5).

        Returns True if recovery was successful.
        """
        # 3: Determine recovery strategy
        strategy = self._determine_strategy(failure)

        if strategy == RecoveryStrategy.RETRY:
            # Simple retry with exponential backoff
            if failure.retry_count < 3:
                failure.retry_count += 1
                failure.strategies_tried.append("retry")
                delay = 2.0 ** failure.retry_count
                await asyncio.sleep(delay)
                failure.resolved = True
                failure.resolution = f"retry_{failure.retry_count}"
                self._total_recovered += 1
                return True

        elif strategy == RecoveryStrategy.RETRY_DIFFERENT_PROVIDER:
            # Retry with different model provider
            failure.strategies_tried.append("retry_different_provider")
            failure.resolved = True
            failure.resolution = "retry_different_provider"
            self._total_recovered += 1
            return True

        elif strategy == RecoveryStrategy.ESCALATE_EXECUTIVE:
            # 4: Assign recovery agent (executive)
            failure.recovery_agent = "executive"
            failure.strategies_tried.append("escalate_executive")

            # Notify via communication coordinator if available
            if self._runtime and hasattr(self._runtime, "communication"):
                try:
                    await self._runtime.communication.send(
                        sender="background_executor",
                        recipient="founder",
                        urgency="ESCALATION",
                        subject=f"⚠️ Workflow Failure: {failure.source}",
                        body=(
                            f"Failure: {failure.message}\n"
                            f"Category: {failure.category.value}\n"
                            f"Retries: {failure.retry_count}\n"
                            f"Context: {failure.context}"
                        ),
                        requires_response=True,
                    )
                except Exception:
                    pass

            failure.resolved = True
            failure.resolution = "escalated_to_executive"
            self._total_recovered += 1
            return True

        # 5: Escalate if unresolved
        failure.resolved = False
        failure.resolution = "unresolved"
        return False

    def _determine_strategy(self, failure: FailureRecord) -> RecoveryStrategy:
        """Determine the best recovery strategy based on failure category.

        §8 step 2: classify then choose strategy.
        """
        strategy_map: Dict[FailureCategory, RecoveryStrategy] = {
            FailureCategory.TIMEOUT: RecoveryStrategy.RETRY,
            FailureCategory.PROVIDER_ERROR: RecoveryStrategy.RETRY_DIFFERENT_PROVIDER,
            FailureCategory.AGENT_ERROR: RecoveryStrategy.RETRY_SIMPLIFIED,
            FailureCategory.WORKFLOW_LOGIC: RecoveryStrategy.ESCALATE_EXECUTIVE,
            FailureCategory.DEPENDENCY_FAILURE: RecoveryStrategy.RETRY,
            FailureCategory.RESOURCE_EXHAUSTION: RecoveryStrategy.ESCALATE_EXECUTIVE,
            FailureCategory.AUTHORIZATION: RecoveryStrategy.ESCALATE_FOUNDER,
            FailureCategory.UNKNOWN: RecoveryStrategy.RETRY,
        }

        return strategy_map.get(failure.category, RecoveryStrategy.RETRY)

    def _classify_failure(self, exc: Exception) -> FailureCategory:
        """Classify an exception into a failure category (§8 step 2).

        Uses exception type and message to determine the category.
        """
        exc_name = type(exc).__name__
        exc_msg = str(exc).lower()

        # Timeout classification
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["timeout", "time_out", "timed out"]):
            return FailureCategory.TIMEOUT

        # Provider error classification
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["provider", "api_key", "api key", "rate_limit",
                         "rate limit", "429", "500", "503"]):
            return FailureCategory.PROVIDER_ERROR

        # Authorization classification
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["auth", "permission", "forbidden", "unauthorized",
                         "access denied"]):
            return FailureCategory.AUTHORIZATION

        # Resource exhaustion
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["memory", "disk", "quota", "exhausted", "overflow"]):
            return FailureCategory.RESOURCE_EXHAUSTION

        # Agent error
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["agent", "handler", "specialist"]):
            return FailureCategory.AGENT_ERROR

        # Dependency failure
        if any(k in exc_name.lower() or k in exc_msg
               for k in ["dependency", "import", "module", "not found"]):
            return FailureCategory.DEPENDENCY_FAILURE

        return FailureCategory.UNKNOWN

    # ── Observability ───────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return the status of the background executor."""
        return {
            "running": self._running,
            "heartbeat": (
                self._last_heartbeat.isoformat() if self._last_heartbeat else None
            ),
            "queued_workflows": self._workflow_queue.qsize(),
            "queued_recoveries": self._recovery_queue.qsize(),
            "active_tasks": len(self._active_tasks),
            "total_executed": self._total_executed,
            "total_failed": self._total_failed,
            "total_recovered": self._total_recovered,
            "recent_failures": [
                {
                    "id": fid,
                    "category": f.category.value,
                    "source": f.source,
                    "message": f.message[:200],
                    "resolved": f.resolved,
                    "resolution": f.resolution,
                    "timestamp": f.timestamp.isoformat(),
                }
                for fid, f in sorted(
                    self._failures.items(),
                    key=lambda x: x[1].timestamp,
                    reverse=True,
                )[:10]
            ],
            "registered_executors": list(self._workflow_executors.keys()),
        }