"""Pydantic models for Quality Control — Phase D Quality Control + Founder Authority.

These models define the QC check types, statuses, and result structures
used by the QC Agent to inspect all deliverables before they reach the Founder.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QCStatus(str, Enum):
    """Status of a QC check."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    RE_CHECKING = "re_checking"


class QCScope(str, Enum):
    """Scope of what the QC check covers."""
    CLIENT_DELIVERABLE = "client_deliverable"
    PROPOSAL = "proposal"
    PUBLIC_CONTENT = "public_content"
    SOCIAL_MEDIA = "social_media"
    CLIENT_FACING_DOCUMENT = "client_facing_document"
    PROJECT_DELIVERY = "project_delivery"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    HIGH_RISK_COMMUNICATION = "high_risk_communication"
    INTERNAL_DOCUMENT = "internal_document"
    CODE_REVIEW = "code_review"
    WORKFLOW_OUTPUT = "workflow_output"
    AGENT_OUTPUT = "agent_output"


class QCCheckType(str, Enum):
    """Each quality dimension the QC Agent inspects."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    READABILITY = "readability"
    PROFESSIONALISM = "professionalism"
    DUPLICATION = "duplication"
    PLACEHOLDER_CONTENT = "placeholder_content"
    DUMMY_DATA = "dummy_data"
    FAKE_INFORMATION = "fake_information"
    BROKEN_LINKS = "broken_links"
    FORMATTING = "formatting"
    CONSISTENCY = "consistency"
    BRAND_STANDARDS = "brand_standards"
    TECHNICAL_CORRECTNESS = "technical_correctness"
    CLIENT_REQUIREMENTS = "client_requirements"
    HALLUCINATED_INFO = "hallucinated_information"
    MISSING_ASSETS = "missing_assets"
    MISSING_SECTIONS = "missing_sections"
    OBVIOUS_ERRORS = "obvious_errors"


class QCSeverity(str, Enum):
    """How severe a QC failure is."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QCFinding(BaseModel):
    """A single QC finding — an issue detected during inspection."""
    check_type: QCCheckType
    severity: QCSeverity
    location: str = ""
    description: str
    detail: str = ""
    suggested_fix: str = ""
    affected_artifact: str = ""


class QCResult(BaseModel):
    """Result of a full QC check on a single artifact."""
    qc_id: str
    artifact_id: str
    artifact_name: str
    artifact_type: str
    scope: QCScope
    status: QCStatus = QCStatus.PENDING

    # Inspector metadata
    inspected_by: str = "qc_agent"
    inspected_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Findings
    findings: List[QCFinding] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Summary
    passed: bool = False
    retry_count: int = 0
    summary: str = ""

    # Version tracking
    artifact_version: str = ""
    previous_qc_id: Optional[str] = None

    def calculate_severity_counts(self) -> None:
        """Recalculate severity counts from findings."""
        self.critical_count = sum(
            1 for f in self.findings if f.severity == QCSeverity.CRITICAL
        )
        self.high_count = sum(
            1 for f in self.findings if f.severity == QCSeverity.HIGH
        )
        self.medium_count = sum(
            1 for f in self.findings if f.severity == QCSeverity.MEDIUM
        )
        self.low_count = sum(
            1 for f in self.findings if f.severity == QCSeverity.LOW
        )

    def has_failures(self) -> bool:
        """Return True if any critical or high severity issues exist."""
        self.calculate_severity_counts()
        return self.critical_count > 0 or self.high_count > 0

    def to_dict(self) -> Dict[str, Any]:
        self.calculate_severity_counts()
        return {
            "qc_id": self.qc_id,
            "artifact_id": self.artifact_id,
            "artifact_name": self.artifact_name,
            "artifact_type": self.artifact_type,
            "scope": self.scope.value,
            "status": self.status.value,
            "inspected_by": self.inspected_by,
            "inspected_at": self.inspected_at.isoformat() if self.inspected_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "findings": [f.model_dump() for f in self.findings],
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "passed": self.passed,
            "retry_count": self.retry_count,
            "summary": self.summary,
            "artifact_version": self.artifact_version,
        }


class QCRequest(BaseModel):
    """Request to QC an artifact."""
    artifact_id: str
    artifact_name: str
    artifact_type: str = "document"
    artifact_content: str = ""
    scope: QCScope = QCScope.INTERNAL_DOCUMENT
    artifact_version: str = ""
    previous_qc_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    client_requirements: Optional[str] = None
    brand_guidelines: Optional[str] = None