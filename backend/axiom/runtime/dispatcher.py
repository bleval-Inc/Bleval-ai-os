"""Dispatcher — task queue and agent routing.

The dispatcher receives tasks from the workflow engine and routes them to
the appropriate agent.  It maintains a task queue and tracks execution state.

When a task completes, the dispatcher automatically advances the parent
workflow instance via the workflow engine.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from axiom.models.runtime import Task, TaskStatus


class Dispatcher:
    """Task queuing and agent routing with auto-workflow-advance."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._queue: "asyncio.Queue[Task]" = asyncio.Queue()
        self._tasks: Dict[str, Task] = {}
        self._handlers: Dict[str, Callable] = {}
        self._processor: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the dispatcher background processor."""
        self._running = True
        self._processor = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        """Stop the dispatcher."""
        self._running = False
        if self._processor is not None:
            self._processor.cancel()
            self._processor = None

    def register_handler(self, agent_id: str, handler: Callable) -> None:
        """Register a handler function for a given agent.

        The handler will be called when a task is dispatched to that agent.
        """
        self._handlers[agent_id] = handler

    async def dispatch(
        self,
        agent_id: str,
        action: str,
        workflow_instance_id: str,
        step_id: str = "",
        context: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ) -> str:
        """Create and enqueue a task for an agent.

        Returns the task_id.
        """
        task = Task(
            task_id=str(uuid.uuid4()),
            workflow_instance_id=workflow_instance_id,
            step_id=step_id,
            agent_id=agent_id,
            action=action,
            context=context or {},
            status=TaskStatus.QUEUED,
            priority=priority,
            created_at=datetime.now(timezone.utc),
        )
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by id."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        agent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks, optionally filtered by status or agent."""
        results = list(self._tasks.values())
        if status is not None:
            results = [t for t in results if t.status == status]
        if agent_id is not None:
            results = [t for t in results if t.agent_id == agent_id]
        return results

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued task."""
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.status in (TaskStatus.QUEUED, TaskStatus.PENDING):
            task.status = TaskStatus.CANCELLED
            return True
        return False

    async def _process_queue(self) -> None:
        """Background loop: read tasks from the queue and dispatch them."""
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

    async def _execute_task(self, task: Task) -> None:
        """Execute a single task by calling its agent's handler.

        On completion, auto-advances the parent workflow instance.
        Falls back to recording the task status if no handler is registered.
        """
        task.status = TaskStatus.DISPATCHED
        task.started_at = datetime.now(timezone.utc)

        handler = self._handlers.get(task.agent_id)
        result = None
        if handler is not None:
            try:
                result = await handler(task)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                task.completed_at = datetime.now(timezone.utc)

                # Retry logic with exponential backoff
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.QUEUED
                    delay = 2.0 ** task.retry_count
                    await asyncio.sleep(delay)
                    await self._queue.put(task)
                return
        else:
            # No handler registered — mark as complete (no-op agent)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

        # Auto-advance the parent workflow instance
        await self._auto_advance_workflow(task, result)

    async def _auto_advance_workflow(
        self,
        task: Task,
        step_output: Any = None,
    ) -> None:
        """When a task completes, advance its parent workflow."""
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return
        instance_id = task.workflow_instance_id
        if not instance_id:
            return
        try:
            output = {}
            if step_output is not None:
                output["result"] = (
                    str(step_output)[:500] if not isinstance(step_output, dict)
                    else step_output
                )
            await wf_engine.advance(instance_id, step_output=output)
        except ValueError:
            # Workflow may be in a non-advanceable state (e.g., awaiting approval)
            pass
        except Exception:
            pass