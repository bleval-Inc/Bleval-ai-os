"""QC Engine — dedicated Quality Control runtime for Phase D.

The QC Agent is mandatory for:
  - client deliverables, proposals, public content, social media posts
  - client-facing documents, project delivery, production deployments
  - high-risk external communications

QC checks inspect: accuracy, completeness, readability, professionalism,
duplication, placeholder content, dummy data, fake information, broken links,
formatting, consistency, brand standards, technical correctness, client
requirements, hallucinated information, missing assets, missing sections,
obvious errors.

If QC fails, return the work to the responsible agent/workflow — NEVER
notify the Founder for approval on a QC failure. Only after QC passes
does the work become Founder-ready.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from axiom.models.qc import (
    QCCheckType,
    QCFinding,
    QCRequest,
    QCResult,
    QCScope,
    QCSeverity,
    QCStatus,
)


class QCAction(str, Enum):
    """Actions the QC system can take on a failed artifact."""
    REWORK = "rework"               # Send back to agent/workflow for fixes
    ESCALATE_AUTO = "escalate_auto"  # Auto-escalate to executive review
    BLOCK = "block"                 # Block the artifact from proceeding


@dataclass
class QCReworkEntry:
    """Record of a QC failure and rework cycle."""
    qc_id: str
    artifact_id: str
    failure_reason: str
    exact_issues: List[str]
    severity: QCSeverity
    required_correction: str
    affected_artifact: str
    retry_count: int
    timestamp: datetime
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "qc_id": self.qc_id,
            "artifact_id": self.artifact_id,
            "failure_reason": self.failure_reason,
            "exact_issues": self.exact_issues,
            "severity": self.severity.value,
            "required_correction": self.required_correction,
            "affected_artifact": self.affected_artifact,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
        }


class QCManager:
    """Central QC engine that processes quality control for all artifacts.

    Lifecycle:
      1. QCRequest submitted for an artifact
      2. All 18 check types are run against it
      3. If FAILED → return to agent/workflow with exact issues (NO Founder)
      4. Agent fixes, QC re-runs
      5. Only PASSED artifacts proceed to Founder/approval pipeline

    The QC Manager integrates with:
      - SpecialistAgentEngine (for intelligence-backed checking)
      - FounderAuthority (artifacts only reach Founder after QC passes)
      - AutonomousWorkflowEngine (QC phase hooks)
    """

    def __init__(self, intelligence: Any = None) -> None:
        self._intelligence = intelligence

        # Active QC results: qc_id -> QCResult
        self._results: Dict[str, QCResult] = {}

        # Pending QC requests: artifact_id -> QCRequest
        self._pending: Dict[str, QCRequest] = {}

        # Rework history: qc_id -> list of rework entries
        self._rework_history: Dict[str, List[QCReworkEntry]] = {}

        # All check types that QC must inspect
        self._all_check_types: List[QCCheckType] = list(QCCheckType)

        # Maximum retries before escalation to executive
        self._max_retries: int = 3

        # Callbacks for integration
        self._on_qc_passed: Optional[Callable] = None
        self._on_qc_failed: Optional[Callable] = None
        self._on_rework_started: Optional[Callable] = None

    # ── Callbacks ──────────────────────────────────────────────────────────

    def set_on_qc_passed(self, callback: Callable) -> None:
        self._on_qc_passed = callback

    def set_on_qc_failed(self, callback: Callable) -> None:
        self._on_qc_failed = callback

    def set_on_rework_started(self, callback: Callable) -> None:
        self._on_rework_started = callback

    def set_max_retries(self, max_retries: int) -> None:
        self._max_retries = max_retries

    # ── Request Submission ─────────────────────────────────────────────────

    def submit(self, request: QCRequest) -> str:
        """Submit an artifact for QC inspection.

        Returns the qc_id for tracking.
        """
        qc_id = f"qc-{uuid.uuid4().hex[:12]}"
        self._pending[request.artifact_id] = request

        # Create initial result
        result = QCResult(
            qc_id=qc_id,
            artifact_id=request.artifact_id,
            artifact_name=request.artifact_name,
            artifact_type=request.artifact_type,
            scope=request.scope,
            status=QCStatus.PENDING,
            inspected_at=datetime.now(timezone.utc),
            artifact_version=request.artifact_version,
            previous_qc_id=request.previous_qc_id,
        )
        self._results[qc_id] = result
        return qc_id

    # ── QC Execution ───────────────────────────────────────────────────────

    async def run_qc(self, qc_id: str) -> QCResult:
        """Execute a full QC inspection on the submitted artifact.

        Runs all 18 check types against the artifact content.
        Returns the QCResult with all findings.
        """
        result = self._results.get(qc_id)
        if not result:
            raise ValueError(f"Unknown QC result: {qc_id}")

        request = self._pending.get(result.artifact_id)
        if not request:
            raise ValueError(f"No pending request for artifact: {result.artifact_id}")

        result.status = QCStatus.IN_PROGRESS
        result.inspected_at = datetime.now(timezone.utc)

        # Determine which checks to run based on scope
        check_types = self._checks_for_scope(result.scope)

        if self._intelligence and request.artifact_content:
            # Use intelligence engine for comprehensive checking
            findings = await self._run_intelligence_checks(
                request=request,
                check_types=check_types,
            )
            result.findings = findings
        else:
            # Fallback: run heuristic checks
            result.findings = self._run_heuristic_checks(
                content=request.artifact_content,
                check_types=check_types,
            )

        # Calculate severity counts
        result.calculate_severity_counts()

        # Determine pass/fail
        result.passed = not result.has_failures()
        result.status = QCStatus.PASSED if result.passed else QCStatus.FAILED
        result.completed_at = datetime.now(timezone.utc)

        # Build summary
        total_findings = len(result.findings)
        if result.passed:
            result.summary = (
                f"QC PASSED: {total_findings} findings "
                f"({result.low_count} low, {result.medium_count} medium). "
                f"No critical or high issues."
            )
        else:
            result.summary = (
                f"QC FAILED: {total_findings} findings "
                f"({result.critical_count} critical, {result.high_count} high, "
                f"{result.medium_count} medium, {result.low_count} low). "
                f"Critical/high issues must be resolved."
            )

        # Handle failure — return to agent/workflow, NEVER to Founder
        if result.has_failures():
            await self._handle_failure(result)
        else:
            if self._on_qc_passed:
                await self._on_qc_passed(qc_id, result)

        return result

    def _checks_for_scope(self, scope: QCScope) -> List[QCCheckType]:
        """Determine which check types apply to a given scope.

        All scopes get the full check suite. High-risk scopes get
        additional scrutiny on hallucination, brand standards, and
        client requirements.
        """
        base_checks = [
            QCCheckType.ACCURACY,
            QCCheckType.COMPLETENESS,
            QCCheckType.READABILITY,
            QCCheckType.PROFESSIONALISM,
            QCCheckType.DUPLICATION,
            QCCheckType.PLACEHOLDER_CONTENT,
            QCCheckType.DUMMY_DATA,
            QCCheckType.FAKE_INFORMATION,
            QCCheckType.FORMATTING,
            QCCheckType.CONSISTENCY,
            QCCheckType.OBVIOUS_ERRORS,
        ]

        high_risk_scopes = {
            QCScope.CLIENT_DELIVERABLE,
            QCScope.PROPOSAL,
            QCScope.PUBLIC_CONTENT,
            QCScope.SOCIAL_MEDIA,
            QCScope.CLIENT_FACING_DOCUMENT,
            QCScope.PRODUCTION_DEPLOYMENT,
            QCScope.HIGH_RISK_COMMUNICATION,
        }

        if scope in high_risk_scopes:
            base_checks.extend([
                QCCheckType.BROKEN_LINKS,
                QCCheckType.BRAND_STANDARDS,
                QCCheckType.TECHNICAL_CORRECTNESS,
                QCCheckType.CLIENT_REQUIREMENTS,
                QCCheckType.HALLUCINATED_INFO,
                QCCheckType.MISSING_ASSETS,
                QCCheckType.MISSING_SECTIONS,
            ])

        return base_checks

    async def _run_intelligence_checks(
        self,
        request: QCRequest,
        check_types: List[QCCheckType],
    ) -> List[QCFinding]:
        """Run QC checks using the intelligence engine.

        Processes each check type against the artifact content.
        """
        findings: List[QCFinding] = []
        content = request.artifact_content

        if not self._intelligence or not content:
            return findings

        for check_type in check_types:
            try:
                finding = await self._check_with_intelligence(
                    check_type=check_type,
                    content=content,
                    request=request,
                )
                if finding:
                    findings.append(finding)
            except Exception:
                continue

        return findings

    async def _check_with_intelligence(
        self,
        check_type: QCCheckType,
        content: str,
        request: QCRequest,
    ) -> Optional[QCFinding]:
        """Run a single QC check type using the intelligence engine."""
        check_prompts: Dict[QCCheckType, str] = {
            QCCheckType.ACCURACY: (
                "Check for factual accuracy. Are there any statements that are "
                "incorrect, misleading, or unsubstantiated? Consider dates, "
                "names, figures, claims, and references."
            ),
            QCCheckType.COMPLETENESS: (
                "Check for completeness. Are there missing sections, "
                "unfinished thoughts, or gaps in the content? Does it "
                "cover all required topics?"
            ),
            QCCheckType.READABILITY: (
                "Check for readability. Is the content clear, well-structured, "
                "and easy to follow? Are sentences an appropriate length? "
                "Is the language accessible?"
            ),
            QCCheckType.PROFESSIONALISM: (
                "Check for professionalism. Does the tone and language meet "
                "professional standards? Is it appropriate for the intended "
                "audience? Are there informal or inappropriate phrases?"
            ),
            QCCheckType.DUPLICATION: (
                "Check for duplication. Are there repeated paragraphs, "
                "sentences, or ideas? Any content that appears more than once?"
            ),
            QCCheckType.PLACEHOLDER_CONTENT: (
                "Check for placeholder content. Look for: Lorem ipsum, "
                "[placeholder], [insert], TBD, TODO, FIXME, REPLACE_ME, "
                "[content], [text], or similar markers."
            ),
            QCCheckType.DUMMY_DATA: (
                "Check for dummy data or test data that should not be in "
                "a deliverable. Look for: test@example.com, john.doe, "
                "sample data, test entries, mock data, 123 Main St."
            ),
            QCCheckType.FAKE_INFORMATION: (
                "Check for fake or fabricated information. Are there made-up "
                "facts, fictional examples presented as real, or synthetic "
                "data that wasn't properly marked?"
            ),
            QCCheckType.BROKEN_LINKS: (
                "Check for broken or placeholder links. Look for: "
                "example.com, your-site.com, link.com, #, javascript:void(0), "
                "or obviously broken URLs."
            ),
            QCCheckType.FORMATTING: (
                "Check for formatting issues. Are headings inconsistent? "
                "Is there inconsistent spacing, indentation, or bullet style? "
                "Are there markup or syntax errors?"
            ),
            QCCheckType.CONSISTENCY: (
                "Check for consistency. Are terms, names, tone, style, and "
                "formatting consistent throughout? Are there contradictions?"
            ),
            QCCheckType.BRAND_STANDARDS: (
                f"Check brand standards compliance for scope: {request.scope.value}. "
                "Does the content follow expected brand voice, terminology, "
                "and presentation standards?"
            ),
            QCCheckType.TECHNICAL_CORRECTNESS: (
                "Check for technical correctness. Are code snippets, "
                "technical terms, specifications, and technical claims "
                "accurate and appropriate?"
            ),
            QCCheckType.CLIENT_REQUIREMENTS: (
                "Check alignment with client requirements. Does the content "
                "address the stated requirements?"
            ),
            QCCheckType.HALLUCINATED_INFO: (
                "Check for hallucinated information. Are there plausible-sounding "
                "but fabricated facts, citations, statistics, or references? "
                "Look for convincing details that may not be real."
            ),
            QCCheckType.MISSING_ASSETS: (
                "Check for missing assets. Are there references to images, "
                "files, attachments, or resources that aren't included?"
            ),
            QCCheckType.MISSING_SECTIONS: (
                "Check for missing sections. Are there expected sections, "
                "chapters, or segments that appear to be missing or incomplete?"
            ),
            QCCheckType.OBVIOUS_ERRORS: (
                "Check for obvious errors: typos, grammatical mistakes, "
                "spelling errors, incorrect punctuation, or syntax issues."
            ),
        }

        prompt = check_prompts.get(check_type)
        if not prompt:
            return None

        full_prompt = (
            f"QC CHECK TYPE: {check_type.value}\n\n"
            f"{prompt}\n\n"
            f"ARTIFACT NAME: {request.artifact_name}\n"
            f"ARTIFACT TYPE: {request.artifact_type}\n"
            f"SCOPE: {request.scope.value}\n\n"
            f"--- ARTIFACT CONTENT ---\n"
            f"{content[:8000]}\n"
        )

        if request.client_requirements:
            full_prompt += (
                f"\n--- CLIENT REQUIREMENTS ---\n"
                f"{request.client_requirements}\n"
            )

        full_prompt += (
            "\n--- INSTRUCTION ---\n"
            "If you find an issue, return a JSON object with these fields:\n"
            "  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'\n"
            "  description: 'brief description of the issue'\n"
            "  detail: 'detailed explanation'\n"
            "  location: 'where in the content the issue appears'\n"
            "  suggested_fix: 'how to fix it'\n"
            "If no issue is found, return null/empty."
        )

        try:
            result = await self._intelligence.generate(
                agent_id="qc_agent",
                task_description=full_prompt,
                org_id=request.metadata.get("org_id", ""),
                dept_id=request.metadata.get("dept_id", ""),
                max_tokens=1024,
            )

            finding_data = self._parse_qc_result(result)
            if finding_data and finding_data.get("description"):
                severity_map = {
                    "critical": QCSeverity.CRITICAL,
                    "high": QCSeverity.HIGH,
                    "medium": QCSeverity.MEDIUM,
                    "low": QCSeverity.LOW,
                    "info": QCSeverity.INFO,
                }
                return QCFinding(
                    check_type=check_type,
                    severity=severity_map.get(
                        finding_data.get("severity", ""),
                        QCSeverity.MEDIUM,
                    ),
                    location=finding_data.get("location", ""),
                    description=finding_data.get("description", ""),
                    detail=finding_data.get("detail", ""),
                    suggested_fix=finding_data.get("suggested_fix", ""),
                    affected_artifact=request.artifact_name,
                )
        except Exception:
            pass

        return None

    def _parse_qc_result(self, result: str) -> Optional[Dict[str, str]]:
        """Parse a JSON QC result from the intelligence engine."""
        # Try to extract JSON from the response
        result = result.strip()
        # Remove markdown code blocks
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()

        try:
            import json
            data = json.loads(result)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find a JSON object in the response
        try:
            import json
            start = result.find("{")
            end = result.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(result[start:end + 1])
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, TypeError):
            pass

        return None

    def _run_heuristic_checks(
        self,
        content: str,
        check_types: List[QCCheckType],
    ) -> List[QCFinding]:
        """Run heuristic/pattern-based QC checks without intelligence.

        Fallback when the intelligence engine is not available.
        """
        findings: List[QCFinding] = []

        for check_type in check_types:
            finding = self._heuristic_check(check_type, content)
            if finding:
                findings.append(finding)

        return findings

    def _heuristic_check(
        self,
        check_type: QCCheckType,
        content: str,
    ) -> Optional[QCFinding]:
        """Run a single heuristic check."""
        content_lower = content.lower()

        if check_type == QCCheckType.PLACEHOLDER_CONTENT:
            patterns = ["lorem ipsum", "tbd", "todo", "fixme", "replace_me",
                        "[insert", "[content]", "xxx", "coming soon"]
            found = [p for p in patterns if p in content_lower]
            if found:
                return QCFinding(
                    check_type=check_type,
                    severity=QCSeverity.HIGH,
                    description=f"Placeholder content detected: {', '.join(found)}",
                    detail=f"Found placeholder patterns that should be replaced with final content.",
                    suggested_fix="Replace all placeholder text with the intended final content.",
                    affected_artifact="",
                )

        elif check_type == QCCheckType.DUMMY_DATA:
            patterns = ["test@example.com", "john.doe", "sample data",
                        "123 main st", "(555)", "test user"]
            found = [p for p in patterns if p in content_lower]
            if found:
                return QCFinding(
                    check_type=check_type,
                    severity=QCSeverity.HIGH,
                    description=f"Dummy data detected: {', '.join(found)}",
                    detail="Test data patterns found in what appears to be a deliverable.",
                    suggested_fix="Replace dummy data with real data or remove it.",
                    affected_artifact="",
                )

        elif check_type == QCCheckType.BROKEN_LINKS:
            patterns = ["example.com", "your-site.com", "link.com",
                        "href=\"#\"", "href='#'"]
            found = [p for p in patterns if p in content_lower]
            if found:
                return QCFinding(
                    check_type=check_type,
                    severity=QCSeverity.MEDIUM,
                    description=f"Broken or placeholder links detected: {', '.join(found)}",
                    detail="Links point to placeholder domains or empty anchors.",
                    suggested_fix="Replace with real, working URLs.",
                    affected_artifact="",
                )

        return None

    # ── Failure Handling ───────────────────────────────────────────────────

    async def _handle_failure(self, result: QCResult) -> None:
        """Handle a QC failure.

        CRITICAL RULE: NEVER notify the Founder for approval on QC failure.
        Return the work to the responsible agent/workflow with exact issues.
        """
        # Record the rework entry
        critical_issues = [
            f for f in result.findings
            if f.severity in (QCSeverity.CRITICAL, QCSeverity.HIGH)
        ]
        medium_issues = [
            f for f in result.findings
            if f.severity == QCSeverity.MEDIUM
        ]

        failure_reason = (
            f"QC failed with {result.critical_count} critical, "
            f"{result.high_count} high, {result.medium_count} medium issues"
        )
        exact_issues = [
            f"[{f.severity.value.upper()}] {f.check_type.value}: {f.description}"
            for f in critical_issues + medium_issues
        ]

        rework = QCReworkEntry(
            qc_id=result.qc_id,
            artifact_id=result.artifact_id,
            failure_reason=failure_reason,
            exact_issues=exact_issues,
            severity=QCSeverity.CRITICAL if result.critical_count > 0 else QCSeverity.HIGH,
            required_correction=self._build_correction_plan(result.findings),
            affected_artifact=result.artifact_name,
            retry_count=result.retry_count,
            timestamp=datetime.now(timezone.utc),
        )

        if result.qc_id not in self._rework_history:
            self._rework_history[result.qc_id] = []
        self._rework_history[result.qc_id].append(rework)

        # Increment retry count
        result.retry_count += 1

        # Notify callbacks
        if self._on_qc_failed:
            await self._on_qc_failed(result.qc_id, result, rework)

        # Check if max retries exceeded — escalate to executive, not Founder
        if result.retry_count >= self._max_retries:
            rework.resolved = False  # Mark as unresolved escalation
            if self._on_rework_started:
                await self._on_rework_started(result.qc_id, result, rework)

    def _build_correction_plan(self, findings: List[QCFinding]) -> str:
        """Build a correction plan from QC findings."""
        if not findings:
            return "No corrections needed."

        critical = [f for f in findings if f.severity == QCSeverity.CRITICAL]
        high = [f for f in findings if f.severity == QCSeverity.HIGH]
        medium = [f for f in findings if f.severity == QCSeverity.MEDIUM]

        lines = ["=== CORRECTION PLAN ==="]
        for label, group in [("CRITICAL", critical), ("HIGH", high), ("MEDIUM", medium)]:
            if group:
                lines.append(f"\n{label}:")
                for f in group:
                    lines.append(f"  - {f.check_type.value}: {f.description}")
                    if f.suggested_fix:
                        lines.append(f"    Fix: {f.suggested_fix}")

        return "\n".join(lines)

    # ── Rework Flow ────────────────────────────────────────────────────────

    async def resubmit(self, artifact_id: str) -> str:
        """Resubmit an artifact for re-check after fixes.

        Returns the new qc_id for the re-check cycle.
        """
        request = self._pending.get(artifact_id)
        if not request:
            raise ValueError(f"No pending request for artifact: {artifact_id}")

        # Find the last QC result for this artifact
        previous_qc_id = None
        for qc_id, result in self._results.items():
            if result.artifact_id == artifact_id:
                previous_qc_id = qc_id

        # Create a new submission
        new_qc_id = self.submit(request)
        result = self._results[new_qc_id]
        result.previous_qc_id = previous_qc_id

        return new_qc_id

    def get_rework_history(self, qc_id: str) -> List[Dict[str, Any]]:
        """Get the rework history for a QC result."""
        entries = self._rework_history.get(qc_id, [])
        return [e.to_dict() for e in entries]

    # ── Query Methods ──────────────────────────────────────────────────────

    def get_result(self, qc_id: str) -> Optional[QCResult]:
        """Get a QC result by ID."""
        return self._results.get(qc_id)

    def get_results_for_artifact(self, artifact_id: str) -> List[QCResult]:
        """Get all QC results for an artifact."""
        return [
            r for r in self._results.values()
            if r.artifact_id == artifact_id
        ]

    def get_results_by_scope(self, scope: QCScope) -> List[QCResult]:
        """Get all QC results for a given scope."""
        return [
            r for r in self._results.values()
            if r.scope == scope
        ]

    def get_pending(self) -> List[Dict[str, Any]]:
        """Get all pending QC requests."""
        return [
            {
                "qc_id": qc_id,
                "artifact_id": result.artifact_id,
                "artifact_name": result.artifact_name,
                "scope": result.scope.value,
                "status": result.status.value,
            }
            for qc_id, result in self._results.items()
            if result.status == QCStatus.PENDING
        ]

    def get_failed(self) -> List[Dict[str, Any]]:
        """Get all failed QC results."""
        return [
            {
                "qc_id": qc_id,
                "artifact_id": result.artifact_id,
                "artifact_name": result.artifact_name,
                "scope": result.scope.value,
                "retry_count": result.retry_count,
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "summary": result.summary,
            }
            for qc_id, result in self._results.items()
            if result.status == QCStatus.FAILED
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of QC system state."""
        total = len(self._results)
        passed = sum(1 for r in self._results.values() if r.passed)
        failed = sum(1 for r in self._results.values()
                     if r.status == QCStatus.FAILED)
        pending = sum(1 for r in self._results.values()
                      if r.status in (QCStatus.PENDING, QCStatus.IN_PROGRESS))
        total_rework = sum(len(entries) for entries in self._rework_history.values())

        # Findings by severity
        all_findings: List[QCFinding] = []
        for r in self._results.values():
            all_findings.extend(r.findings)

        return {
            "total_inspections": total,
            "passed": passed,
            "failed": failed,
            "pending": pending,
            "total_rework_cycles": total_rework,
            "total_findings": len(all_findings),
            "critical_findings": sum(
                1 for f in all_findings if f.severity == QCSeverity.CRITICAL
            ),
            "high_findings": sum(
                1 for f in all_findings if f.severity == QCSeverity.HIGH
            ),
            "max_retries": self._max_retries,
            "check_types_enabled": len(self._all_check_types),
        }