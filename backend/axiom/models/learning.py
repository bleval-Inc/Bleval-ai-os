"""Pydantic models for the Continuous Learning Layer.

Sprint 2: Every workflow learns; every executive improves;
memory evolves; playbooks evolve; performance is measurable.

Learning models capture execution history, score performance,
detect patterns, and drive recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# =========================================================================
# Enums
# =========================================================================


class LearningSource(str, Enum):
    WORKFLOW = "workflow"
    EXECUTIVE = "executive"
    AGENT = "agent"
    MEMORY = "memory"
    SYSTEM = "system"


class ScoreCategory(str, Enum):
    SPEED = "speed"
    QUALITY = "quality"
    RELIABILITY = "reliability"
    EFFICIENCY = "efficiency"
    AUTONOMY = "autonomy"


class PatternSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    OPTIMIZATION = "optimization"
    LEARNING = "learning"


class RecommendationStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


# =========================================================================
# Performance Scoring
# =========================================================================


class PerformanceScore(BaseModel):
    """A single performance score for a workflow, executive, or agent run.

    Captures duration, error rate, step completion, and efficiency.
    Used by the Learning Engine to track improvement over time.
    """
    entity_id: str
    entity_type: str  # "workflow" | "executive" | "agent"
    instance_id: str = ""
    categories: Dict[ScoreCategory, float] = {}
    overall_score: float = 0.0
    duration_seconds: float = 0.0
    step_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    had_approval_hold: bool = False
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class ScoreHistory(BaseModel):
    """Rolling history of performance scores for an entity."""
    entity_id: str
    entity_type: str
    scores: List[PerformanceScore] = []
    running_average: float = 0.0
    trend: str = "stable"  # "improving" | "declining" | "stable"
    last_updated: datetime


# =========================================================================
# Workflow Analytics
# =========================================================================


class WorkflowExecutionRecord(BaseModel):
    """Detailed record of a single workflow execution for analytics."""
    instance_id: str
    workflow_id: str
    org: str = ""
    department: str = ""
    coordinator: str = ""
    status: str = ""
    total_duration_seconds: float = 0.0
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    retries: int = 0
    approval_requests: int = 0
    agents_involved: List[str] = []
    triggered_by: str = ""  # "event" | "manual" | "scheduler"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    tags: Dict[str, str] = {}


class WorkflowAnalyticsSummary(BaseModel):
    """Aggregated analytics for a workflow definition across all runs."""
    workflow_id: str
    total_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    avg_retries_per_run: float = 0.0
    avg_approval_holds: float = 0.0
    failure_reasons: Dict[str, int] = {}
    trend: str = "stable"
    last_run: Optional[datetime] = None
    recent_runs: List[WorkflowExecutionRecord] = []


# =========================================================================
# Executive / Agent Analytics
# =========================================================================


class ExecutiveDecisionRecord(BaseModel):
    """Record of an executive decision for analytics."""
    exec_id: str
    decision_type: str  # "delegation" | "approval" | "rejection" | "workflow_launch"
    workflow_instance_id: str = ""
    target: str = ""
    outcome: str = ""  # "success" | "failure" | "pending"
    reasoning: str = ""
    duration_seconds: float = 0.0
    timestamp: datetime


class AgentPerformanceRecord(BaseModel):
    """Record of an agent's task execution for analytics."""
    agent_id: str
    task_id: str = ""
    workflow_instance_id: str = ""
    action: str = ""
    duration_seconds: float = 0.0
    success: bool = True
    error: Optional[str] = None
    retries: int = 0
    timestamp: datetime


# =========================================================================
# Pattern Detection
# =========================================================================


class DetectedPattern(BaseModel):
    """A pattern detected across workflow/executive/agent executions."""
    pattern_id: str
    pattern_type: str  # "performance" | "error" | "bottleneck" | "opportunity"
    severity: PatternSeverity = PatternSeverity.INFO
    title: str
    description: str
    entities_involved: List[str] = []
    frequency: int = 0
    impact_score: float = 0.0  # 0.0 to 1.0
    first_detected: datetime
    last_detected: datetime
    evidence: List[str] = []
    metadata: Dict[str, Any] = {}


# =========================================================================
# Recommendation Engine
# =========================================================================


class Recommendation(BaseModel):
    """A concrete recommendation produced by the Learning Engine."""
    recommendation_id: str
    title: str
    description: str
    rationale: str
    expected_impact: str = ""
    source_pattern_id: str = ""
    target_entity_id: str = ""
    target_entity_type: str = ""  # "workflow" | "executive" | "agent" | "playbook"
    change_type: str = ""  # "modify" | "create" | "remove" | "reassign"
    suggested_action: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    status: RecommendationStatus = RecommendationStatus.DRAFT
    created_at: datetime
    applied_at: Optional[datetime] = None
    approved_by: str = ""


# =========================================================================
# Playbook Evolution
# =========================================================================


class PlaybookEvolution(BaseModel):
    """A change to a playbook driven by learning."""
    playbook_name: str
    version: str
    previous_version: str = ""
    change_description: str
    triggered_by_pattern: str = ""
    recommendation_id: str = ""
    diff_summary: str = ""
    applied_at: datetime
    approved_by: str = ""


# =========================================================================
# Knowledge Consolidation
# =========================================================================


class KnowledgeEntry(BaseModel):
    """A consolidated knowledge entry promoted from learning to memory."""
    entry_id: str
    title: str
    content: str
    source: LearningSource = LearningSource.SYSTEM
    source_entity: str = ""
    tags: List[str] = []
    confidence: float = 0.0
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0


# =========================================================================
# Learning Cycle
# =========================================================================


class LearningCycle(BaseModel):
    """A complete learning cycle: Execute → Observe → Measure → Learn → Improve."""
    cycle_id: str
    source_entity_id: str
    source_entity_type: str
    execution_ref: str = ""  # workflow instance id or task id
    scores: Dict[str, float] = {}
    patterns_detected: List[str] = []
    recommendations_generated: List[str] = []
    knowledge_written: List[str] = []
    improvements_applied: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    success: bool = True


# =========================================================================
# Learning Engine State (runtime persistence model)
# =========================================================================


class LearningEngineState(BaseModel):
    """Persistent state of the Learning Engine."""
    version: str = "1.0"
    total_cycles: int = 0
    total_patterns_detected: int = 0
    total_recommendations: int = 0
    total_knowledge_entries: int = 0
    workflow_runs_tracked: int = 0
    last_consolidation: Optional[datetime] = None
    last_knowledge_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = {}