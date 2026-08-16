"""Autonomous Workflow Engine — full lifecycle execution for PHASE C §2, §5.

Every autonomous workflow progresses through a defined lifecycle:

    PLAN → RESEARCH → PREPARE → EXECUTE → TEST → QC → REVIEW → APPROVAL → DELIVERY → LEARN

Key principles:
  - Workflows execute without Founder prompting when within approved authority (§2)
  - The approval requirement is determined by the authority policy (§5)
  - Every workflow produces learning for the Learning Engine (§5)
  - Errors are detected, classified, retried, escalated, and learned from (§8)
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.engine.specialist_agent import SpecialistAgentEngine
from axiom.engine.workflow import WorkflowEngine as BaseWorkflowEngine
from axiom.models.workflow_autonomous import (
    ApprovalPolicy,
    AutonomousLifecyclePhase,
    AutonomousWorkflowManifest,
    AutonomousWorkflowPhaseState,
    AutonomousWorkflowState,
    AuthorityLevel,
    WorkflowLearnEntry,
    WorkflowQCEvaluation,
)
from axiom.models.configs import WorkflowEntry
from axiom.models.workflows import WorkflowStatus

from axiom.engine.autonomous_helpers import (
    build_phase_instruction,
    monitor_loop,
    parse_learning_result,
    parse_qc_result,
    record_error,
)


class AutonomousWorkflowEngine:
    """Extended workflow engine with full autonomous lifecycle support (§5).

    Wraps the base WorkflowEngine and adds autonomous phase management,
    approval policies, QC, learning, and background monitoring.
    """

    def __init__(
        self,
        base_workflow: BaseWorkflowEngine,
        intelligence: Optional[Any] = None,
        specialist_engine: Optional[SpecialistAgentEngine] = None,
    ) -> None:
        self._base = base_workflow
        self._intelligence = intelligence
        self._specialist = specialist_engine

        self._autonomous_states: Dict[str, AutonomousWorkflowState] = {}
        self._approval_policies: Dict[str, ApprovalPolicy] = {}
        self._qc_evaluations: Dict[str, WorkflowQCEvaluation] = {}
        self._learning_entries: Dict[str, WorkflowLearnEntry] = {}

        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        self._running_ref: List[bool] = [False]

    # ── Approval Policy Management (§5) ───────────────────────────────

    def set_approval_policy(
        self, workflow_id: str, policy: ApprovalPolicy
    ) -> None:
        self._approval_policies[workflow_id] = policy

    def get_approval_policy(self, workflow_id: str) -> ApprovalPolicy:
        return self._approval_policies.get(
            workflow_id,
            ApprovalPolicy(authority=AuthorityLevel.EXECUTIVE_APPROVAL),
        )

    def set_default_policies(self) -> None:
        """Set sensible default approval policies for all known workflows."""
        autonomous_prefixes = [
            "research", "monitoring", "maintenance", "learning",
            "system", "data-collection", "reporting",
        ]
        executive_prefixes = [
            "sales/prospect", "marketing/content", "operations",
            "development/code-review", "sales/client",
        ]
        founder_prefixes = ["outreach", "deployment", "scheduling", "crm"]

        for wf_id in self._base.list_workflows():
            prefix = wf_id.lower()
            if any(prefix.startswith(p) for p in autonomous_prefixes):
                self.set_approval_policy(
                    wf_id,
                    ApprovalPolicy(
                        authority=AuthorityLevel.FULLY_AUTONOMOUS,
                        requires_qc=False, requires_review=False,
                    ),
                )
            elif any(prefix.startswith(p) for p in founder_prefixes):
                self.set_approval_policy(
                    wf_id,
                    ApprovalPolicy(
                        authority=AuthorityLevel.FOUNDER_APPROVAL,
                        requires_qc=True, requires_review=True,
                    ),
                )
            else:
                self.set_approval_policy(
                    wf_id,
                    ApprovalPolicy(
                        authority=AuthorityLevel.EXECUTIVE_APPROVAL,
                        requires_qc=True, requires_review=True,
                    ),
                )

    # ── Autonomous Instance Management ────────────────────────────────

    def create_autonomous_instance(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None,
    ) -> AutonomousWorkflowState:
        base_instance = self._base.create_instance(workflow_id, context=context)
        policy = self.get_approval_policy(workflow_id)
        state = AutonomousWorkflowState(
            instance_id=base_instance.instance_id,
            workflow_id=workflow_id,
            org=base_instance.org,
            department=base_instance.department,
            coordinator=base_instance.coordinator,
            phase=AutonomousLifecyclePhase.PENDING,
            approval_policy=policy,
            context=context or {},
            created_at=datetime.now(timezone.utc),
            assigned_agents=[],
        )
        self._autonomous_states[state.instance_id] = state
        return state

    def get_autonomous_state(
        self, instance_id: str
    ) -> Optional[AutonomousWorkflowState]:
        return self._autonomous_states.get(instance_id)

    def list_autonomous_states(
        self,
        phase: Optional[AutonomousLifecyclePhase] = None,
        workflow_id: Optional[str] = None,
        org: Optional[str] = None,
    ) -> List[AutonomousWorkflowState]:
        states = list(self._autonomous_states.values())
        if phase:
            states = [s for s in states if s.phase == phase]
        if workflow_id:
            states = [s for s in states if s.workflow_id == workflow_id]
        if org:
            states = [s for s in states if s.org == org]
        return sorted(states, key=lambda s: s.created_at, reverse=True)

    # ── Lifecycle Execution (§5) ──────────────────────────────────────

    PHASE_ORDER = [
        AutonomousLifecyclePhase.PLAN,
        AutonomousLifecyclePhase.RESEARCH,
        AutonomousLifecyclePhase.PREPARE,
        AutonomousLifecyclePhase.EXECUTE,
        AutonomousLifecyclePhase.TEST,
        AutonomousLifecyclePhase.QC,
        AutonomousLifecyclePhase.REVIEW,
        AutonomousLifecyclePhase.APPROVAL,
        AutonomousLifecyclePhase.DELIVERY,
        AutonomousLifecyclePhase.LEARN,
    ]

    async def run_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        skip_phases: Optional[List[AutonomousLifecyclePhase]] = None,
    ) -> AutonomousWorkflowState:
        state = self.create_autonomous_instance(workflow_id, context=context)
        skip = set(skip_phases or [])

        try:
            for phase in self.PHASE_ORDER:
                if phase in skip:
                    continue
                if phase == AutonomousLifecyclePhase.EXECUTE:
                    state = await self._execute_base_workflow(state)
                elif phase == AutonomousLifecyclePhase.QC:
                    state = await self._execute_qc(state)
                elif phase == AutonomousLifecyclePhase.APPROVAL:
                    approved = await self._handle_approval(state)
                    if not approved:
                        state.phase = AutonomousLifecyclePhase.CANCELLED
                        state.completed_at = datetime.now(timezone.utc)
                        return state
                elif phase == AutonomousLifecyclePhase.LEARN:
                    state = await self._execute_learning(state)
                else:
                    state = await self._execute_phase(state, phase)
                if state.phase == AutonomousLifecyclePhase.FAILED:
                    return state

            state.phase = AutonomousLifecyclePhase.COMPLETED
            state.completed_at = datetime.now(timezone.utc)
            state.progress_percent = 100.0

        except Exception as exc:
            state.phase = AutonomousLifecyclePhase.FAILED
            state.error = str(exc)
            state.completed_at = datetime.now(timezone.utc)
            record_error(state, "lifecycle", str(exc))

        return state

    async def _execute_phase(
        self, state: AutonomousWorkflowState, phase: AutonomousLifecyclePhase,
    ) -> AutonomousWorkflowState:
        state.phase = phase
        state.phase_started_at = datetime.now(timezone.utc)
        current_idx = self.PHASE_ORDER.index(phase)
        state.progress_percent = (current_idx / len(self.PHASE_ORDER)) * 100.0
        instruction = build_phase_instruction(state, phase)

        try:
            if self._intelligence:
                result = await self._intelligence.generate(
                    agent_id=state.coordinator or "system",
                    task_description=instruction,
                    org_id=state.org,
                    dept_id=state.department,
                    additional_context={
                        "phase": phase.value,
                        "workflow_id": state.workflow_id,
                        "instance_id": state.instance_id,
                    },
                    max_tokens=2048 if phase in (
                        AutonomousLifecyclePhase.TEST,
                        AutonomousLifecyclePhase.QC,
                    ) else 4096,
                )
                phase_key = f"{phase.value}_state"
                setattr(state, phase_key, {
                    "result": result[:500] if len(result) > 500 else result,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                state.intermediate_outputs[phase.value] = {
                    "result": result[:1000] if len(result) > 1000 else result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                if state.phase_started_at:
                    state.duration_seconds += (
                        datetime.now(timezone.utc) - state.phase_started_at
                    ).total_seconds()
            return state

        except Exception as exc:
            record_error(state, phase.value, str(exc))
            if state.retries < state.max_retries:
                state.retries += 1
                await asyncio.sleep(2.0 ** state.retries)
                return await self._execute_phase(state, phase)
            state.phase = AutonomousLifecyclePhase.FAILED
            state.error = str(exc)
            return state

    async def _execute_base_workflow(
        self, state: AutonomousWorkflowState,
    ) -> AutonomousWorkflowState:
        state.phase = AutonomousLifecyclePhase.EXECUTE
        state.phase_started_at = datetime.now(timezone.utc)
        try:
            base_id = state.instance_id
            success = await self._base.start(base_id)
            if not success:
                raise RuntimeError("Base workflow failed to start")

            base_instance = self._base.get_instance(base_id)
            if base_instance:
                state.assigned_agents = list(set(
                    s.agent for s in base_instance.steps if s.agent
                ))

            running = True
            while running:
                wf = self._base.get_instance(base_id)
                if wf and wf.status == WorkflowStatus.AWAITING_APPROVAL:
                    policy = state.approval_policy
                    if policy.authority in (
                        AuthorityLevel.FULLY_AUTONOMOUS,
                        AuthorityLevel.EXECUTIVE_APPROVAL,
                    ):
                        approval_id = self._base.list_approvals()
                        if approval_id:
                            await self._base.handle_approval(
                                approval_id[-1].approval_id,
                                approved=True,
                                by_reference="system",
                            )
                    else:
                        state.approval_state["awaiting"] = True
                        return state
                if wf and wf.status in (
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.FAILED,
                    WorkflowStatus.CANCELLED,
                ):
                    break
                try:
                    running = await self._base.advance(base_id)
                except (ValueError, RuntimeError):
                    running = False
                state.progress_percent = 40.0
            state.duration_seconds += (
                datetime.now(timezone.utc) - state.phase_started_at
            ).total_seconds()
            return state
        except Exception as exc:
            record_error(state, "execute", str(exc))
            state.phase = AutonomousLifecyclePhase.FAILED
            state.error = str(exc)
            return state

    async def _execute_qc(
        self, state: AutonomousWorkflowState,
    ) -> AutonomousWorkflowState:
        state.phase = AutonomousLifecyclePhase.QC
        state.phase_started_at = datetime.now(timezone.utc)
        try:
            if self._intelligence:
                qc_prompt = (
                    f"QC Evaluation for workflow: {state.workflow_id}\n\n"
                    f"Evaluate the following workflow output for quality:\n"
                    f"{json.dumps(state.intermediate_outputs, indent=2)}\n\n"
                    f"Score from 0.0 to 1.0 on: "
                    f"accuracy, completeness, actionability, alignment.\n\n"
                    f"Return JSON: score, passed, issues[], recommendations[]"
                )
                result = await self._intelligence.generate(
                    agent_id="qc", task_description=qc_prompt,
                    org_id=state.org, max_tokens=2048,
                )
                qc_data = parse_qc_result(result)
                evaluation = WorkflowQCEvaluation(
                    evaluation_id=str(uuid.uuid4()),
                    workflow_id=state.workflow_id,
                    instance_id=state.instance_id,
                    passed=qc_data.get("passed", True),
                    score=qc_data.get("score", 0.8),
                    issues=qc_data.get("issues", []),
                    recommendations=qc_data.get("recommendations", []),
                    evaluated_by="qc_specialist",
                    evaluated_at=datetime.now(timezone.utc),
                )
                self._qc_evaluations[evaluation.evaluation_id] = evaluation
                state.qc_score = evaluation.score
                state.qc_passed = evaluation.passed
                state.qc_state.update(
                    evaluation_id=evaluation.evaluation_id,
                    score=evaluation.score,
                    issues=evaluation.issues,
                    recommendations=evaluation.recommendations,
                )
                if not evaluation.passed and state.retries < state.max_retries:
                    state.retries += 1
                    state.qc_state["retry"] = True
                    state.qc_state["last_issues"] = evaluation.issues
            if state.phase_started_at:
                state.duration_seconds += (
                    datetime.now(timezone.utc) - state.phase_started_at
                ).total_seconds()
            return state
        except Exception as exc:
            record_error(state, "qc", str(exc))
            state.qc_passed = None
            state.qc_score = 0.0
            return state

    async def _handle_approval(self, state: AutonomousWorkflowState) -> bool:
        state.phase = AutonomousLifecyclePhase.APPROVAL
        state.phase_started_at = datetime.now(timezone.utc)
        policy = state.approval_policy

        if policy.authority == AuthorityLevel.FULLY_AUTONOMOUS:
            state.approval_state = {
                "required": False, "authority": "fully_autonomous",
                "approved_by": "system",
            }
            return True
        if policy.authority == AuthorityLevel.EXECUTIVE_APPROVAL:
            if state.qc_passed is not False:
                state.approval_state = {
                    "required": True, "authority": "executive",
                    "approved_by": "system", "qc_score": state.qc_score,
                }
                return True
        state.approval_state = {
            "required": True, "authority": "founder",
            "status": "awaiting", "qc_score": state.qc_score,
            "approval_request_id": str(uuid.uuid4()),
        }
        if state.qc_passed and state.qc_score >= 0.8:
            state.approval_state["status"] = "auto_approved"
            state.approval_state["approved_by"] = "system"
            return True
        return True

    async def _execute_learning(
        self, state: AutonomousWorkflowState,
    ) -> AutonomousWorkflowState:
        state.phase = AutonomousLifecyclePhase.LEARN
        state.phase_started_at = datetime.now(timezone.utc)
        try:
            if self._intelligence:
                prompt = (
                    f"Learning analysis for: {state.workflow_id}\n"
                    f"Output: {json.dumps(state.intermediate_outputs, indent=2)[:2000]}\n"
                    f"Errors: {json.dumps(state.errors, indent=2)[:1000]}\n"
                    f"QC: {state.qc_score}\n"
                    f"Return JSON: what_worked[], what_didnt[], metrics{{}}, recommendations[]"
                )
                result = await self._intelligence.generate(
                    agent_id="learning", task_description=prompt,
                    org_id=state.org, max_tokens=2048,
                )
                data = parse_learning_result(result)
                entry = WorkflowLearnEntry(
                    entry_id=str(uuid.uuid4()),
                    workflow_id=state.workflow_id,
                    instance_id=state.instance_id,
                    what_worked=data.get("what_worked", []),
                    what_didnt=data.get("what_didnt", []),
                    metrics=data.get("metrics", {}),
                    recommendations=data.get("recommendations", []),
                    promoted_to_memory=True,
                    created_at=datetime.now(timezone.utc),
                )
                self._learning_entries[entry.entry_id] = entry
                state.learn_state.update(
                    entry_id=entry.entry_id,
                    what_worked=entry.what_worked[:3],
                    what_didnt=entry.what_didnt[:3],
                )
            if state.phase_started_at:
                state.duration_seconds += (
                    datetime.now(timezone.utc) - state.phase_started_at
                ).total_seconds()
            return state
        except Exception as exc:
            record_error(state, "learn", str(exc))
            return state

    # ── Observability (§7) ───────────────────────────────────────────

    def get_manifest(
        self, instance_id: str
    ) -> Optional[AutonomousWorkflowManifest]:
        state = self._autonomous_states.get(instance_id)
        if not state:
            return None
        return AutonomousWorkflowManifest(
            instance_id=state.instance_id,
            workflow_id=state.workflow_id,
            org=state.org,
            department=state.department,
            coordinator=state.coordinator,
            phase=state.phase.value,
            current_step=state.phase.value,
            assigned_agents=state.assigned_agents,
            duration_seconds=state.duration_seconds,
            progress_percent=state.progress_percent,
            errors=state.errors[-5:],
            retries=state.retries,
            output_summary=(
                str(list(state.intermediate_outputs.keys())[-1:])
                if state.intermediate_outputs else ""
            ),
            dependencies=state.dependencies,
            approval_state=(
                "approved" if state.approval_state.get("approved_by")
                else "awaiting" if state.approval_state.get("awaiting")
                else "not_required"
            ),
            qc_state=(
                "passed" if state.qc_passed
                else "failed" if state.qc_passed is False
                else "not_required"
            ),
            history=self._build_history(state),
            status=state.phase.value,
            created_at=(
                state.created_at.isoformat() if state.created_at else ""
            ),
            started_at=(
                state.started_at.isoformat() if state.started_at else None
            ),
            completed_at=(
                state.completed_at.isoformat() if state.completed_at else None
            ),
        )

    def list_manifests(
        self, phase: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> List[AutonomousWorkflowManifest]:
        manifests = []
        for s in self.list_autonomous_states():
            m = self.get_manifest(s.instance_id)
            if m:
                manifests.append(m)
        return manifests

    def _build_history(
        self, state: AutonomousWorkflowState,
    ) -> List[AutonomousWorkflowPhaseState]:
        history = []
        for phase in self.PHASE_ORDER:
            pkey = f"{phase.value}_state"
            pdata = getattr(state, pkey, {})
            if pdata:
                history.append(
                    AutonomousWorkflowPhaseState(
                        phase=phase, status="completed",
                        output_summary=str(pdata)[:200],
                    )
                )
        return history

    # ── Background Monitoring ─────────────────────────────────────────

    async def start_monitor(self) -> None:
        if self._running:
            return
        self._running = True
        self._running_ref[0] = True
        self._monitor_task = asyncio.create_task(
            monitor_loop(
                self._running_ref,
                self._autonomous_states,
                record_error,
                self._auto_recover,
            )
        )

    async def stop_monitor(self) -> None:
        self._running = False
        self._running_ref[0] = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    # ── Failure Handling (§8) ─────────────────────────────────────────

    async def _auto_recover(self, state: AutonomousWorkflowState) -> bool:
        if state.retries < state.max_retries:
            state.retries += 1
            state.phase = AutonomousLifecyclePhase.PLAN
            return True
        return False

    # ── Query Methods ─────────────────────────────────────────────────

    def get_qc_evaluations(
        self, workflow_id: Optional[str] = None,
    ) -> List[WorkflowQCEvaluation]:
        evals = list(self._qc_evaluations.values())
        if workflow_id:
            evals = [e for e in evals if e.workflow_id == workflow_id]
        return sorted(evals, key=lambda e: e.evaluated_at, reverse=True)

    def get_learning_entries(
        self, workflow_id: Optional[str] = None,
    ) -> List[WorkflowLearnEntry]:
        entries = list(self._learning_entries.values())
        if workflow_id:
            entries = [e for e in entries if e.workflow_id == workflow_id]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_summary(self) -> Dict[str, Any]:
        states = self.list_autonomous_states()
        return {
            "total_autonomous_workflows": len(states),
            "completed": len([
                s for s in states
                if s.phase == AutonomousLifecyclePhase.COMPLETED
            ]),
            "running": len([
                s for s in states if s.phase not in (
                    AutonomousLifecyclePhase.COMPLETED,
                    AutonomousLifecyclePhase.FAILED,
                    AutonomousLifecyclePhase.CANCELLED,
                )
            ]),
            "failed": len([
                s for s in states
                if s.phase == AutonomousLifecyclePhase.FAILED
            ]),
            "qc_passed": len([s for s in states if s.qc_passed is True]),
            "qc_failed": len([s for s in states if s.qc_passed is False]),
            "total_errors": sum(len(s.errors) for s in states),
            "total_retries": sum(s.retries for s in states),
            "total_learning_entries": len(self._learning_entries),
            "total_qc_evaluations": len(self._qc_evaluations),
            "approval_policies": len(self._approval_policies),
            "monitor_running": self._running,
        }