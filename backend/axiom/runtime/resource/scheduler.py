"""Resource Scheduler — Task scheduling with priority and resource awareness."""

import asyncio
import heapq
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from pydantic import BaseModel, Field

from axiom.runtime.resource.monitor import ResourceMonitor, ResourceMetrics
from axiom.runtime.logging import RuntimeLogger


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ScheduledTask(BaseModel):
    """Scheduled task definition."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    coro: Optional[Callable[..., Awaitable]] = None  # Not serialized
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING

    # Scheduling
    scheduled_for: Optional[datetime] = None
    recurring: bool = False
    interval: Optional[timedelta] = None
    cron: Optional[str] = None  # cron expression

    # Resource requirements
    min_cpu_percent: float = 0.0
    min_memory_percent: float = 0.0
    max_cpu_percent: float = 100.0
    max_memory_percent: float = 100.0
    requires_gpu: bool = False

    # Execution
    max_retries: int = 3
    retry_delay: timedelta = Field(default_factory=lambda: timedelta(seconds=60))
    timeout: Optional[timedelta] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Runtime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    last_error: Optional[str] = None
    result: Any = None

    def __lt__(self, other: "ScheduledTask") -> bool:
        """Priority queue ordering."""
        # Higher priority first, then earlier scheduled time
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3,
        }
        self_prio = priority_order.get(self.priority, 2)
        other_prio = priority_order.get(other.priority, 2)

        if self_prio != other_prio:
            return self_prio < other_prio

        if self.scheduled_for and other.scheduled_for:
            return self.scheduled_for < other.scheduled_for
        elif self.scheduled_for:
            return True
        elif other.scheduled_for:
            return False

        return self.created_at < other.created_at


class ResourceScheduler:
    """Resource-aware task scheduler."""

    def __init__(
        self,
        monitor: ResourceMonitor,
        max_concurrent: int = 10,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.monitor = monitor
        self.max_concurrent = max_concurrent
        self.logger = logger or RuntimeLogger()

        self._queue: List[ScheduledTask] = []
        self._running: Dict[str, ScheduledTask] = {}
        self._completed: Dict[str, ScheduledTask] = {}
        self._running_count = 0
        self._task_semaphore: Optional[asyncio.Semaphore] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running_flag = False

        # Callbacks
        self._on_task_start: List[Callable[[ScheduledTask], Any]] = []
        self._on_task_complete: List[Callable[[ScheduledTask], Any]] = []
        self._on_task_failed: List[Callable[[ScheduledTask, Exception], Any]] = []

    def on_task_start(self, callback: Callable[[ScheduledTask], Any]):
        self._on_task_start.append(callback)

    def on_task_complete(self, callback: Callable[[ScheduledTask], Any]):
        self._on_task_complete.append(callback)

    def on_task_failed(self, callback: Callable[[ScheduledTask, Exception], Any]):
        self._on_task_failed.append(callback)

    async def start(self):
        """Start scheduler."""
        if self._running_flag:
            return
        self._running_flag = True
        self._task_semaphore = asyncio.Semaphore(self.max_concurrent)
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("resource_scheduler", "Resource scheduler started")

    async def stop(self, wait: bool = True):
        """Stop scheduler."""
        self._running_flag = False

        if wait and self._running:
            self.logger.info("resource_scheduler", f"Waiting for {len(self._running)} running tasks...")
            while self._running:
                await asyncio.sleep(1)

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        self.logger.info("resource_scheduler", "Resource scheduler stopped")

    def schedule(self, task: ScheduledTask) -> str:
        """Schedule a task."""
        # Set scheduled_for if not set
        if task.scheduled_for is None:
            task.scheduled_for = datetime.utcnow()

        heapq.heappush(self._queue, task)
        task.status = TaskStatus.QUEUED
        self.logger.debug("resource_scheduler", f"Scheduled task: {task.name} ({task.id})")
        return task.id

    def schedule_coro(
        self,
        name: str,
        coro: Callable[..., Awaitable],
        priority: TaskPriority = TaskPriority.NORMAL,
        scheduled_for: Optional[datetime] = None,
        interval: Optional[timedelta] = None,
        **kwargs
    ) -> str:
        """Schedule a coroutine."""
        task = ScheduledTask(
            name=name,
            coro=coro,
            priority=priority,
            scheduled_for=scheduled_for,
            recurring=interval is not None,
            interval=interval,
            **kwargs
        )
        return self.schedule(task)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        # Check queue
        for i, task in enumerate(self._queue):
            if task.id == task_id:
                task.status = TaskStatus.CANCELLED
                self._queue.pop(i)
                heapq.heapify(self._queue)
                return True

        # Check running
        if task_id in self._running:
            task = self._running[task_id]
            task.status = TaskStatus.CANCELLED
            # Would need to cancel the actual coroutine
            return True

        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID."""
        for task in self._queue:
            if task.id == task_id:
                return task
        if task_id in self._running:
            return self._running[task_id]
        return self._completed.get(task_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "queued": len(self._queue),
            "running": len(self._running),
            "completed": len(self._completed),
            "max_concurrent": self.max_concurrent,
            "available_slots": self.max_concurrent - len(self._running),
        }

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running_flag:
            try:
                # Check if we can run more tasks
                if len(self._running) >= self.max_concurrent:
                    await asyncio.sleep(1)
                    continue

                # Get next eligible task
                task = self._get_next_task()
                if not task:
                    await asyncio.sleep(1)
                    continue

                # Check resource constraints
                if not await self._check_resources(task):
                    # Re-queue with slight delay
                    task.scheduled_for = datetime.utcnow() + timedelta(seconds=10)
                    heapq.heappush(self._queue, task)
                    await asyncio.sleep(1)
                    continue

                # Execute task
                asyncio.create_task(self._execute_task(task))

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("resource_scheduler", f"Scheduler loop error: {e}")
                await asyncio.sleep(1)

    def _get_next_task(self) -> Optional[ScheduledTask]:
        """Get next eligible task from queue."""
        now = datetime.utcnow()

        # Find first task that's ready to run
        temp = []
        while self._queue:
            task = heapq.heappop(self._queue)
            if task.status == TaskStatus.CANCELLED:
                continue

            if task.scheduled_for and task.scheduled_for > now:
                # Not ready yet, put back
                temp.append(task)
                break

            # Ready to run
            for t in temp:
                heapq.heappush(self._queue, t)
            return task

        # Put back any we popped
        for t in temp:
            heapq.heappush(self._queue, t)

        return None

    async def _check_resources(self, task: ScheduledTask) -> bool:
        """Check if resources are available for task."""
        metrics = self.monitor.get_current()
        if not metrics:
            return True  # No metrics, assume OK

        # Check CPU
        if metrics.cpu_percent > task.max_cpu_percent:
            return False
        if metrics.cpu_percent < task.min_cpu_percent:
            return False

        # Check memory
        if metrics.memory_percent > task.max_memory_percent:
            return False
        if metrics.memory_percent < task.min_memory_percent:
            return False

        # Check GPU
        if task.requires_gpu and not metrics.gpu_available:
            return False

        return True

    async def _execute_task(self, task: ScheduledTask):
        """Execute a task."""
        if not task.coro:
            self.logger.error("resource_scheduler", f"Task {task.id} has no coroutine")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.last_error = "No coroutine"
            return

        async with self._task_semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            self._running[task.id] = task

            self.logger.info("resource_scheduler", f"Starting task: {task.name} ({task.id})")
            for cb in self._on_task_start:
                try:
                    cb(task)
                except Exception:
                    pass

            try:
                # Execute with timeout
                if task.timeout:
                    result = await asyncio.wait_for(task.coro(), timeout=task.timeout.total_seconds())
                else:
                    result = await task.coro()

                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()

                self.logger.info("resource_scheduler", f"Task completed: {task.name} ({task.id})")

            except asyncio.TimeoutError:
                task.status = TaskStatus.FAILED
                task.last_error = "Timeout"
                self.logger.error("resource_scheduler", f"Task timeout: {task.name} ({task.id})")

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.last_error = str(e)
                self.logger.error("resource_scheduler", f"Task failed: {task.name} ({task.id}): {e}")

                # Retry logic
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING
                    self.logger.info("resource_scheduler", f"Retrying task {task.name} (attempt {task.retry_count}/{task.max_retries})")
                    await asyncio.sleep(task.retry_delay.total_seconds())
                    task.scheduled_for = datetime.utcnow()
                    heapq.heappush(self._queue, task)
                    del self._running[task.id]
                    for cb in self._on_task_failed:
                        try:
                            cb(task, e)
                        except Exception:
                            pass
                    return

                for cb in self._on_task_failed:
                    try:
                        cb(task, e)
                    except Exception:
                        pass

            else:
                for cb in self._on_task_complete:
                    try:
                        cb(task)
                    except Exception:
                        pass

            finally:
                self._completed[task.id] = task
                del self._running[task.id]

    def get_recent_completed(self, limit: int = 50) -> List[ScheduledTask]:
        """Get recently completed tasks."""
        sorted_tasks = sorted(
            self._completed.values(),
            key=lambda t: t.completed_at or datetime.min,
            reverse=True
        )
        return sorted_tasks[:limit]