"""Pydantic models for the workflow state machine.

These are runtime models — they represent the state of a running workflow
instance, not the static configuration from YAML files.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStepState(BaseModel):
    """Runtime state of a single workflow step."""
    step_id: str
    step_name: str = ""
    agent: str = ""
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    events_emitted: List[str] = []
    retry_count: int = 0
    error: Optional[str] = None


class WorkflowInstance(BaseModel):
    """Runtime state of a single workflow execution."""
    workflow_id: str
    instance_id: str
    org: str = ""
    department: str = ""
    coordinator: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStepState] = []
    current_step_index: int = 0
    context: Dict[str, Any] = {}
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    error: Optional[str] = None
    version: str = "3.0"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    """A request for human (or executive) approval during a workflow."""
    approval_id: str
    workflow_instance_id: str
    step_id: str = ""
    step_name: str = ""
    requested_by: str = ""
    requested_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None