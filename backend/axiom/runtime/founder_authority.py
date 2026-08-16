"""Founder Authority — Phase D Quality Control + Founder Authority.

The Founder retains final authority over:
  - money, trades, contracts
  - deletion, irreversible actions
  - external client communication
  - high-risk prospect communication
  - public publishing
  - production deployment
  - major strategic decisions

Every approval is recorded for full auditability.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class RestrictedAction(str, Enum):
    """Actions that require explicit Founder approval."""
    MONEY = "money"
    TRADES = "trades"
    CONTRACTS = "contracts"
    DELETION = "deletion"
    IRREVERSIBLE = "irreversible"
    EXTERNAL_CLIENT_COMMS = "external_client_comms"
    HIGH_RISK_PROSPECT_COMMS = "high_risk_prospect_comms"
    PUBLIC_PUBLISHING = "public_publishing"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    MAJOR_STRATEGIC = "major_strategic"


class ApprovalAction(str, Enum):
    """Actions the Founder can take on an approval request."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    DISCUSS = "discuss"


class ApprovalUrgency(str, Enum):
    """Urgency level of an approval request."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalStatus(str, Enum):
    """Status of a founder approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    UNDER_DISCUSSION = "under_discussion"
    ESCALATED = "escalated"


@dataclass
class ApprovalContext:
    """Full context shown in the Approval UI:
    WHAT, WHY, WHO, EXPECTED_RESULT, RISK, COST, TIMELINE, SOURCE_MATERIAL, FINAL_OUTPUT.
    """
    what: str
    why: str
    who: str
    expected_result: str
    risk: str
    cost: str
    timeline: str
    source_material: str = ""
    final_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        return {
            "what": self.what,
            "why": self.why,
            "who": self.who,
            "expected_result": self.expected_result,
            "risk": self.risk,
            "cost": self.cost,
            "timeline": self.timeline,
            "source_material": self.source_material,
            "final_output": self.final_output,
        }


@dataclass
class AuthorityRecord:
    """Audit record for every Founder approval action."""
    record_id: str
    founder_identity: str
    action: ApprovalAction
    status: ApprovalStatus
    timestamp: datetime
    approval_id: str
    restricted_action: RestrictedAction
    artifact_id: str
    artifact_version: str
    approving_context: str
    downstream_action: str
    notes: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "founder_identity": self.founder_identity,
            "action": self.action.value,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "approval_id": self.approval_id,
            "restricted_action": self.restricted_action.value,
            "artifact_id": self.artifact_id,
            "artifact_version": self.artifact_version,
            "approving_context": self.approving_context,
            "downstream_action": self.downstream_action,
            "notes": self.notes,
            "duration_ms": self.duration_ms,
        }


class FounderAuthority:
    """Enforces Founder authority over all restricted actions.

    Every restricted action must go through this system:
    1. Action is classified as restricted
    2. Approval request is created with full context
    3. Founder approves/rejects/requests changes/discusses
    4. Action executes only on APPROVE
    5. Every action is audited
    """

    # The complete set of restricted actions
    RESTRICTED_ACTIONS: Set[str] = {
        RestrictedAction.MONEY,
        RestrictedAction.TRADES,
        RestrictedAction.CONTRACTS,
        RestrictedAction.DELETION,
        RestrictedAction.IRREVERSIBLE,
        RestrictedAction.EXTERNAL_CLIENT_COMMS,
        RestrictedAction.HIGH_RISK_PROSPECT_COMMS,
        RestrictedAction.PUBLIC_PUBLISHING,
        RestrictedAction.PRODUCTION_DEPLOYMENT,
        RestrictedAction.MAJOR_STRATEGIC,
    }

    def __init__(self) -> None:
        # Active approval requests
        self._approvals: Dict[str, ApprovalContext] = {}
        self._approval_statuses: Dict[str, ApprovalStatus] = {}
        self._approval_actions: Dict[str, RestrictedAction] = {}
        self._approval_urgencies: Dict[str, ApprovalUrgency] = {}
        self._approval_versions: Dict[str, str] = {}
        self._approval_downstream: Dict[str, str] = {}

        # Audit trail
        self._audit_records: List[AuthorityRecord] = []
        self._founder_identity: str = "founder"

        # Approval handler callbacks (set by lifecycle)
        self._on_approve: Optional[callable] = None
        self._on_reject: Optional[callable] = None
        self._on_changes_requested: Optional[callable] = None

    # ── Setting callbacks ──────────────────────────────────────────────

    def set_on_approve(self, callback: callable) -> None:
        self._on_approve = callback

    def set_on_reject(self, callback: callable) -> None:
        self._on_reject = callback

    def set_on_changes_requested(self, callback: callable) -> None:
        self._on_changes_requested = callback

    # ── Authority Checks ───────────────────────────────────────────────

    def is_restricted(self, action_type: str) -> bool:
        """Check if an action type requires Founder approval."""
        return action_type in self.RESTRICTED_ACTIONS

    def requires_approval(self, action_type: str, context: Dict[str, Any] = None) -> bool:
        """Check if an action requires approval.

        Some restricted actions may have thresholds (e.g., money < $100).
        Default: all restricted actions require approval.
        """
        return self.is_restricted(action_type)

    # ── Approval Request Lifecycle ─────────────────────────────────────

    def request_approval(
        self,
        restricted_action: RestrictedAction,
        context: ApprovalContext,
        urgency: ApprovalUrgency = ApprovalUrgency.MEDIUM,
        artifact_version: str = "",
        downstream_action: str = "",
    ) -> str:
        """Create a new approval request for a restricted action.

        Returns the approval_id.
        """
        approval_id = f"fa-{uuid.uuid4().hex[:12]}"
        self._approvals[approval_id] = context
        self._approval_statuses[approval_id] = ApprovalStatus.PENDING
        self._approval_actions[approval_id] = restricted_action
        self._approval_urgencies[approval_id] = urgency
        self._approval_versions[approval_id] = artifact_version
        self._approval_downstream[approval_id] = downstream_action
        return approval_id

    def get_approval_context(self, approval_id: str) -> Optional[ApprovalContext]:
        return self._approvals.get(approval_id)

    def get_approval_status(self, approval_id: str) -> Optional[ApprovalStatus]:
        return self._approval_statuses.get(approval_id)

    def get_approval_action(self, approval_id: str) -> Optional[RestrictedAction]:
        return self._approval_actions.get(approval_id)

    def get_approval_urgency(self, approval_id: str) -> Optional[ApprovalUrgency]:
        return self._approval_urgencies.get(approval_id)

    def list_pending(self) -> List[Dict[str, Any]]:
        """List all pending approval requests with full context."""
        results = []
        for aid, status in self._approval_statuses.items():
            if status == ApprovalStatus.PENDING:
                ctx = self._approvals.get(aid)
                results.append({
                    "approval_id": aid,
                    "restricted_action": self._approval_actions.get(aid).value
                    if self._approval_actions.get(aid) else "unknown",
                    "urgency": self._approval_urgencies.get(aid).value
                    if self._approval_urgencies.get(aid) else "medium",
                    "context": ctx.to_dict() if ctx else {},
                    "status": status.value,
                    "artifact_version": self._approval_versions.get(aid, ""),
                })
        return results

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all approval requests, most recent first."""
        results = []
        for aid in list(self._approvals.keys())[-limit:]:
            ctx = self._approvals.get(aid)
            status = self._approval_statuses.get(aid)
            results.append({
                "approval_id": aid,
                "restricted_action": self._approval_actions.get(aid).value
                if self._approval_actions.get(aid) else "unknown",
                "status": status.value if status else "unknown",
                "urgency": self._approval_urgencies.get(aid).value
                if self._approval_urgencies.get(aid) else "medium",
                "context": ctx.to_dict() if ctx else {},
                "artifact_version": self._approval_versions.get(aid, ""),
            })
        return list(reversed(results))

    def pending_count(self) -> int:
        """Return number of pending approvals."""
        return sum(1 for s in self._approval_statuses.values()
                   if s == ApprovalStatus.PENDING)

    # ── Founder Actions ────────────────────────────────────────────────

    async def approve(self, approval_id: str, founder_identity: str = "founder",
                      notes: str = "") -> bool:
        """Founder approves a restricted action. Returns True if action can proceed."""
        status = self._approval_statuses.get(approval_id)
        if not status or status != ApprovalStatus.PENDING:
            return False

        self._approval_statuses[approval_id] = ApprovalStatus.APPROVED

        # Audit record
        self._record(
            approval_id=approval_id,
            founder_identity=founder_identity,
            action=ApprovalAction.APPROVE,
            status=ApprovalStatus.APPROVED,
            notes=notes,
        )

        # Fire callback
        if self._on_approve:
            await self._on_approve(approval_id)

        return True

    async def reject(self, approval_id: str, founder_identity: str = "founder",
                     notes: str = "") -> bool:
        """Founder rejects a restricted action."""
        status = self._approval_statuses.get(approval_id)
        if not status or status != ApprovalStatus.PENDING:
            return False

        self._approval_statuses[approval_id] = ApprovalStatus.REJECTED

        self._record(
            approval_id=approval_id,
            founder_identity=founder_identity,
            action=ApprovalAction.REJECT,
            status=ApprovalStatus.REJECTED,
            notes=notes,
        )

        if self._on_reject:
            await self._on_reject(approval_id)

        return True

    async def request_changes(self, approval_id: str, founder_identity: str = "founder",
                              notes: str = "") -> bool:
        """Founder requests changes before approving."""
        status = self._approval_statuses.get(approval_id)
        if not status or status != ApprovalStatus.PENDING:
            return False

        self._approval_statuses[approval_id] = ApprovalStatus.CHANGES_REQUESTED

        self._record(
            approval_id=approval_id,
            founder_identity=founder_identity,
            action=ApprovalAction.REQUEST_CHANGES,
            status=ApprovalStatus.CHANGES_REQUESTED,
            notes=notes,
        )

        if self._on_changes_requested:
            await self._on_changes_requested(approval_id, notes)

        return True

    async def discuss(self, approval_id: str, founder_identity: str = "founder",
                      notes: str = "") -> bool:
        """Founder opens discussion on an approval request."""
        status = self._approval_statuses.get(approval_id)
        if not status:
            return False

        self._approval_statuses[approval_id] = ApprovalStatus.UNDER_DISCUSSION

        self._record(
            approval_id=approval_id,
            founder_identity=founder_identity,
            action=ApprovalAction.DISCUSS,
            status=ApprovalStatus.UNDER_DISCUSSION,
            notes=notes,
        )

        return True

    # ── Audit Trail ────────────────────────────────────────────────────

    def _record(self, approval_id: str, founder_identity: str,
                action: ApprovalAction, status: ApprovalStatus,
                notes: str = "") -> None:
        """Record an authority action in the audit trail."""
        context = self._approvals.get(approval_id)
        restricted_action = self._approval_actions.get(approval_id, RestrictedAction.MONEY)

        record = AuthorityRecord(
            record_id=f"ar-{uuid.uuid4().hex[:12]}",
            founder_identity=founder_identity,
            action=action,
            status=status,
            timestamp=datetime.now(timezone.utc),
            approval_id=approval_id,
            restricted_action=restricted_action,
            artifact_id=context.what if context else "",
            artifact_version=self._approval_versions.get(approval_id, ""),
            approving_context=context.why if context else "",
            downstream_action=self._approval_downstream.get(approval_id, ""),
            notes=notes,
        )
        self._audit_records.append(record)

    def get_audit_trail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the complete audit trail of all Founder authority actions."""
        return [r.to_dict() for r in self._audit_records[-limit:]]

    def get_audit_by_approval(self, approval_id: str) -> List[Dict[str, Any]]:
        """Get audit records for a specific approval request."""
        return [
            r.to_dict() for r in self._audit_records
            if r.approval_id == approval_id
        ]

    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary statistics of authority actions."""
        total = len(self._audit_records)
        approved = sum(1 for r in self._audit_records
                       if r.action == ApprovalAction.APPROVE)
        rejected = sum(1 for r in self._audit_records
                       if r.action == ApprovalAction.REJECT)
        changes = sum(1 for r in self._audit_records
                      if r.action == ApprovalAction.REQUEST_CHANGES)

        return {
            "total_records": total,
            "approved": approved,
            "rejected": rejected,
            "changes_requested": changes,
            "pending_approvals": self.pending_count(),
            "unique_actions": len(set(r.restricted_action.value
                                      for r in self._audit_records)),
        }

    # ── Summary ────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get full status of the Founder Authority system."""
        return {
            "restricted_actions": sorted(self.RESTRICTED_ACTIONS),
            "pending_approvals": self.pending_count(),
            "total_approvals": len(self._approvals),
            "total_audit_records": len(self._audit_records),
            "audit_summary": self.get_audit_summary(),
        }