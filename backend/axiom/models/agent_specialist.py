"""Pydantic models for the specialist agent system.

Specialist agents are the skilled workforce in Axiom OS.
Each specialist type has a defined role, capabilities, and tool access.

Architecture:
  Executive (manages)
       ↓
  Specialist Agent (performs)
       ↓
  Tools / Workflows (executes)

Specialist types defined in PHASE C §3:
  Research, Market Intelligence, Content Writer, Image, Video, Audio,
  SEO, Lead Research, Outreach, CRM, Development, Testing, Documentation,
  Trading Research, Calendar, Learning, Monitoring, QC, etc.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SpecialistType(str, Enum):
    """All specialist agent types in the system."""
    RESEARCH = "research"
    MARKET_INTELLIGENCE = "market_intelligence"
    CONTENT_WRITER = "content_writer"
    CONTENT_RESEARCH = "content_research"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SEO = "seo"
    LEAD_RESEARCH = "lead_research"
    OUTREACH = "outreach"
    CRM = "crm"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    TRADING_RESEARCH = "trading_research"
    CALENDAR = "calendar"
    LEARNING = "learning"
    MONITORING = "monitoring"
    QC = "qc"
    CUSTOM = "custom"


class SpecialistCapability(BaseModel):
    """A discrete capability a specialist agent can perform."""
    name: str
    description: str = ""
    required_tools: List[str] = []
    estimated_complexity: str = "normal"  # simple | normal | complex | strategic
    estimated_duration_seconds: int = 60


class SpecialistOutput(BaseModel):
    """Output produced by a specialist agent."""
    output_id: str
    specialist_type: str
    task_id: str = ""
    workflow_instance_id: str = ""
    content: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime
    quality_score: float = 0.0
    qc_passed: Optional[bool] = None


class SpecialistTask(BaseModel):
    """A task assigned to a specialist agent."""
    task_id: str
    specialist_type: SpecialistType
    agent_id: str
    workflow_instance_id: str = ""
    step_id: str = ""
    instruction: str
    context: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    status: str = "pending"  # pending | running | completed | failed | qc_failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[SpecialistOutput] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0


class AgentSession(BaseModel):
    """Runtime session for an active specialist agent."""
    session_id: str
    agent_id: str
    specialist_type: SpecialistType
    status: str = "idle"  # idle | busy | paused | error
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    started_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = {}


class SpecialistRegistry(BaseModel):
    """Registry of all specialist agents available in the system.

    This is the discovery mechanism for specialist agents (§3).
    Agents are discovered through the capability/tool architecture.
    """
    specialists: Dict[str, SpecialistType] = Field(
        default_factory=lambda: {
            t.value: t for t in SpecialistType
        }
    )