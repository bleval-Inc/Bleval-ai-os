"""Pydantic models for the runtime infrastructure.

Task queue items, health checks, and scheduled events.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """A unit of work dispatched to an agent."""
    task_id: str
    workflow_instance_id: str
    step_id: str = ""
    agent_id: str
    action: str = ""
    context: Dict[str, Any] = {}
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    error: Optional[str] = None


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single runtime component."""
    component: str
    status: HealthStatus = HealthStatus.HEALTHY
    last_check: datetime
    details: Dict[str, Any] = {}


class ScheduledEvent(BaseModel):
    """A cron-triggered event that fires on a schedule."""
    schedule_id: str
    event_type: str
    payload: Dict[str, Any] = {}
    cron_expression: str = ""
    next_run: datetime
    workflow_to_trigger: Optional[str] = None
    enabled: bool = True