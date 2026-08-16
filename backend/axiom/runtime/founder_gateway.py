"""Founder Gateway — the approval pipeline orchestrator for Phase D.

Orchestrates the full approval pipeline:

    Executive researches
    ↓
    Executive creates plan
    ↓
    Executive provides: objective, proposed action, methodology,
                       expected result, resources, risks, timeline
    ↓
    Founder approves
    ↓
    Workflow executes
    ↓
    Agents complete work
    ↓
    Testing
    ↓
    QC → FAILED → return to agent/workflow (NEVER to Founder)
    ↓
    Executive review
    ↓
    Founder final review
    ↓
    Publish / Deploy / Schedule

Founder Feed (default): FAST FEED — show only critical issues,
approvals, important decisions, and executive requests.

Approval UI shows: WHAT, WHY, WHO, EXPECTED_RESULT, RISK, COST,
TIMELINE, SOURCE_MATERIAL, FINAL_OUTPUT.

Actions: APPROVE, REJECT, REQUEST CHANGES, DISCUSS.

Every approval is audited: Founder identity, action, timestamp,
artifact, version, approving context, downstream action.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from axiom.models.qc import QCResult, QCScope, QCStatus
from axiom.runtime.founder_authority import (
    ApprovalAction,
    ApprovalContext,
    ApprovalStatus,
    ApprovalUrgency,
    FounderAuthority,
    RestrictedAction,
)
from axiom.runtime.qc_engine import QCManager, QCReworkEntry


class PipelineStage(str, Enum):
    """Stages in the Founder approval pipeline."""
    EXECUTIVE_RESEARCH = "executive_research"
    EXECUTIVE_PLAN = "executive_plan"
    FOUNDER_APPROVE = "founder_approve"
    WORKFLOW_EXECUTE = "workflow_execute"
    AGENTS_COMPLETE = "agents_complete"
    TESTING = "testing"
    QC = "qc"
    EXECUTIVE_REVIEW = "executive_review"
    FOUNDER_REVIEW = "founder_review"
    PUBLISH = "publish"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class PipelineExecutionPlan:
    """The plan produced by the executive for Founder approval.

    Matches the Approval UI spec:
      WHAT, WHY, WHO, EXPECTED_RESULT, RISK, COST, TIMELINE,
      SOURCE_MATERIAL, FINAL_OUTPUT
    """
    objective: str
    proposed_action: str
    methodology: str
    expected_result: str
    resources: str
    risks: str
    timeline: str
    source_material: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_approval_context(self, who: str) -> ApprovalContext:
        """Convert this plan into an ApprovalContext for the FounderAuthority."""
        return ApprovalContext(
            what=self.objective,
            why=self.proposed_action,
            who=who,
            expected_result=self.expected_result,
            risk=self.risks,
            cost=self.resources,
            timeline=self.timeline,
            source_material=self.source_material,
            final_output="",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "proposed_action": self.proposed_action,
            "methodology": self.methodology,
            "expected_result": self.expected_result,
            "resources": self.resources,
            "risks": self.risks,
            "timeline": self.timeline,
            "source_material": self.source_material,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class PipelineInstance:
    """A single pipeline instance tracking end-to-end flow."""
    pipeline_id: str
    title: str
    executive: str
    stage: PipelineStage = PipelineStage.EXECUTIVE_RESEARCH
    plan: Optional[PipelineExecutionPlan] = None

    # Workflow tracking
    workflow_instance_id: str = ""
    workflow_id: str = ""

    # QC tracking
    qc_id: Optional[str] = None
    qc_result: Optional[QCResult] = None

    # Approval tracking
    founder_approval_id: Optional[str] = None
    founder_review_approval_id: Optional[str] = None

    # Output
    final_output: str = ""
    downstream_action: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    stage_started_at: Optional[datetime] = None

    # Status
    failed: bool = False
    error: Optional[str] = None
    cancelled: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "title": self.title,
            "executive": self.executive,
            "stage": self.stage.value,
            "plan": self.plan.to_dict() if self.plan else None,
            "workflow_instance_id": self.workflow_instance_id,
            "workflow_id": self.workflow_id,
            "qc_id": self.qc_id,
            "qc_passed": self.qc_result.passed if self.qc_result else None,
            "founder_approval_id": self.founder_approval_id,
            "founder_review_approval_id": self.founder_review_approval_id,
            "final_output": self.final_output[:500] if len(self.final_output) > 500 else self.final_output,
            "downstream_action": self.downstream_action,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed": self.failed,
            "error": self.error,
            "cancelled": self.cancelled,
        }


@dataclass
class FounderFeedItem:
    """A single item in the Founder's FAST FEED.

    The default Founder experience is FAST FEED — show only:
      - critical issues
      - approvals
      - important decisions
      - executive requests
    Everything else runs silently.
    """
    feed_id: str
    item_type: str  # critical_issue, approval, decision, executive_request, notification
    title: str
    summary: str
    pipeline_id: Optional[str] = None
    approval_id: Optional[str] = None
    severity: str = "info"  # critical, high, medium, low, info
    requires_action: bool = False
    actionable: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feed_id": self.feed_id,
            "item_type": self.item_type,
            "title": self.title,
            "summary": self.summary,
            "pipeline_id": self.pipeline_id,
            "approval_id": self.approval_id,
            "severity": self.severity,
            "requires_action": self.requires_action,
            "actionable": self.actionable,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
        }


class FounderGateway:
    """Orchestrates the complete Founder approval and QC pipeline.

    Full pipeline:
      1. Executive researches and creates a plan
      2. Executive submits plan (objective, methodology, risks, timeline...)
      3. Founder approves the plan → OR rejects/changes
      4. Workflow executes
      5. Agents complete work
      6. Testing
      7. QC → if fails, returned to agent/workflow (NEVER to Founder)
      8. Executive review
      9. Founder final review
      10. Publish / Deploy / Schedule
    """

    def __init__(
        self,
        founder_authority: FounderAuthority,
        qc_manager: QCManager,
        runtime: Any = None,
    ) -> None:
        self._authority = founder_authority
        self._qc = qc_manager
        self._runtime = runtime

        # Active pipeline instances: pipeline_id -> PipelineInstance
        self._pipelines: Dict[str, PipelineInstance] = {}

        # Founder's FAST FEED
        self._feed: List[FounderFeedItem] = []

        # Callbacks
        self._on_pipeline_stage: Optional[Callable] = None
        self._on_founder_ready: Optional[Callable] = None
        self._on_pipeline_completed: Optional[Callable] = None

    # ── Callbacks ──────────────────────────────────────────────────────────

    def set_on_pipeline_stage(self, callback: Callable) -> None:
        self._on_pipeline_stage = callback

    def set_on_founder_ready(self, callback: Callable) -> None:
        self._on_founder_ready = callback

    def set_on_pipeline_completed(self, callback: Callable) -> None:
        self._on_pipeline_completed = callback

    # ── Pipeline Lifecycle ─────────────────────────────────────────────────

    def create_pipeline(
        self,
        title: str,
        executive: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new approval pipeline instance.

        Returns the pipeline_id.
        """
        pipeline_id = f"pl-{uuid.uuid4().hex[:12]}"
        instance = PipelineInstance(
            pipeline_id=pipeline_id,
            title=title,
            executive=executive,
            metadata=metadata or {},
        )
        self._pipelines[pipeline_id] = instance
        return pipeline_id

    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineInstance]:
        """Get a pipeline instance."""
        return self._pipelines.get(pipeline_id)

    def list_pipelines(
        self,
        stage: Optional[PipelineStage] = None,
        executive: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List pipeline instances, optionally filtered."""
        items = list(self._pipelines.values())
        if stage:
            items = [i for i in items if i.stage == stage]
        if executive:
            items = [i for i in items if i.executive == executive]
        return [i.to_dict() for i in sorted(items, key=lambda x: x.created_at, reverse=True)]

    # ── Stage 1-2: Executive Research & Plan ───────────────────────────────

    async def submit_plan(
        self,
        pipeline_id: str,
        plan: PipelineExecutionPlan,
    ) -> bool:
        """Executive submits a plan after research.

        Transitions pipeline from RESEARCH to PLAN stage.
        The plan includes: objective, proposed_action, methodology,
        expected_result, resources, risks, timeline, source_material.
        """
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return False

        instance.plan = plan
        instance.stage = PipelineStage.EXECUTIVE_PLAN
        instance.stage_started_at = datetime.now(timezone.utc)

        # Notify stage change
        if self._on_pipeline_stage:
            await self._on_pipeline_stage(pipeline_id, instance)

        # Add to Founder's feed — this is an important decision
        self._add_to_feed(
            item_type="executive_request",
            title=f"{instance.executive} requests approval: {instance.title}",
            summary=f"Plan submitted. Risks: {plan.risks[:200]}. Timeline: {plan.timeline}",
            pipeline_id=pipeline_id,
            severity="medium" if "low" in plan.risks.lower() else "high",
            requires_action=True,
            actionable=True,
        )

        return True

    # ── Stage 3: Founder Approve ───────────────────────────────────────────

    async def request_founder_approval(
        self,
        pipeline_id: str,
        urgency: ApprovalUrgency = ApprovalUrgency.MEDIUM,
    ) -> Optional[str]:
        """Submit the plan for Founder approval.

        Creates an approval request in the FounderAuthority.
        Returns the approval_id.
        """
        instance = self._pipelines.get(pipeline_id)
        if not instance or not instance.plan:
            return None

        instance.stage = PipelineStage.FOUNDER_APPROVE
        instance.stage_started_at = datetime.now(timezone.utc)

        # Map pipeline to restricted action
        restricted_action = self._map_to_restricted_action(instance)

        # Create approval context from the plan
        ctx = instance.plan.to_approval_context(who=instance.executive)
        ctx.final_output = instance.final_output

        # Request approval from FounderAuthority
        approval_id = self._authority.request_approval(
            restricted_action=restricted_action,
            context=ctx,
            urgency=urgency,
            artifact_version=instance.metadata.get("version", "1.0"),
            downstream_action=instance.downstream_action or "execute_workflow",
        )

        instance.founder_approval_id = approval_id

        # Notify stage change
        if self._on_pipeline_stage:
            await self._on_pipeline_stage(pipeline_id, instance)

        # Add to Founder feed
        self._add_to_feed(
            item_type="approval",
            title=f"APPROVAL REQUIRED: {instance.title}",
            summary=f"{instance.executive} requests approval for: {instance.plan.objective[:200]}",
            pipeline_id=pipeline_id,
            approval_id=approval_id,
            severity="high" if urgency in (ApprovalUrgency.CRITICAL, ApprovalUrgency.HIGH) else "medium",
            requires_action=True,
            actionable=True,
        )

        return approval_id

    def _map_to_restricted_action(self, instance: PipelineInstance) -> RestrictedAction:
        """Map a pipeline to the appropriate RestrictedAction."""
        title_lower = instance.title.lower()
        metadata = instance.metadata or {}

        action_hints = metadata.get("restricted_action", "")
        if action_hints:
            try:
                return RestrictedAction(action_hints)
            except ValueError:
                pass

        # Heuristic mapping
        if any(w in title_lower for w in ["money", "payment", "budget", "fund", "pricing", "invoice"]):
            return RestrictedAction.MONEY
        elif any(w in title_lower for w in ["trade", "market", "position", "deal"]):
            return RestrictedAction.TRADES
        elif any(w in title_lower for w in ["contract", "agreement", "legal", "terms"]):
            return RestrictedAction.CONTRACTS
        elif any(w in title_lower for w in ["delete", "remove", "destroy", "terminate"]):
            return RestrictedAction.DELETION
        elif any(w in title_lower for w in ["irreversible", "irrevers"]):
            return RestrictedAction.IRREVERSIBLE
        elif any(w in title_lower for w in ["client", "customer communication", "client email"]):
            return RestrictedAction.EXTERNAL_CLIENT_COMMS
        elif any(w in title_lower for w in ["prospect", "cold", "outreach", "sales pitch"]):
            return RestrictedAction.HIGH_RISK_PROSPECT_COMMS
        elif any(w in title_lower for w in ["publish", "public", "release", "announce", "social", "post"]):
            return RestrictedAction.PUBLIC_PUBLISHING
        elif any(w in title_lower for w in ["deploy", "production", "release"]):
            return RestrictedAction.PRODUCTION_DEPLOYMENT
        elif any(w in title_lower for w in ["strategic", "strategy", "pivot", "acquisition", "partnership"]):
            return RestrictedAction.MAJOR_STRATEGIC

        return RestrictedAction.MAJOR_STRATEGIC

    # ── Stage 4-6: Execute, Test, QC ───────────────────────────────────────

    async def start_execution(
        self,
        pipeline_id: str,
        workflow_id: str,
    ) -> bool:
        """Start workflow execution after Founder approval."""
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return False

        instance.stage = PipelineStage.WORKFLOW_EXECUTE
        instance.workflow_id = workflow_id
        instance.stage_started_at = datetime.now(timezone.utc)

        if self._on_pipeline_stage:
            await self._on_pipeline_stage(pipeline_id, instance)

        return True

    async def register_qc_result(
        self,
        pipeline_id: str,
        qc_result: QCResult,
    ) -> None:
        """Register a QC result for the pipeline.

        If QC FAILED: return to agent/workflow — NEVER to Founder.
        If QC PASSED: advance to executive review.
        """
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return

        instance.qc_id = qc_result.qc_id
        instance.qc_result = qc_result

        instance.stage = PipelineStage.QC
        instance.stage_started_at = datetime.now(timezone.utc)

        if qc_result.passed:
            # QC passed — advance to executive review
            instance.stage = PipelineStage.EXECUTIVE_REVIEW

            # Notify
            if self._on_pipeline_stage:
                await self._on_pipeline_stage(pipeline_id, instance)

            # Add to Founder feed (informational)
            self._add_to_feed(
                item_type="notification",
                title=f"QC passed: {instance.title}",
                summary=qc_result.summary,
                pipeline_id=pipeline_id,
                severity="info",
                requires_action=False,
            )
        else:
            # QC FAILED — NEVER notify Founder.
            # The QC engine handles returning work to agent/workflow.
            # We just log the state here.
            instance.stage = PipelineStage.QC

    # ── Stage 8-9: Founder Final Review ────────────────────────────────────

    async def submit_for_founder_review(
        self,
        pipeline_id: str,
        final_output: str,
    ) -> Optional[str]:
        """Executive submits completed work for Founder final review.

        This happens after QC has passed and executive has reviewed.
        Returns the approval_id for the final review.
        """
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return None

        instance.final_output = final_output
        instance.stage = PipelineStage.FOUNDER_REVIEW
        instance.stage_started_at = datetime.now(timezone.utc)

        # Create an approval context for final review
        plan = instance.plan
        ctx = ApprovalContext(
            what=plan.objective if plan else instance.title,
            why=f"Final review of approved work: {instance.title}",
            who=instance.executive,
            expected_result=plan.expected_result if plan else "",
            risk=plan.risks if plan else "",
            cost=plan.resources if plan else "",
            timeline=plan.timeline if plan else "",
            source_material=f"Pipeline: {pipeline_id}, QC: {instance.qc_id}",
            final_output=final_output[:1000],
        )

        qc_summary = (
            f"QC {'PASSED' if instance.qc_result and instance.qc_result.passed else 'N/A'}"
        )

        approval_id = self._authority.request_approval(
            restricted_action=RestrictedAction.PRODUCTION_DEPLOYMENT,
            context=ctx,
            urgency=ApprovalUrgency.MEDIUM,
            artifact_version=instance.metadata.get("version", "2.0"),
            downstream_action=instance.downstream_action or "publish",
        )

        instance.founder_review_approval_id = approval_id

        # Add to Founder feed
        self._add_to_feed(
            item_type="approval",
            title=f"FINAL REVIEW: {instance.title}",
            summary=f"{instance.executive} requests final review. {qc_summary}. Output: {final_output[:200]}",
            pipeline_id=pipeline_id,
            approval_id=approval_id,
            severity="medium",
            requires_action=True,
            actionable=True,
        )

        # Notify founder-ready
        if self._on_founder_ready:
            await self._on_founder_ready(pipeline_id, instance, approval_id)

        return approval_id

    # ── Stage 10: Publish / Deploy / Schedule ──────────────────────────────

    async def complete_pipeline(
        self,
        pipeline_id: str,
        downstream_action: str = "",
    ) -> bool:
        """Complete the pipeline — publish, deploy, or schedule."""
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return False

        instance.stage = PipelineStage.PUBLISH
        instance.downstream_action = downstream_action
        instance.completed_at = datetime.now(timezone.utc)

        if self._on_pipeline_stage:
            await self._on_pipeline_stage(pipeline_id, instance)

        if self._on_pipeline_completed:
            await self._on_pipeline_completed(pipeline_id, instance)

        # Add to Founder feed
        self._add_to_feed(
            item_type="notification",
            title=f"Completed: {instance.title}",
            summary=f"Pipeline completed. Downstream action: {downstream_action or 'N/A'}",
            pipeline_id=pipeline_id,
            severity="info",
            requires_action=False,
        )

        return True

    async def cancel_pipeline(self, pipeline_id: str, reason: str = "") -> bool:
        """Cancel a pipeline."""
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return False

        instance.stage = PipelineStage.CANCELLED
        instance.cancelled = True
        instance.completed_at = datetime.now(timezone.utc)

        self._add_to_feed(
            item_type="notification",
            title=f"Cancelled: {instance.title}",
            summary=f"Cancelled. Reason: {reason or 'No reason provided'}",
            pipeline_id=pipeline_id,
            severity="high",
            requires_action=False,
        )

        return True

    async def fail_pipeline(self, pipeline_id: str, error: str) -> bool:
        """Mark a pipeline as failed."""
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return False

        instance.stage = PipelineStage.FAILED
        instance.failed = True
        instance.error = error
        instance.completed_at = datetime.now(timezone.utc)

        # Critical issues go to Founder feed
        self._add_to_feed(
            item_type="critical_issue",
            title=f"FAILED: {instance.title}",
            summary=f"Pipeline failed: {error[:300]}",
            pipeline_id=pipeline_id,
            severity="critical",
            requires_action=True,
        )

        return True

    # ── Founder FAST FEED ──────────────────────────────────────────────────

    def _add_to_feed(
        self,
        item_type: str,
        title: str,
        summary: str,
        pipeline_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        severity: str = "info",
        requires_action: bool = False,
        actionable: bool = False,
    ) -> str:
        """Add an item to the Founder's FAST FEED."""
        feed_id = f"feed-{uuid.uuid4().hex[:8]}"
        item = FounderFeedItem(
            feed_id=feed_id,
            item_type=item_type,
            title=title,
            summary=summary,
            pipeline_id=pipeline_id,
            approval_id=approval_id,
            severity=severity,
            requires_action=requires_action,
            actionable=actionable,
        )
        self._feed.append(item)
        return feed_id

    def get_feed(
        self,
        unread_only: bool = False,
        actionable_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get the Founder's FAST FEED.

        The FAST FEED shows only:
          - critical issues
          - approvals
          - important decisions
          - executive requests

        Everything else runs silently. Founder can open any item
        into its complete workspace.
        """
        items = list(self._feed)
        if unread_only:
            items = [i for i in items if not i.read]
        if actionable_only:
            items = [i for i in items if i.actionable]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return [i.to_dict() for i in items[:limit]]

    def mark_feed_read(self, feed_id: str) -> bool:
        """Mark a feed item as read."""
        for item in self._feed:
            if item.feed_id == feed_id:
                item.read = True
                return True
        return False

    def get_unread_count(self) -> int:
        """Get the number of unread feed items."""
        return sum(1 for i in self._feed if not i.read)

    # ── Approval UI Helpers ────────────────────────────────────────────────

    def get_approval_ui_context(
        self,
        pipeline_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the full context for the Approval UI.

        The UI shows:
          WHAT, WHY, WHO, EXPECTED_RESULT, RISK, COST, TIMELINE,
          SOURCE_MATERIAL, FINAL_OUTPUT

        Actions: APPROVE, REJECT, REQUEST CHANGES, DISCUSS
        """
        instance = self._pipelines.get(pipeline_id)
        if not instance:
            return None

        return {
            "pipeline_id": pipeline_id,
            "title": instance.title,
            "executive": instance.executive,
            "stage": instance.stage.value,
            "plan": instance.plan.to_dict() if instance.plan else None,
            "qc_passed": instance.qc_result.passed if instance.qc_result else None,
            "qc_summary": instance.qc_result.summary if instance.qc_result else "",
            "final_output": instance.final_output,
            "founder_approval_id": instance.founder_approval_id,
            "founder_review_approval_id": instance.founder_review_approval_id,
            "available_actions": [
                {"action": "approve", "label": "APPROVE"},
                {"action": "reject", "label": "REJECT"},
                {"action": "request_changes", "label": "REQUEST CHANGES"},
                {"action": "discuss", "label": "DISCUSS"},
            ],
            "created_at": instance.created_at.isoformat(),
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
        }

    # ── Query Methods ──────────────────────────────────────────────────────

    def get_pipelines_needing_approval(self) -> List[Dict[str, Any]]:
        """Get all pipelines waiting for Founder approval."""
        return [
            p.to_dict() for p in self._pipelines.values()
            if p.stage in (
                PipelineStage.FOUNDER_APPROVE,
                PipelineStage.FOUNDER_REVIEW,
            )
        ]

    def get_pipelines_in_qc(self) -> List[Dict[str, Any]]:
        """Get all pipelines currently in QC."""
        return [
            p.to_dict() for p in self._pipelines.values()
            if p.stage == PipelineStage.QC
        ]

    def get_active_pipelines(self) -> List[Dict[str, Any]]:
        """Get all active (not completed/cancelled/failed) pipelines."""
        terminal = {
            PipelineStage.COMPLETED,
            PipelineStage.CANCELLED,
            PipelineStage.FAILED,
            PipelineStage.PUBLISH,
        }
        return [
            p.to_dict() for p in self._pipelines.values()
            if p.stage not in terminal
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the Founder Gateway state."""
        total = len(self._pipelines)
        active = len(self.get_active_pipelines())
        awaiting_approval = len(self.get_pipelines_needing_approval())
        in_qc = len(self.get_pipelines_in_qc())
        completed = sum(
            1 for p in self._pipelines.values()
            if p.stage in (PipelineStage.COMPLETED, PipelineStage.PUBLISH)
        )
        failed_pipelines = sum(1 for p in self._pipelines.values() if p.failed)
        cancelled = sum(1 for p in self._pipelines.values() if p.cancelled)

        return {
            "total_pipelines": total,
            "active": active,
            "awaiting_founder_approval": awaiting_approval,
            "in_qc": in_qc,
            "completed": completed,
            "failed": failed_pipelines,
            "cancelled": cancelled,
            "feed_unread": self.get_unread_count(),
            "feed_total": len(self._feed),
        }