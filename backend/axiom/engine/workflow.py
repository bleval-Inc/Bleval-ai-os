"""Workflow Engine — full state machine for workflow execution.

Wired to the Dispatcher and EventEngine at the runtime level.

State machine transitions:

    PENDING --start()--> RUNNING --advance()--> RUNNING (next step)
                             |                        |
                             v                        v
                       AWAITING_APPROVAL          COMPLETED (last step)
                             |                        |
                      approve()/reject()              |
                             |                        v
                        RUNNING / CANCELLED        COMPLETED

                        RUNNING --[error]--> FAILED --retry()--> RUNNING
                        RUNNING --cancel()--> CANCELLED
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.config import settings
from axiom.models.configs import WorkflowDetail, WorkflowEntry, WorkflowIndex
from axiom.models.workflows import (
    ApprovalRequest,
    ApprovalStatus,
    StepStatus,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowStepState,
)
from axiom.registry.workflow import WorkflowRegistryLoader


class WorkflowEngine:
    """Manages the lifecycle of workflow instances."""

    def __init__(
        self,
        event_engine: Any = None,
        dispatcher: Any = None,
        approval_manager: Any = None,
    ) -> None:
        self._registry = WorkflowRegistryLoader()
        self._instances: Dict[str, WorkflowInstance] = {}
        self._approvals: Dict[str, ApprovalRequest] = {}
        self._event_engine = event_engine
        self._dispatcher = dispatcher
        self._approval_manager = approval_manager

    def set_event_engine(self, event_engine: Any) -> None:
        """Inject the event engine after construction (avoid circular imports)."""
        self._event_engine = event_engine

    def set_dispatcher(self, dispatcher: Any) -> None:
        """Inject the dispatcher after construction."""
        self._dispatcher = dispatcher

    def set_approval_manager(self, approval_manager: Any) -> None:
        """Inject the approval manager after construction."""
        self._approval_manager = approval_manager

    # ── Helpers ────────────────────────────────────────────────────────────

    async def _emit(self, event_type: str, instance: WorkflowInstance,
                    extra: Optional[Dict[str, Any]] = None) -> None:
        """Publish a workflow lifecycle event if the event engine is wired."""
        if self._event_engine is None:
            return
        try:
            payload = {
                "instance_id": instance.instance_id,
                "workflow_id": instance.workflow_id,
                "status": instance.status.value,
                "org": instance.org,
                "department": instance.department,
                **(extra or {}),
            }
            await self._event_engine.publish(
                event_type=event_type,
                source=f"workflow:{instance.instance_id}",
                payload=payload,
                correlation_id=instance.instance_id,
            )
        except Exception:
            pass  # Event emission is best-effort

    async def _dispatch_step(self, instance: WorkflowInstance, step_idx: int) -> None:
        """Dispatch the current step to the dispatcher if wired."""
        if self._dispatcher is None:
            return
        step = instance.steps[step_idx]
        try:
            task_id = await self._dispatcher.dispatch(
                agent_id=step.agent,
                action=step.step_name,
                workflow_instance_id=instance.instance_id,
                step_id=step.step_id,
                context=instance.context,
            )
            # Store the task_id on the step state for tracking
            self._dispatcher._tasks[task_id].workflow_instance_id = (  # noqa: private access is internal wiring
                instance.instance_id
            )
        except Exception:
            pass  # Dispatch failure is non-fatal for state transitions

    # ── Workflow Discovery ───────────────────────────────────────────────

    def get_index(self) -> WorkflowIndex:
        """Return the full workflow index."""
        return self._registry.load_index()

    def list_workflows(self) -> Dict[str, WorkflowEntry]:
        """Return all registered workflow definitions."""
        return self._registry.list_workflows()

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowEntry]:
        """Get a workflow definition by id."""
        return self._registry.get_workflow(workflow_id)

    def get_workflow_detail(self, workflow_id: str) -> Optional[WorkflowDetail]:
        """Get the detailed workflow definition."""
        return self._registry.load_detail(workflow_id)

    # ── Instance Lifecycle ───────────────────────────────────────────────

    def create_instance(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowInstance:
        """Create a new workflow instance from a workflow definition.

        All steps start as PENDING.  The instance is persisted to disk.
        """
        wf = self._registry.get_workflow(workflow_id)
        if wf is None:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        if not wf.steps:
            raise ValueError(f"Workflow {workflow_id} has no steps defined")

        instance_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        steps: List[WorkflowStepState] = []
        for i, step_def in enumerate(wf.steps):
            steps.append(WorkflowStepState(
                step_id=str(i + 1),
                step_name=step_def.name,
                agent=step_def.agent,
                status=StepStatus.PENDING,
            ))

        instance = WorkflowInstance(
            workflow_id=workflow_id,
            instance_id=instance_id,
            org=wf.org,
            department=wf.department,
            coordinator=wf.coordinator,
            status=WorkflowStatus.PENDING,
            steps=steps,
            current_step_index=0,
            context=context or {},
            created_at=now,
        )

        self._instances[instance_id] = instance
        self._persist(instance)
        return instance

    async def start(self, instance_id: str) -> bool:
        """Start a workflow instance.

        Transitions from PENDING -> RUNNING and dispatches the first step.
        Returns True if the workflow started successfully.
        """
        instance = self._get_instance(instance_id)
        if instance.status != WorkflowStatus.PENDING:
            raise ValueError(f"Cannot start workflow in status: {instance.status}")

        instance.status = WorkflowStatus.RUNNING
        instance.started_at = datetime.now(timezone.utc)

        await self._emit("workflow-started", instance)

        # Start the first step
        if instance.steps:
            await self._start_step(instance, 0)

        self._persist(instance)
        return True

    async def advance(
        self,
        instance_id: str,
        step_output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Advance to the next workflow step.

        Completes the current step, then starts the next one.
        If the current step is the last, the workflow completes.
        Returns True if the workflow is still running, False if completed.

        Raises ValueError if the step is not in IN_PROGRESS state.
        """
        instance = self._get_instance(instance_id)
        if instance.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot advance workflow in status: {instance.status}")

        # Guard: verify the current step is actually IN_PROGRESS
        current_step = instance.steps[instance.current_step_index]
        if current_step.status != StepStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot advance step {current_step.step_name}: "
                f"current status is {current_step.status.value}, "
                f"expected in_progress"
            )

        # Complete the current step
        current_step.status = StepStatus.COMPLETED
        current_step.completed_at = datetime.now(timezone.utc)
        if step_output:
            current_step.output = step_output

        await self._emit("step-completed", instance, {
            "step_id": current_step.step_id,
            "step_name": current_step.step_name,
            "agent": current_step.agent,
        })

        # Check if there are more steps
        next_idx = instance.current_step_index + 1
        if next_idx >= len(instance.steps):
            # Workflow complete
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now(timezone.utc)
            await self._emit("workflow-completed", instance)
            self._persist(instance)
            return False  # Workflow is done

        # Start the next step
        instance.current_step_index = next_idx
        await self._start_step(instance, next_idx)
        self._persist(instance)
        return True  # Still running

    async def fail_step(self, instance_id: str, error: str) -> None:
        """Mark the current step as failed.

        Transitions the workflow to FAILED status.
        """
        instance = self._get_instance(instance_id)
        if instance.current_step_index < len(instance.steps):
            step = instance.steps[instance.current_step_index]
            step.status = StepStatus.FAILED
            step.error = error

        instance.status = WorkflowStatus.FAILED
        instance.error = error
        instance.completed_at = datetime.now(timezone.utc)

        await self._emit("workflow-failed", instance, {"error": error})
        self._persist(instance)

    async def retry(self, instance_id: str) -> bool:
        """Retry a failed workflow step.

        Resets the failed step to PENDING and transitions back to RUNNING.
        Raises ValueError if retry_count exceeds max_retries.
        Returns True if retry was initiated.
        """
        instance = self._get_instance(instance_id)
        if instance.status != WorkflowStatus.FAILED:
            raise ValueError(f"Cannot retry workflow in status: {instance.status}")

        failed_step = instance.steps[instance.current_step_index]

        # Enforce retry limit
        if failed_step.retry_count >= 3:
            raise ValueError(
                f"Step {failed_step.step_name} has reached maximum retries "
                f"({failed_step.retry_count})"
            )

        failed_step.status = StepStatus.PENDING
        failed_step.error = None
        failed_step.retry_count += 1
        failed_step.started_at = None
        failed_step.completed_at = None

        instance.status = WorkflowStatus.RUNNING
        instance.error = None
        instance.completed_at = None

        # Re-start the failed step
        await self._start_step(instance, instance.current_step_index)

        await self._emit("workflow-retried", instance, {
            "retry_count": failed_step.retry_count,
            "step_name": failed_step.step_name,
        })
        self._persist(instance)
        return True

    async def cancel(self, instance_id: str) -> bool:
        """Cancel a running workflow. Async for consistency with other lifecycle methods."""
        instance = self._get_instance(instance_id)
        if instance.status not in (WorkflowStatus.RUNNING, WorkflowStatus.AWAITING_APPROVAL):
            raise ValueError(f"Cannot cancel workflow in status: {instance.status}")

        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.now(timezone.utc)

        # Mark remaining steps as skipped
        for i in range(instance.current_step_index, len(instance.steps)):
            step = instance.steps[i]
            if step.status in (StepStatus.PENDING, StepStatus.IN_PROGRESS):
                step.status = StepStatus.SKIPPED

        await self._emit("workflow-cancelled", instance)
        self._persist(instance)
        return True

    # ── Approval ─────────────────────────────────────────────────────────

    async def request_approval(
        self,
        instance_id: str,
        step_name: str = "",
        requested_by: str = "",
    ) -> ApprovalRequest:
        """Request human (or executive) approval to proceed.

        Pauses the workflow in AWAITING_APPROVAL status.
        """
        instance = self._get_instance(instance_id)
        if instance.status != WorkflowStatus.RUNNING:
            raise ValueError(f"Cannot request approval in status: {instance.status}")

        current_step = instance.steps[instance.current_step_index]
        current_step.status = StepStatus.AWAITING_INPUT
        instance.status = WorkflowStatus.AWAITING_APPROVAL

        approval = ApprovalRequest(
            approval_id=str(uuid.uuid4()),
            workflow_instance_id=instance_id,
            step_id=current_step.step_id,
            step_name=step_name or current_step.step_name,
            requested_by=requested_by,
            requested_at=datetime.now(timezone.utc),
            status=ApprovalStatus.PENDING,
        )

        self._approvals[approval.approval_id] = approval

        # Sync with approval manager if wired
        if self._approval_manager is not None:
            try:
                self._approval_manager.register(approval)
            except Exception:
                pass

        await self._emit("approval-requested", instance, {
            "approval_id": approval.approval_id,
            "step_name": approval.step_name,
        })
        self._persist(instance)
        return approval

    async def handle_approval(
        self,
        approval_id: str,
        approved: bool,
        by_reference: str = "",
        notes: Optional[str] = None,
    ) -> bool:
        """Handle an approval decision.

        If approved: resumes the workflow (RUNNING).
        If rejected: cancels the workflow (CANCELLED).
        Returns True if the workflow continues, False if cancelled.
        """
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ValueError(f"Unknown approval request: {approval_id}")

        instance = self._get_instance(approval.workflow_instance_id)

        if approved:
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = by_reference
            approval.approved_at = datetime.now(timezone.utc)
            approval.notes = notes

            instance.status = WorkflowStatus.RUNNING
            instance.approved_at = datetime.now(timezone.utc)

            # Resume the current step
            current_step = instance.steps[instance.current_step_index]
            current_step.status = StepStatus.IN_PROGRESS

            await self._emit("approval-granted", instance, {
                "approval_id": approval_id,
            })
            self._persist(instance)
            return True  # Workflow continues
        else:
            approval.status = ApprovalStatus.REJECTED
            approval.approved_by = by_reference
            approval.approved_at = datetime.now(timezone.utc)
            approval.notes = notes

            await self._emit("approval-rejected", instance, {
                "approval_id": approval_id,
            })
            await self.cancel(instance.instance_id)
            return False  # Workflow cancelled

    # ── Query ────────────────────────────────────────────────────────────

    def get_status(self, instance_id: str) -> Optional[WorkflowStatus]:
        """Get the current status of a workflow instance."""
        instance = self._instances.get(instance_id)
        if instance is None:
            instance = self._load_state(instance_id)
        if instance is None:
            return None
        return instance.status

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by id."""
        instance = self._instances.get(instance_id)
        if instance is None:
            instance = self._load_state(instance_id)
            if instance is not None:
                self._instances[instance_id] = instance
        return instance

    def list_instances(self, status: Optional[WorkflowStatus] = None) -> List[WorkflowInstance]:
        """List all active workflow instances, optionally filtered by status."""
        results = list(self._instances.values())
        if status is not None:
            results = [i for i in results if i.status == status]
        return results

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by id."""
        return self._approvals.get(approval_id)

    def list_approvals(self, status: Optional[ApprovalStatus] = None) -> List[ApprovalRequest]:
        """List all approval requests, optionally filtered by status."""
        results = list(self._approvals.values())
        if status is not None:
            results = [a for a in results if a.status == status]
        return results

    def find_instances_by_workflow(self, workflow_id: str) -> List[WorkflowInstance]:
        """Find all instances of a given workflow definition."""
        return [i for i in self._instances.values() if i.workflow_id == workflow_id]

    # ── Internal Helpers ─────────────────────────────────────────────────

    async def _start_step(self, instance: WorkflowInstance, step_idx: int) -> None:
        """Mark a step as in-progress and dispatch a task to the agent."""
        step = instance.steps[step_idx]
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now(timezone.utc)

        # Dispatch to agent via dispatcher if wired
        await self._dispatch_step(instance, step_idx)

        await self._emit("step-started", instance, {
            "step_id": step.step_id,
            "step_name": step.step_name,
            "agent": step.agent,
        })

    def _get_instance(self, instance_id: str) -> WorkflowInstance:
        """Get an instance, loading from disk if needed."""
        instance = self._instances.get(instance_id)
        if instance is None:
            instance = self._load_state(instance_id)
            if instance is None:
                raise ValueError(f"Unknown workflow instance: {instance_id}")
            self._instances[instance_id] = instance
        return instance

    # ── Persistence ──────────────────────────────────────────────────────

    def _persist(self, instance: WorkflowInstance) -> None:
        """Write workflow state to disk as JSON."""
        state_dir = settings.state_dir
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / f"{instance.instance_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(instance.model_dump_json())

    def _load_state(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Load workflow state from disk."""
        path = settings.state_dir / f"{instance_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WorkflowInstance(**data)
        except (json.JSONDecodeError, Exception):
            return None

    def load_all_persisted(self) -> List[WorkflowInstance]:
        """Load all persisted workflow instances from disk."""
        state_dir = settings.state_dir
        if not state_dir.exists():
            return []
        instances: List[WorkflowInstance] = []
        for path in sorted(state_dir.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                inst = WorkflowInstance(**data)
                instances.append(inst)
                self._instances[inst.instance_id] = inst
            except Exception as exc:
                # Log load failures but don't crash startup
                print(f"Warning: skipped corrupted state file {path}: {exc}")
                continue
        return instances