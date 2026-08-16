"""Pydantic models for the autonomous workflow lifecycle (§5).

Every autonomous workflow progresses through a defined lifecycle:

    PLAN → RESEARCH → PREPARE → EXECUTE → TEST → QC → REVIEW → APPROVAL → DELIVERY → LEARN

Not every workflow requires Founder approval.
The approval requirement is determined by the authority policy.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AutonomousLifecyclePhase(str, Enum):
    """The 10 phases of the autonomous workflow lifecycle."""
    PENDING = "pending"
    PLAN = "plan"
    RESEARCH = "research"
    PREPARE = "prepare"
    EXECUTE = "execute"
    TEST = "test"
    QC = "qc"
    REVIEW = "review"
    APPROVAL = "approval"
    DELIVERY = "delivery"
    LEARN = "learn"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuthorityLevel(str, Enum):
    """Determines whether Founder approval is required."""
    FULLY_AUTONOMOUS = "fully_autonomous"  # No approval needed
    EXECUTIVE_APPROVAL = "executive_approval"  # Executive can approve
    FOUNDER_APPROVAL = "founder_approval"  # Founder must approve
    BOARD_APPROVAL = "board_approval"  # Board vote required


class ApprovalPolicy(BaseModel):
    """Policy that determines workflow approval requirements."""
    authority: AuthorityLevel = AuthorityLevel.EXECUTIVE_APPROVAL
    requires_qc: bool = True
    requires_review: bool = True
    auto_approve_on_success: bool = False
    escalation_delay_minutes: int = 0
    allowed_approvers: List[str] = []


class AutonomousWorkflowState(BaseModel):
    """Complete runtime state of an autonomous workflow instance."""
    instance_id: str
    workflow_id: str
    org: str = ""
    department: str = ""
    coordinator: str = ""
    phase: AutonomousLifecyclePhase = AutonomousLifecyclePhase.PENDING

    # Lifecycle phase states (each phase has its own status + data)
    plan_state: Dict[str, Any] = {}
    research_state: Dict[str, Any] = {}
    prepare_state: Dict[str, Any] = {}
    execute_state: Dict[str, Any] = {}
    test_state: Dict[str, Any] = {}
    qc_state: Dict[str, Any] = {}
    review_state: Dict[str, Any] = {}
    approval_state: Dict[str, Any] = {}
    delivery_state: Dict[str, Any] = {}
    learn_state: Dict[str, Any] = {}

    # Execution metadata
    assigned_agents: List[str] = []
    current_agent: str = ""
    duration_seconds: float = 0.0
    progress_percent: float = 0.0

    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retries: int = 0
    max_retries: int = 3

    # Dependencies
    dependencies: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)

    # Context and output
    context: Dict[str, Any] = {}
    output: Dict[str, Any] = {}
    intermediate_outputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Approval tracking
    approval_policy: ApprovalPolicy = ApprovalPolicy()
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # QC tracking
    qc_score: float = 0.0
    qc_passed: Optional[bool] = None
    qc_checked_by: Optional[str] = None

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    phase_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    # Version
    version: str = "3.1"


class AutonomousWorkflowPhaseState(BaseModel):
    """Lightweight phase state for observability."""
    phase: AutonomousLifecyclePhase
    status: str  # pending | in_progress | completed | failed | skipped
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: str = ""
    duration_seconds: float = 0.0
    error: Optional[str] = None
    output_summary: str = ""


class AutonomousWorkflowManifest(BaseModel):
    """Observability manifest for a workflow instance (§7).

    Every workflow exposes:
      state, current_step, assigned_agents, duration, progress,
      errors, retries, output, dependencies, approval_state,
      QC state, history
    """
    instance_id: str
    workflow_id: str
    org: str
    department: str
    coordinator: str = ""
    phase: str
    current_step: str = ""
    assigned_agents: List[str] = []
    duration_seconds: float = 0.0
    progress_percent: float = 0.0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retries: int = 0
    output_summary: str = ""
    dependencies: List[str] = Field(default_factory=list)
    approval_state: str = "not_required"
    qc_state: str = "not_required"
    history: List[AutonomousWorkflowPhaseState] = Field(default_factory=list)
    status: str = "pending"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WorkflowExecutionPlan(BaseModel):
    """A plan produced during the PLAN phase."""
    plan_id: str
    workflow_id: str
    objectives: List[str] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    required_agents: List[str] = Field(default_factory=list)
    estimated_duration: str = ""
    risk_assessment: str = ""
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime


class WorkflowResearchResult(BaseModel):
    """Research gathered during the RESEARCH phase."""
    research_id: str
    workflow_id: str
    sources: List[str] = Field(default_factory=list)
    findings: Dict[str, Any] = Field(default_factory=dict)
    key_insights: List[str] = Field(default_factory=list)
    data_points: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class WorkflowQCEvaluation(BaseModel):
    """Quality control evaluation (§8 - QC phase)."""
    evaluation_id: str
    workflow_id: str
    instance_id: str
    passed: bool = False
    score: float = 0.0
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    evaluated_by: str = ""
    evaluated_at: datetime


class WorkflowLearnEntry(BaseModel):
    """Learning entry produced during the LEARN phase."""
    entry_id: str
    workflow_id: str
    instance_id: str
    what_worked: List[str] = Field(default_factory=list)
    what_didnt: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    promoted_to_memory: bool = False
    created_at: datetime