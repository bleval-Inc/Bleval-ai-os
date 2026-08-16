"""QC-to-Learning Pipeline — connects Quality Control failures to the Learning Engine.

Every QC check failure becomes a learning signal that:
1. Creates/updates patterns in the Learning Engine
2. Generates recommendations for remediation
3. Triggers learning cycles
4. Feeds into executive intelligence for decision support

This ensures QC is not just a gate — it's a teacher.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.engine.learning import LearningEngine
from axiom.models.learning import (
    DetectedPattern,
    LearningRecommendation,
    LearningSource,
    PatternSeverity,
    RecommendationStatus,
)


class QCtoLearningPipeline:
    """Pipeline that converts QC results into learning signals.

    Flow:
    QC Check → Submission Result → This Pipeline → Learning Engine
    """

    def __init__(self, learning_engine: LearningEngine, runtime: Any = None) -> None:
        self.learning = learning_engine
        self.runtime = runtime
        self._enabled = True

    async def process_qc_result(
        self,
        qc_id: str,
        artifact_name: str,
        artifact_type: str,
        passed: bool,
        scope: str,
        findings: List[Dict[str, Any]],
        retry_count: int = 0,
        workflow_id: str = "",
        workflow_instance_id: str = "",
    ) -> None:
        """Process a QC result and feed it into the Learning Engine.

        This is the main entry point — called whenever a QC check completes.
        """
        if not self._enabled:
            return

        if passed:
            # Record success pattern
            await self._record_qc_success(
                qc_id, artifact_name, scope, workflow_id, workflow_instance_id
            )
        else:
            # Process each failure finding as a learning signal
            for finding in findings:
                await self._process_qc_failure(
                    qc_id=qc_id,
                    artifact_name=artifact_name,
                    artifact_type=artifact_type,
                    scope=scope,
                    finding=finding,
                    retry_count=retry_count,
                    workflow_id=workflow_id,
                    workflow_instance_id=workflow_instance_id,
                )

            # Also record the overall failure pattern
            await self._record_qc_failure_pattern(
                qc_id, artifact_name, scope, findings, retry_count,
                workflow_id, workflow_instance_id
            )

    async def _process_qc_failure(
        self,
        qc_id: str,
        artifact_name: str,
        artifact_type: str,
        scope: str,
        finding: Dict[str, Any],
        retry_count: int,
        workflow_id: str,
        workflow_instance_id: str,
    ) -> None:
        """Process a single QC failure finding into learning patterns."""
        check_type = finding.get("check_type", "unknown")
        severity = finding.get("severity", "medium")
        message = finding.get("message", "")

        # Detect/update pattern for this failure type
        pattern_type = self._map_check_type_to_pattern(check_type)
        pattern_severity = self._map_severity_to_pattern(severity)

        pattern = self._get_or_create_qc_pattern(
            pattern_type=pattern_type,
            title=f"QC Failure: {check_type} in {scope}",
            severity=pattern_severity,
            entities=[artifact_name, scope, artifact_type],
        )

        pattern.description = (
            f"QC check '{check_type}' failed on {artifact_name} ({artifact_type}) "
            f"in scope '{scope}'. Message: {message[:200]}"
        )
        pattern.frequency += 1
        pattern.last_detected = datetime.now(timezone.utc)
        pattern.evidence.append(
            f"qc_id={qc_id}, severity={severity}, retries={retry_count}"
        )
        pattern.impact_score = self._calculate_impact(severity, retry_count)

        # Generate recommendation if this is a recurring issue
        if pattern.frequency >= 2 or severity in ("critical", "high"):
            await self._generate_qc_recommendation(pattern, finding, artifact_name, scope)

    async def _record_qc_failure_pattern(
        self,
        qc_id: str,
        artifact_name: str,
        scope: str,
        findings: List[Dict[str, Any]],
        retry_count: int,
        workflow_id: str,
        workflow_instance_id: str,
    ) -> None:
        """Record an overall failure pattern for this QC submission."""
        critical_count = sum(1 for f in findings if f.get("severity") == "critical")
        high_count = sum(1 for f in findings if f.get("severity") == "high")
        total_findings = len(findings)

        # Create pattern for repeated failures
        if retry_count > 0:
            pattern = self._get_or_create_qc_pattern(
                pattern_type="error",
                title=f"Repeated QC failures: {artifact_name} in {scope}",
                severity=PatternSeverity.CRITICAL if critical_count > 0 else PatternSeverity.WARNING,
                entities=[artifact_name, scope, workflow_id] if workflow_id else [artifact_name, scope],
            )

            pattern.description = (
                f"Artifact '{artifact_name}' failed QC {retry_count + 1} times "
                f"in scope '{scope}'. {critical_count} critical, {high_count} high, "
                f"{total_findings - critical_count - high_count} medium/low findings."
            )
            pattern.frequency += 1
            pattern.last_detected = datetime.now(timezone.utc)
            pattern.evidence.append(
                f"qc_id={qc_id}, finding_count={total_findings}, "
                f"retries={retry_count}, workflow={workflow_id}"
            )
            pattern.impact_score = min(0.9, 0.3 + retry_count * 0.15 + critical_count * 0.2)

            if pattern.frequency >= 2:
                await self._generate_qc_recommendation(pattern, {
                    "check_type": "repeated_failure",
                    "message": f"Artifact failed {retry_count + 1} times",
                }, artifact_name, scope)

    async def _record_qc_success(
        self,
        qc_id: str,
        artifact_name: str,
        scope: str,
        workflow_id: str,
        workflow_instance_id: str,
    ) -> None:
        """Record a QC success as a positive learning signal."""
        # Detect consistent success patterns
        pattern = self._get_or_create_qc_pattern(
            pattern_type="learning",
            title=f"Consistent QC pass: {artifact_name} in {scope}",
            severity=PatternSeverity.LEARNING,
            entities=[artifact_name, scope],
        )

        pattern.description = (
            f"Artifact '{artifact_name}' passed QC in scope '{scope}' "
            f"on first attempt (qc_id: {qc_id[:8]})"
        )
        pattern.frequency += 1
        pattern.last_detected = datetime.now(timezone.utc)
        pattern.impact_score = 0.3 + min(0.3, pattern.frequency * 0.05)

        # Promote to knowledge if consistently passing
        if pattern.frequency >= 5:
            await self._promote_qc_success_to_knowledge(pattern, artifact_name, scope)

    async def _generate_qc_recommendation(
        self,
        pattern: DetectedPattern,
        finding: Dict[str, Any],
        artifact_name: str,
        scope: str,
    ) -> Optional[LearningRecommendation]:
        """Generate a recommendation from a QC failure pattern."""
        rec = self.learning.recommendation_engine.generate(pattern)
        if rec:
            # Enrich with QC-specific details
            rec.target_entity_id = artifact_name
            rec.target_entity_type = "qc_scope"
            rec.change_type = "modify"
            rec.description += (
                f"\n\n**QC Context:**\n"
                f"- Artifact: {artifact_name}\n"
                f"- Scope: {scope}\n"
                f"- Check type: {finding.get('check_type', 'unknown')}\n"
                f"- Severity: {finding.get('severity', 'unknown')}"
            )
            rec.suggested_action = self._get_qc_suggested_action(finding, pattern)
            self.learning.recommendation_engine.register(rec)
            self.learning.recommendation_engine.propose(rec.recommendation_id)

            # Auto-approve high-confidence QC recommendations
            if rec.confidence >= 0.85:
                self.learning.recommendation_engine.approve(rec.recommendation_id, by="qc_pipeline")

            return rec
        return None

    async def _promote_qc_success_to_knowledge(
        self,
        pattern: DetectedPattern,
        artifact_name: str,
        scope: str,
    ) -> None:
        """Promote a consistent QC success pattern to organizational knowledge."""
        content = (
            f"**QC Success Pattern**\n\n"
            f"Artifact `{artifact_name}` in scope `{scope}` has passed QC "
            f"consistently ({pattern.frequency} consecutive passes).\n\n"
            f"This indicates the production process for this artifact type is stable "
            f"and meets quality standards. Consider this pattern as a reference "
            f"for similar artifacts.\n\n"
            f"**Generated from:** QC pipeline learning signal\n"
            f"**Confidence:** {pattern.impact_score:.0%}"
        )

        entry = self.learning.knowledge_consolidator.promote_recommendation(
            recommendation=type('obj', (object,), {
                'title': pattern.title,
                'confidence': pattern.impact_score,
                'target_entity_id': artifact_name,
            })(),
            content=content,
        )

        if entry:
            self.learning._state.total_knowledge_entries += 1

    def _get_qc_suggested_action(
        self,
        finding: Dict[str, Any],
        pattern: DetectedPattern,
    ) -> str:
        """Generate a QC-specific suggested action."""
        check_type = finding.get("check_type", "")
        severity = finding.get("severity", "medium")

        if "security" in check_type.lower() or "secret" in check_type.lower():
            return "Review security scanning rules and ensure no credentials/tokens in code"
        elif "style" in check_type.lower() or "lint" in check_type.lower():
            return "Run auto-formatter and update linting rules if patterns are consistent"
        elif "test" in check_type.lower():
            return "Investigate test flakiness or update test expectations"
        elif "type" in check_type.lower():
            return "Fix type annotations or update type checking configuration"
        elif "performance" in check_type.lower():
            return "Profile and optimize the flagged code paths"
        elif severity == "critical":
            return "Immediate investigation required — critical quality gate failure"
        elif severity == "high":
            return "High-priority fix needed before production deployment"
        else:
            return "Review QC findings and adjust artifact or check configuration"

    def _map_check_type_to_pattern(self, check_type: str) -> str:
        """Map QC check type to learning pattern type."""
        mapping = {
            "security": "error",
            "secret": "error",
            "vulnerability": "error",
            "style": "optimization",
            "lint": "optimization",
            "format": "optimization",
            "test": "error",
            "coverage": "optimization",
            "type": "error",
            "typing": "error",
            "performance": "bottleneck",
            "benchmark": "bottleneck",
            "dependency": "error",
            "license": "optimization",
        }
        for key, val in mapping.items():
            if key in check_type.lower():
                return val
        return "error"

    def _map_severity_to_pattern(self, severity: str) -> PatternSeverity:
        """Map QC severity to pattern severity."""
        mapping = {
            "critical": PatternSeverity.CRITICAL,
            "high": PatternSeverity.WARNING,
            "medium": PatternSeverity.OPTIMIZATION,
            "low": PatternSeverity.INFO,
            "info": PatternSeverity.INFO,
        }
        return mapping.get(severity.lower(), PatternSeverity.WARNING)

    def _calculate_impact(self, severity: str, retry_count: int) -> float:
        """Calculate impact score from severity and retry count."""
        base_impact = {
            "critical": 0.8,
            "high": 0.6,
            "medium": 0.4,
            "low": 0.2,
            "info": 0.1,
        }.get(severity.lower(), 0.3)

        retry_bonus = min(0.2, retry_count * 0.05)
        return min(1.0, base_impact + retry_bonus)

    def _get_or_create_qc_pattern(
        self,
        pattern_type: str,
        title: str,
        severity: PatternSeverity,
        entities: List[str],
    ) -> DetectedPattern:
        """Get existing QC pattern or create new one."""
        return self.learning.pattern_detector._get_or_create(
            pattern_type=pattern_type,
            title=title,
            severity=severity,
            entities=entities,
        )

    async def process_qc_feedback(
        self,
        pattern_id: str,
        action: str,  # "fixed" | "false_positive" | "configuration_changed"
        details: str = "",
    ) -> None:
        """Process human feedback on a QC pattern.

        Called when Founder/executive takes action on a QC recommendation.
        This closes the learning loop.
        """
        patterns = self.learning.get_patterns()
        pattern = next((p for p in patterns if p.pattern_id == pattern_id), None)
        if not pattern:
            return

        if action == "fixed":
            # Mark recommendations as applied
            recs = self.learning.get_recommendations(
                status=RecommendationStatus.APPROVED
            )
            for rec in recs:
                if rec.source_pattern_id == pattern_id:
                    self.learning.recommendation_engine.mark_applied(rec.recommendation_id)

            # Record successful resolution
            pattern.impact_score = max(0.1, pattern.impact_score * 0.5)

        elif action == "false_positive":
            # Reduce pattern impact
            pattern.frequency = max(1, pattern.frequency - 1)
            pattern.impact_score = max(0.1, pattern.impact_score * 0.3)

        elif action == "configuration_changed":
            # Pattern is still valid but check was updated
            pattern.evidence.append(f"config_changed: {details}")


class QCtrendAnalyzer:
    """Analyzes QC trends over time to predict quality issues."""

    def __init__(self, learning_engine: LearningEngine) -> None:
        self.learning = learning_engine

    def analyze_qc_pass_rate_trend(
        self,
        scope: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Analyze QC pass rate trend for a scope."""
        # This would query historical QC results
        # For now, return structure for future implementation
        return {
            "scope": scope,
            "period_days": days,
            "trend": "stable",
            "current_pass_rate": 0.85,
            "projected_pass_rate": 0.85,
            "risk_level": "low",
            "recommendation": "Continue monitoring",
        }

    def identify_qc_bottlenecks(
        self,
        scope: str = "",
    ) -> List[Dict[str, Any]]:
        """Identify QC bottlenecks from patterns."""
        patterns = self.learning.get_patterns(severity=PatternSeverity.CRITICAL)
        if scope:
            patterns = [p for p in patterns if scope in p.entities_involved]

        return [
            {
                "pattern_id": p.pattern_id,
                "title": p.title,
                "frequency": p.frequency,
                "impact_score": p.impact_score,
                "entities": p.entities_involved,
            }
            for p in patterns
        ]