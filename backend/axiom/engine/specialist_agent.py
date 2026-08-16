"""Specialist Agent Engine — registry, factory, and runtime for specialist agents.

PHASE C §3: Specialist Agents

Specialist agents are the skilled workforce in Axiom OS.
Each specialist type is specialized rather than generic:

  Research, Market Intelligence, Content Writer, Content Research,
  Image, Video, Audio, SEO, Lead Research, Outreach, CRM,
  Development, Testing, Documentation, Trading Research, Calendar,
  Learning, Monitoring, QC

Architecture:
  AXIOM
    ↓
  Executive (manages)
    ↓
  Specialist Agent (performs)
    ↓
  Intelligence + Tool Engines

Agents are discoverable through the existing capability/tool architecture.
"""

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from axiom.engine.base import ModelProvider
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.tool import ToolEngine
from axiom.models.agent_specialist import (
    AgentSession,
    SpecialistCapability,
    SpecialistOutput,
    SpecialistRegistry,
    SpecialistTask,
    SpecialistType,
)


# ── Agent Handler Registry ─────────────────────────────────────────────

class AgentHandler:
    """Base class for a specialist agent handler.

    Each specialist type can optionally register a custom handler
    that processes tasks in a specialized way. If no handler is
    registered, the generic intelligence-based handler is used.
    """

    specialist_type: SpecialistType = SpecialistType.CUSTOM

    async def handle(
        self,
        task: SpecialistTask,
        intelligence: Any,
        tool_engine: Any,
    ) -> SpecialistOutput:
        """Process a specialist task and return output.

        Override this in subclasses for custom handling.
        """
        raise NotImplementedError


# ── Specialist Agent Engine ────────────────────────────────────────────


class SpecialistAgentEngine:
    """Manages specialist agent lifecycle: registration, dispatch, sessions.

    This is the central coordinator for all specialist agents.
    It connects to the IntelligenceEngine for reasoning and the
    ToolEngine for tool access — every specialist uses the same
    abstraction layer (Architecture Law 9).
    """

    def __init__(
        self,
        intelligence: Optional[IntelligenceEngine] = None,
        tool: Optional[ToolEngine] = None,
    ) -> None:
        self._intelligence = intelligence
        self._tool = tool
        self._registry = SpecialistRegistry()

        # Active sessions: agent_id -> AgentSession
        self._sessions: Dict[str, AgentSession] = {}

        # Task queue per specialist type
        self._task_queues: Dict[str, "asyncio.Queue[SpecialistTask]"] = {}
        self._tasks: Dict[str, SpecialistTask] = {}

        # Custom handlers: specialist_type -> AgentHandler
        self._handlers: Dict[str, AgentHandler] = {}

        # Background task processors
        self._processors: Dict[str, asyncio.Task] = {}
        self._running = False

    # ── Registration ──────────────────────────────────────────────────

    def register_handler(
        self, specialist_type: SpecialistType, handler: AgentHandler
    ) -> None:
        """Register a custom handler for a specialist type."""
        self._handlers[specialist_type.value] = handler

    def register_handlers(
        self, handlers: Dict[SpecialistType, AgentHandler]
    ) -> None:
        """Register multiple handlers at once."""
        for st, handler in handlers.items():
            self.register_handler(st, handler)

    def get_handler(self, specialist_type: SpecialistType) -> Optional[AgentHandler]:
        """Get the handler for a specialist type."""
        return self._handlers.get(specialist_type.value)

    def list_specialist_types(self) -> List[Dict[str, Any]]:
        """Return all registered specialist types."""
        return [
            {
                "type": st.value,
                "has_custom_handler": st.value in self._handlers,
                "active_sessions": sum(
                    1 for s in self._sessions.values()
                    if s.specialist_type == st and s.status == "busy"
                ),
            }
            for st in SpecialistType
        ]

    # ── Session Management ───────────────────────────────────────────

    def create_session(
        self,
        agent_id: str,
        specialist_type: SpecialistType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:
        """Create a new session for a specialist agent."""
        now = datetime.now(timezone.utc)
        session = AgentSession(
            session_id=str(uuid.uuid4()),
            agent_id=agent_id,
            specialist_type=specialist_type,
            status="idle",
            started_at=now,
            last_activity=now,
            metadata=metadata or {},
        )
        self._sessions[agent_id] = session

        # Ensure task queue exists for this type
        st_key = specialist_type.value
        if st_key not in self._task_queues:
            self._task_queues[st_key] = asyncio.Queue()

        return session

    def get_session(self, agent_id: str) -> Optional[AgentSession]:
        """Get an active session."""
        return self._sessions.get(agent_id)

    def list_sessions(
        self,
        specialist_type: Optional[SpecialistType] = None,
        status: Optional[str] = None,
    ) -> List[AgentSession]:
        """List active sessions, optionally filtered."""
        sessions = list(self._sessions.values())
        if specialist_type:
            sessions = [s for s in sessions if s.specialist_type == specialist_type]
        if status:
            sessions = [s for s in sessions if s.status == status]
        return sessions

    def end_session(self, agent_id: str) -> bool:
        """End a specialist session."""
        session = self._sessions.pop(agent_id, None)
        return session is not None

    # ── Task Dispatch ────────────────────────────────────────────────

    async def dispatch_task(
        self,
        agent_id: str,
        specialist_type: SpecialistType,
        instruction: str,
        workflow_instance_id: str = "",
        step_id: str = "",
        context: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> str:
        """Dispatch a task to a specialist agent.

        Returns the task_id.
        """
        now = datetime.now(timezone.utc)
        task = SpecialistTask(
            task_id=str(uuid.uuid4()),
            specialist_type=specialist_type,
            agent_id=agent_id,
            workflow_instance_id=workflow_instance_id,
            step_id=step_id,
            instruction=instruction,
            context=context or {},
            inputs=inputs or {},
            status="pending",
            created_at=now,
            priority=priority,
        )
        self._tasks[task.task_id] = task

        # Enqueue for processing
        st_key = specialist_type.value
        if st_key not in self._task_queues:
            self._task_queues[st_key] = asyncio.Queue()
        await self._task_queues[st_key].put(task)

        # Update session state
        session = self._sessions.get(agent_id)
        if session:
            session.status = "busy"
            session.current_task = task.task_id
            session.last_activity = now

        return task.task_id

    def get_task(self, task_id: str) -> Optional[SpecialistTask]:
        """Get a task by id."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        specialist_type: Optional[SpecialistType] = None,
        status: Optional[str] = None,
        workflow_instance_id: Optional[str] = None,
    ) -> List[SpecialistTask]:
        """List tasks, optionally filtered."""
        tasks = list(self._tasks.values())
        if specialist_type:
            tasks = [t for t in tasks if t.specialist_type == specialist_type]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if workflow_instance_id:
            tasks = [t for t in tasks if t.workflow_instance_id == workflow_instance_id]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    # ── Background Processing ────────────────────────────────────────

    async def start(self) -> None:
        """Start background processors for each specialist type."""
        if self._running:
            return
        self._running = True

        for st_key in self._task_queues:
            self._processors[st_key] = asyncio.create_task(
                self._process_queue(st_key)
            )

        # Create a default processor for unregistered types
        if not self._processors:
            for st in SpecialistType:
                st_key = st.value
                if st_key not in self._task_queues:
                    self._task_queues[st_key] = asyncio.Queue()
                self._processors[st_key] = asyncio.create_task(
                    self._process_queue(st_key)
                )

    async def stop(self) -> None:
        """Stop all background processors."""
        self._running = False
        for st_key, processor in self._processors.items():
            processor.cancel()
            try:
                await processor
            except asyncio.CancelledError:
                pass
        self._processors.clear()

    async def _process_queue(self, specialist_type_key: str) -> None:
        """Background loop: process tasks for a specialist type."""
        queue = self._task_queues.get(specialist_type_key)
        if not queue:
            return

        while self._running:
            try:
                task = await asyncio.wait_for(queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

    async def _execute_task(self, task: SpecialistTask) -> None:
        """Execute a specialist task using either custom handler or intelligence."""
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)

        try:
            st = task.specialist_type
            handler = self._handlers.get(st.value)

            if handler:
                # Custom handler — specialist-specific logic
                output = await handler.handle(
                    task=task,
                    intelligence=self._intelligence,
                    tool_engine=self._tool,
                )
            elif self._intelligence:
                # Generic intelligence-based handling
                output = await self._intelligence_handle(task)
            else:
                # Fallback: no intelligence engine
                output = SpecialistOutput(
                    output_id=str(uuid.uuid4()),
                    specialist_type=st.value,
                    task_id=task.task_id,
                    workflow_instance_id=task.workflow_instance_id,
                    content={"message": "No intelligence engine available"},
                    metadata={"fallback": True},
                    created_at=datetime.now(timezone.utc),
                )

            task.output = output
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)

            # Update session
            session = self._sessions.get(task.agent_id)
            if session:
                session.status = "idle"
                session.current_task = None
                session.tasks_completed += 1
                session.last_activity = datetime.now(timezone.utc)

        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            task.completed_at = datetime.now(timezone.utc)

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"
                task.started_at = None
                task.completed_at = None
                await asyncio.sleep(2.0 ** task.retry_count)

                st_key = task.specialist_type.value
                if st_key in self._task_queues:
                    await self._task_queues[st_key].put(task)
            else:
                # Update session
                session = self._sessions.get(task.agent_id)
                if session:
                    session.status = "idle"
                    session.current_task = None
                    session.tasks_failed += 1
                    session.last_activity = datetime.now(timezone.utc)

    async def _intelligence_handle(
        self, task: SpecialistTask
    ) -> SpecialistOutput:
        """Handle a task using the intelligence engine."""
        if not self._intelligence:
            raise RuntimeError("Intelligence engine not available")

        # Build a specialist-specific system prompt
        system_prompt = (
            f"You are a {task.specialist_type.value} specialist in the Axiom OS platform.\n"
            f"Your role is to perform specialized work autonomously.\n"
            f"Produce high-quality, actionable output."
        )

        # Build the full instruction with context
        prompt_parts = [f"## INSTRUCTION\n{task.instruction}"]

        if task.context:
            ctx_lines = "\n".join(
                f"{k}: {v}" for k, v in task.context.items()
            )
            prompt_parts.append(f"## CONTEXT\n{ctx_lines}")

        if task.inputs:
            inp_lines = "\n".join(
                f"{k}: {v}" for k, v in task.inputs.items()
            )
            prompt_parts.append(f"## INPUTS\n{inp_lines}")

        prompt = "\n\n---\n\n".join(prompt_parts)

        # Route through the intelligence engine
        result = await self._intelligence.generate(
            agent_id=task.agent_id,
            task_description=prompt,
            org_id=task.context.get("org_id", ""),
            dept_id=task.context.get("dept_id", ""),
            additional_context={
                "specialist_type": task.specialist_type.value,
                "workflow_instance_id": task.workflow_instance_id,
            },
        )

        return SpecialistOutput(
            output_id=str(uuid.uuid4()),
            specialist_type=task.specialist_type.value,
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            content={"result": result},
            metadata={"provider": "intelligence_engine"},
            created_at=datetime.now(timezone.utc),
        )

    # ── Summary ─────────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the specialist agent engine state."""
        sessions = self.list_sessions()
        tasks = self.list_tasks()

        return {
            "total_specialist_types": len(SpecialistType),
            "custom_handlers": len(self._handlers),
            "active_sessions": len([s for s in sessions if s.status == "busy"]),
            "idle_sessions": len([s for s in sessions if s.status == "idle"]),
            "total_tasks_created": len(tasks),
            "completed_tasks": len([t for t in tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in tasks if t.status == "failed"]),
            "pending_tasks": len([t for t in tasks if t.status == "pending"]),
            "running": self._running,
        }