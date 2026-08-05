"""QC Specialist Agent handler — integrates QCManager with the SpecialistAgent system.

Each specialist agent type in Axiom OS can optionally register a custom handler.
The QC handler processes specialist tasks through the full QC Manager pipeline.

Specialist agents produce output → QC handler inspects → passes/fails → rework loop
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from axiom.engine.specialist_agent import AgentHandler
from axiom.models.agent_specialist import (
    SpecialistOutput,
    SpecialistTask,
    SpecialistType,
)
from axiom.models.qc import (
    QCCheckType,
    QCFinding,
    QCRequest,
    QCResult,
    QCScope,
    QCSeverity,
    QCStatus,
)
from axiom.runtime.qc_engine import QCManager


class QCSpecialistHandler(AgentHandler):
    """Custom handler for QC specialist agent tasks.

    Integrates the QCManager into the specialist agent dispatch pipeline.
    When a QC specialist task is dispatched, this handler:
      1. Creates a QCRequest from the task
      2. Submits it to the QC Manager
      3. Runs the full QC check suite
      4. Returns the QC result as SpecialistOutput
      5. On failure, the task is marked for rework (NEVER to Founder)
    """

    specialist_type: SpecialistType = SpecialistType.QC

    def __init__(self, qc_manager: QCManager) -> None:
        self._qc = qc_manager

    async def handle(
        self,
        task: SpecialistTask,
        intelligence: Any,
        tool_engine: Any,
    ) -> SpecialistOutput:
        """Process a QC specialist task.

        The task instruction should contain:
          - artifact content to inspect
          - artifact name/type
          - QC scope (defaults to WORKFLOW_OUTPUT)
          - client requirements (optional)
          - brand guidelines (optional)
        """
        # Build QC request from the task
        context = task.context or {}
        inputs = task.inputs or {}

        content = inputs.get("content", task.instruction)
        scope_str = context.get("qc_scope", context.get("scope", "workflow_output"))
        artifact_name = context.get("artifact_name", task.workflow_instance_id or "unknown")
        artifact_type = context.get("artifact_type", "agent_output")

        # Map scope string to QCScope enum
        scope = self._map_scope(scope_str)

        qc_request = QCRequest(
            artifact_id=task.task_id,
            artifact_name=artifact_name,
            artifact_type=artifact_type,
            artifact_content=content,
            scope=scope,
            artifact_version=context.get("version", ""),
            metadata={
                "workflow_instance_id": task.workflow_instance_id,
                "agent_id": task.agent_id,
                "specialist_type": task.specialist_type.value,
                "org_id": context.get("org_id", ""),
                "dept_id": context.get("dept_id", ""),
            },
            client_requirements=context.get("client_requirements"),
            brand_guidelines=context.get("brand_guidelines"),
        )

        # Submit to QC Manager
        qc_id = self._qc.submit(qc_request)

        # Run QC
        result = await self._qc.run_qc(qc_id)

        # Build specialist output
        output = SpecialistOutput(
            output_id=f"qc-{task.task_id}",
            specialist_type=SpecialistType.QC.value,
            task_id=task.task_id,
            workflow_instance_id=task.workflow_instance_id,
            content={
                "qc_id": qc_id,
                "passed": result.passed,
                "status": result.status.value,
                "summary": result.summary,
                "findings": [
                    {
                        "check_type": f.check_type.value,
                        "severity": f.severity.value,
                        "description": f.description,
                        "detail": f.detail,
                        "suggested_fix": f.suggested_fix,
                        "location": f.location,
                    }
                    for f in result.findings
                ],
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
                "retry_count": result.retry_count,
                "rework_history": self._qc.get_rework_history(qc_id),
            },
            metadata={
                "qc_scope": scope.value,
                "artifact_name": artifact_name,
                "artifact_type": artifact_type,
                "pass_threshold": "no_critical_or_high",
            },
            quality_score=1.0 if result.passed else 0.0,
            qc_passed=result.passed,
            created_at=datetime.now(timezone.utc),
        )

        return output

    def _map_scope(self, scope_str: str) -> QCScope:
        """Map a scope string to a QCScope enum value."""
        scope_map = {
            "client_deliverable": QCScope.CLIENT_DELIVERABLE,
            "proposal": QCScope.PROPOSAL,
            "public_content": QCScope.PUBLIC_CONTENT,
            "social_media": QCScope.SOCIAL_MEDIA,
            "client_facing_document": QCScope.CLIENT_FACING_DOCUMENT,
            "project_delivery": QCScope.PROJECT_DELIVERY,
            "production_deployment": QCScope.PRODUCTION_DEPLOYMENT,
            "high_risk_communication": QCScope.HIGH_RISK_COMMUNICATION,
            "internal_document": QCScope.INTERNAL_DOCUMENT,
            "code_review": QCScope.CODE_REVIEW,
            "workflow_output": QCScope.WORKFLOW_OUTPUT,
            "agent_output": QCScope.AGENT_OUTPUT,
        }
        return scope_map.get(scope_str, QCScope.WORKFLOW_OUTPUT)


class QCTaskInspector:
    """Standalone inspector that can QC any agent task or workflow output.

    This is designed to be called from within the autonomous workflow
    lifecycle or from agent dispatch pipelines to automatically QC
    all outputs before they proceed.
    """

    def __init__(self, qc_manager: QCManager) -> None:
        self._qc = qc_manager

    async def inspect_agent_output(
        self,
        agent_id: str,
        output_content: str,
        artifact_name: str = "",
        scope: QCScope = QCScope.AGENT_OUTPUT,
        workflow_instance_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QCResult:
        """QC an agent's output before it progresses in the workflow."""
        request = QCRequest(
            artifact_id=f"agent-{agent_id}-{datetime.now(timezone.utc).timestamp()}",
            artifact_name=artifact_name or f"Agent output: {agent_id}",
            artifact_type="agent_output",
            artifact_content=output_content,
            scope=scope,
            metadata={
                "agent_id": agent_id,
                "workflow_instance_id": workflow_instance_id,
                **(metadata or {}),
            },
        )
        qc_id = self._qc.submit(request)
        return await self._qc.run_qc(qc_id)

    async def inspect_workflow_output(
        self,
        workflow_id: str,
        instance_id: str,
        output_content: str,
        scope: QCScope = QCScope.WORKFLOW_OUTPUT,
    ) -> QCResult:
        """QC a workflow's output."""
        request = QCRequest(
            artifact_id=instance_id,
            artifact_name=f"Workflow output: {workflow_id}",
            artifact_type="workflow_output",
            artifact_content=output_content,
            scope=scope,
            metadata={
                "workflow_id": workflow_id,
                "instance_id": instance_id,
            },
        )
        qc_id = self._qc.submit(request)
        return await self._qc.run_qc(qc_id)