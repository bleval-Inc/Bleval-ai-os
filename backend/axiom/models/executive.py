"""Pydantic models for the Phase B executive layer.

Includes:
  - ExecutiveIdentity — personality, communication style, behavioral rules
  - ExecutiveWorkstation — available agents, tools, workflows per executive
  - ExecutiveSchedule — detailed schedule with time blocks, active hours
  - ExecutiveKPI — KPI definitions with targets, current values, trends
  - ExecutiveDecision — decision record with context, outcome, reasoning
  - ExecutiveLearning — learning record with pattern, impact, incorporated date
  - ExecutiveFounderRelationship — communication preferences, escalation rules
  - BoardRoomAgenda — agenda items for board meetings
  - BoardRoomDecision — board decisions with voter records
  - BoardRoomMeeting — meeting record with attendees, agenda, decisions, action items
  - BoardRoomActionItem — action items with owner, deadline, status
  - MorningRoutine — morning routine steps with completion status
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutiveTier(str, Enum):
    """Executive tier classification."""
    FOUNDER = "founder"
    EXECUTIVE = "executive"
    SPECIALIST = "specialist"


class DecisionOutcome(str, Enum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class KPIStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BEHIND = "behind"
    EXCEEDED = "exceeded"
    NOT_TRACKED = "not_tracked"


class MeetingType(str, Enum):
    DAILY_BRIEFING = "daily_briefing"
    WEEKLY_EXECUTIVE = "weekly_executive"
    MONTHLY_REVIEW = "monthly_review"
    QUARTERLY_STRATEGIC = "quarterly_strategic"
    EMERGENCY = "emergency"
    AD_HOC = "ad_hoc"


class ActionItemStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class RoutineStepStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"
    ESCALATED = "escalated"


# ═══════════════════════════════════════════════════════════════════════════════
# Executive Identity
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutivePersonality(BaseModel):
    """The personality traits of an executive."""
    archetype: str = ""
    traits: List[str] = []
    communication_style: str = ""
    decision_style: str = ""
    signature: str = ""


class ExecutiveBehavioralRules(BaseModel):
    """Behavioral rules that govern the executive."""
    must_always: List[str] = []
    must_never: List[str] = []
    escalation_conditions: List[str] = []
    approval_required: List[str] = []


class ExecutiveObjectives(BaseModel):
    """High-level objectives for the executive."""
    primary_objective: str = ""
    secondary_objectives: List[str] = []
    current_focus: str = ""
    quarterly_goals: List[str] = []


class ExecutiveResponsibilities(BaseModel):
    """Areas of responsibility."""
    departments: List[str] = []
    direct_reports: List[str] = []
    tools_owned: List[str] = []
    workflows_owned: List[str] = []


class ExecutiveFounderRelationship(BaseModel):
    """How the executive relates to the Founder."""
    communication_preference: str = "briefing"
    report_cadence: str = "daily"
    escalation_protocol: str = ""
    decision_autonomy_level: str = "medium"  # low, medium, high
    requires_approval_for: List[str] = []


class ExecutiveIdentity(BaseModel):
    """Full identity definition for an executive."""
    exec_id: str
    name: str
    title: str
    organization: str
    tier: ExecutiveTier = ExecutiveTier.EXECUTIVE
    personality: ExecutivePersonality = ExecutivePersonality()
    behavioral_rules: ExecutiveBehavioralRules = ExecutiveBehavioralRules()
    objectives: ExecutiveObjectives = ExecutiveObjectives()
    responsibilities: ExecutiveResponsibilities = ExecutiveResponsibilities()
    founder_relationship: ExecutiveFounderRelationship = ExecutiveFounderRelationship()


# ═══════════════════════════════════════════════════════════════════════════════
# Executive Workstation
# ═══════════════════════════════════════════════════════════════════════════════


class WorkstationToolAccess(BaseModel):
    """Access level for a specific tool."""
    tool_id: str
    access_level: str = "read"  # read, write, execute
    restrictions: List[str] = []


class WorkstationAgentAccess(BaseModel):
    """An agent the executive can delegate to."""
    agent_id: str
    department: str = ""
    capabilities: List[str] = []
    priority: int = 0


class WorkstationWorkflowAccess(BaseModel):
    """A workflow the executive can launch."""
    workflow_id: str
    department: str = ""
    can_launch: bool = True
    requires_approval: bool = False


class ExecutiveWorkstation(BaseModel):
    """The tools, agents, and workflows available to an executive."""
    exec_id: str
    description: str = ""
    tools: List[WorkstationToolAccess] = []
    agents: List[WorkstationAgentAccess] = []
    workflows: List[WorkstationWorkflowAccess] = []
    integrations: List[str] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Executive Schedule
# ═══════════════════════════════════════════════════════════════════════════════


class TimeBlock(BaseModel):
    """A scheduled block of time for a specific activity."""
    name: str
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format
    description: str = ""
    day_of_week: str = "all"  # all, weekday, weekend, Mon, Tue, etc.
    is_fixed: bool = True     # Fixed time vs flexible window


class ExecutiveSchedule(BaseModel):
    """Full schedule definition for an executive."""
    exec_id: str
    active_hours_start: str = "08:00"
    active_hours_end: str = "18:00"
    timezone: str = "UTC"
    daily_blocks: List[TimeBlock] = []
    weekly_blocks: List[TimeBlock] = []
    monthly_blocks: List[TimeBlock] = []


# ═══════════════════════════════════════════════════════════════════════════════
# Executive KPI
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutiveKPIDefinition(BaseModel):
    """Definition of a single KPI."""
    kpi_id: str
    name: str
    description: str = ""
    unit: str = ""
    target: float = 0.0
    current_value: float = 0.0
    previous_value: float = 0.0
    trend: str = "stable"  # improving, declining, stable
    status: KPIStatus = KPIStatus.NOT_TRACKED
    last_updated: Optional[datetime] = None
    category: str = "general"


class ExecutiveKPISet(BaseModel):
    """Complete KPI set for an executive."""
    exec_id: str
    kpis: Dict[str, ExecutiveKPIDefinition] = {}
    last_full_update: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Executive Decision & Learning Records
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutiveDecision(BaseModel):
    """Record of an executive decision."""
    decision_id: str
    exec_id: str
    decision_type: str
    description: str
    context: Dict[str, Any] = {}
    reasoning: str = ""
    alternatives_considered: List[str] = []
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    outcome_detail: str = ""
    impact_score: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    workflow_instance_id: str = ""
    tags: List[str] = []


class ExecutiveLearning(BaseModel):
    """Record of a learning event."""
    learning_id: str
    exec_id: str
    pattern_type: str  # success, failure, optimization, insight
    description: str
    context: str = ""
    impact: str = ""
    incorporated: bool = False
    incorporated_at: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_decision_id: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Board Room
# ═══════════════════════════════════════════════════════════════════════════════


class BoardRoomAgenda(BaseModel):
    """An item on the board meeting agenda."""
    agenda_id: str
    meeting_id: str = ""
    submitted_by: str
    title: str
    description: str = ""
    supporting_data: Dict[str, Any] = {}
    priority: int = 0
    status: str = "pending"  # pending, discussed, resolved, deferred
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution: str = ""


class BoardRoomDecision(BaseModel):
    """A decision made in the board room."""
    decision_id: str
    meeting_id: str
    title: str
    description: str
    proposed_by: str
    voted_by: List[str] = []        # Executives who voted
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    approved: bool = False
    approved_by: str = ""           # Founder or system
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action_items: List[str] = []    # Action item IDs generated from this decision
    notes: str = ""


class BoardRoomActionItem(BaseModel):
    """An action item assigned during a board meeting."""
    item_id: str
    meeting_id: str
    title: str
    description: str = ""
    assigned_to: str        # Executive ID
    priority: str = "normal"  # critical, high, normal, low
    deadline: Optional[datetime] = None
    status: ActionItemStatus = ActionItemStatus.OPEN
    completed_at: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    depends_on: List[str] = []  # Other action item IDs


class BoardRoomMeeting(BaseModel):
    """Record of a board meeting."""
    meeting_id: str
    meeting_type: MeetingType
    title: str = ""
    called_by: str = ""  # Executive who called the meeting
    attendees: List[str] = []
    agenda: List[BoardRoomAgenda] = []
    decisions: List[BoardRoomDecision] = []
    action_items: List[BoardRoomActionItem] = []
    kpi_snapshots: Dict[str, Dict[str, float]] = {}  # exec_id -> {kpi_name: value}
    minutes: str = ""
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    notes: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Morning Routine
# ═══════════════════════════════════════════════════════════════════════════════


class MorningRoutineStep(BaseModel):
    """A single step in the morning routine."""
    step_name: str
    target_time: str  # "HH:MM"
    duration_minutes: int = 15
    description: str = ""
    required: bool = True
    escalation_after_minutes: int = 15
    status: RoutineStepStatus = RoutineStepStatus.PENDING
    completed_at: Optional[datetime] = None


class MorningRoutine(BaseModel):
    """The complete morning routine definition."""
    routine_name: str = "Founder Morning Routine"
    owner: str = "yamako"
    wake_up_time: str = "05:00"
    routine_end_time: str = "08:30"
    steps: List[MorningRoutineStep] = []
    escalation_message: str = "Tounga, wake up. It's time to start your day."
    escalation_interval_minutes: int = 5
    max_escalations: int = 5
    quote_of_the_day: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))