"""Approval Manager — workflow approval lifecycle management.

Manages the lifecycle of approval requests created during workflow execution.
Integrates with the Executive Engine for routing approval requests to the
appropriate executive or human.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.models.workflows import ApprovalRequest, ApprovalStatus


class ApprovalManager:
    """Manages approval requests for workflow checkpoints."""

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._approvals: Dict[str, ApprovalRequest] = {}

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by id."""
        return self._approvals.get(approval_id)

    def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        workflow_instance_id: Optional[str] = None,
    ) -> List[ApprovalRequest]:
        """List approval requests, optionally filtered."""
        results = list(self._approvals.values())
        if status is not None:
            results = [a for a in results if a.status == status]
        if workflow_instance_id is not None:
            results = [a for a in results if a.workflow_instance_id == workflow_instance_id]
        return results

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Return all pending approval requests."""
        return self.list_approvals(status=ApprovalStatus.PENDING)

    async def approve(self, approval_id: str, by: str, notes: Optional[str] = None) -> bool:
        """Approve a pending request.

        Returns True if the workflow continues, False if cancelled.
        """
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return False

        return await wf_engine.handle_approval(
            approval_id=approval_id,
            approved=True,
            by=by,
            notes=notes,
        )

    async def reject(self, approval_id: str, by: str, reason: Optional[str] = None) -> bool:
        """Reject a pending request.

        Returns False (the workflow is cancelled).
        """
        wf_engine = getattr(self._runtime, "workflow", None)
        if wf_engine is None:
            return False

        return await wf_engine.handle_approval(
            approval_id=approval_id,
            approved=False,
            by=by,
            notes=reason,
        )

    def register(self, approval: ApprovalRequest) -> None:
        """Register an approval request (called by the workflow engine)."""
        self._approvals[approval.approval_id] = approval

    def set_workflow_engine(self, wf_engine: Any) -> None:
        """Inject the workflow engine reference."""
        self._wf_engine = wf_engine