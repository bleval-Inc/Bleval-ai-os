"""Executive Intelligence Layer — connects Learning Engine patterns to executive decision-making.

This module enables executives to:
1. Query learning patterns relevant to their domain
2. Receive proactive recommendations from the Learning Engine
3. Adjust decision weights based on historical performance
4. Learn from completed workflows automatically

Architecture Law 10: Learning is separate from memory.
- Memory stores knowledge.
- Learning improves future decisions.
- Learning updates Memory through controlled interfaces.
- Only executives approve permanent changes to Memory.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.engine.learning import LearningEngine
from axiom.models.learning import (
    DetectedPattern,
    LearningRecommendation,
    LearningSource,
    PatternSeverity,
    PerformanceScore,
    RecommendationStatus,
    ScoreCategory,
    WorkflowAnalyticsSummary,
)
from axiom.models.executive_constants import EXECUTIVE_ORGS, EXECUTIVE_DEPTS


class ExecutiveIntelligence:
    """Intelligence layer that feeds learning insights into executive decisions.

    Each executive gets a personalized view of learning data relevant to their
    organization and departments. They use this to:
    - Weight decisions based on historical success rates
    - Avoid known failure patterns
    - Replicate successful workflow patterns
    - Prioritize based on detected bottlenecks or opportunities
    """

    def __init__(self, learning_engine: LearningEngine, runtime: Any = None) -> None:
        self.learning = learning_engine
        self.runtime = runtime

        # Per-executive cached intelligence
        self._pattern_cache: Dict[str, List[DetectedPattern]] = {}
        self._recommendation_cache: Dict[str, List[LearningRecommendation]] = {}
        self._score_cache: Dict[str, Dict[str, float]] = {}
        self._last_refresh: Dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    # ── Public API ──────────────────────────────────────────────────────────

    async def get_executive_intelligence(self, exec_id: str) -> Dict[str, Any]:
        """Get all learning intelligence relevant to an executive.

        Returns patterns, recommendations, scores, and analytics
        filtered to the executive's organization and departments.
        """
        await self._refresh_cache(exec_id)

        org_id = EXECUTIVE_ORGS.get(exec_id, "")
        departments = self._get_executive_departments(exec_id)

        # Filter patterns relevant to this executive
        relevant_patterns = self._filter_patterns_for_exec(
            self._pattern_cache.get(exec_id, []),
            org_id,
            departments,
        )

        # Filter recommendations
        relevant_recs = self._filter_recommendations_for_exec(
            self._recommendation_cache.get(exec_id, []),
            org_id,
            departments,
        )

        # Get performance scores for workflows in this org
        workflow_scores = self._get_workflow_scores_for_exec(org_id, departments)

        # Get workflow analytics
        workflow_analytics = self._get_workflow_analytics_for_exec(org_id, departments)

        # Build actionable intelligence summary
        intelligence = self._build_intelligence_summary(
            exec_id=exec_id,
            org_id=org_id,
            patterns=relevant_patterns,
            recommendations=relevant_recs,
            workflow_scores=workflow_scores,
            workflow_analytics=workflow_analytics,
        )

        return intelligence

    async def get_workflow_decision_support(
        self,
        exec_id: str,
        workflow_id: str,
        priority: str = "",
    ) -> Dict[str, Any]:
        """Get decision support for launching a specific workflow.

        Analyzes historical performance, detected patterns, and recommendations
        to provide a confidence score and warnings/insights.
        """
        await self._refresh_cache(exec_id)

        org_id = EXECUTIVE_ORGS.get(exec_id, "")

        # Get workflow analytics
        analytics = self.learning.get_workflow_analytics(workflow_id)
        summary = analytics[0] if analytics else None

        # Get relevant patterns
        patterns = self._pattern_cache.get(exec_id, [])
        workflow_patterns = [
            p for p in patterns
            if workflow_id in p.entities_involved or
               any(e.startswith(workflow_id.split("-")[0]) for e in p.entities_involved)
        ]

        # Get relevant recommendations
        recs = self._recommendation_cache.get(exec_id, [])
        workflow_recs = [
            r for r in recs
            if r.target_entity_id == workflow_id or r.target_entity_type == "workflow"
        ]

        # Compute confidence
        confidence = self._compute_launch_confidence(summary, workflow_patterns, workflow_recs)

        # Build warnings and insights
        warnings, insights = self._analyze_launch_risks(
            workflow_id, summary, workflow_patterns, workflow_recs
        )

        return {
            "workflow_id": workflow_id,
            "executive_id": exec_id,
            "org_id": org_id,
            "confidence": confidence,
            "recommendation": "proceed" if confidence > 0.6 else "review",
            "warnings": warnings,
            "insights": insights,
            "historical_performance": {
                "success_rate": summary.success_rate if summary else None,
                "avg_duration": summary.avg_duration_seconds if summary else None,
                "avg_retries": summary.avg_retries_per_run if summary else None,
                "trend": summary.trend if summary else "unknown",
                "total_runs": summary.total_runs if summary else 0,
            } if summary else None,
            "patterns": [
                {
                    "title": p.title,
                    "severity": p.severity.value,
                    "impact": p.impact_score,
                    "description": p.description[:200],
                }
                for p in workflow_patterns
            ],
            "recommendations": [
                {
                    "title": r.title,
                    "confidence": r.confidence,
                    "action": r.suggested_action,
                    "status": r.status.value,
                }
                for r in workflow_recs
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def record_workflow_outcome(
        self,
        exec_id: str,
        workflow_id: str,
        instance_id: str,
        status: str,
        duration: float,
        steps_completed: int,
        steps_total: int,
        retries: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """Record a workflow execution outcome for learning.

        This feeds directly into the Learning Engine to update scores,
        detect patterns, and generate recommendations.
        """
        await self.learning.record_workflow_execution(
            workflow_id=workflow_id,
            instance_id=instance_id,
            status=status,
            total_duration=duration,
            total_steps=steps_total,
            completed_steps=steps_completed,
            failed_steps=steps_total - steps_completed if status != "completed" else 0,
            retries=retries,
            org=EXECUTIVE_ORGS.get(exec_id, ""),
            department="",  # Could be enhanced to infer from workflow
            error=error,
        )

    async def record_agent_outcome(
        self,
        exec_id: str,
        agent_id: str,
        task_id: str,
        workflow_instance_id: str,
        success: bool,
        duration: float,
        retries: int = 0,
        action: str = "",
        error: Optional[str] = None,
    ) -> None:
        """Record an agent task outcome for learning."""
        await self.learning.record_agent_task(
            agent_id=agent_id,
            task_id=task_id,
            workflow_instance_id=workflow_instance_id,
            action=action,
            success=success,
            duration=duration,
            retries=retries,
            error=error,
        )

    async def run_learning_cycle_for_exec(self, exec_id: str) -> Dict[str, Any]:
        """Run a learning cycle specifically for an executive's domain."""
        org_id = EXECUTIVE_ORGS.get(exec_id, "")
        return await self.learning.run_learning_cycle(
            source_entity_id=f"exec:{exec_id}",
            source_entity_type="executive",
            execution_ref=org_id,
        )

    # ── Cache Management ─────────────────────────────────────────────────────

    async def _refresh_cache(self, exec_id: str) -> None:
        """Refresh the cached intelligence for an executive."""
        now = datetime.now(timezone.utc)
        last = self._last_refresh.get(exec_id)

        if last and (now - last).total_seconds() < self._cache_ttl_seconds:
            return

        # Fetch all patterns
        all_patterns = self.learning.get_patterns()
        self._pattern_cache[exec_id] = all_patterns

        # Fetch all recommendations
        all_recs = self.learning.get_recommendations()
        self._recommendation_cache[exec_id] = all_recs

        # Update score cache
        self._update_score_cache()

        self._last_refresh[exec_id] = now

    def _update_score_cache(self) -> None:
        """Update the score cache from the score tracker."""
        for history in self.learning.score_tracker.get_all():
            key = f"{history.entity_type}:{history.entity_id}"
            self._score_cache[key] = {
                "running_average": history.running_average,
                "trend": history.trend,
                "total_scores": len(history.scores),
            }

    def _get_score(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get cached score for an entity."""
        return self._score_cache.get(f"{entity_type}:{entity_id}")

    # ── Filtering ───────────────────────────────────────────────────────────

    def _get_executive_departments(self, exec_id: str) -> List[str]:
        """Get departments for an executive."""
        from axiom.runtime.executive_loop import EXECUTIVE_DEPTS
        return EXECUTIVE_DEPTS.get(exec_id, [])

    def _filter_patterns_for_exec(
        self,
        patterns: List[DetectedPattern],
        org_id: str,
        departments: List[str],
    ) -> List[DetectedPattern]:
        """Filter patterns relevant to an executive's domain."""
        relevant = []

        for pattern in patterns:
            # Check if any involved entity matches org or departments
            for entity in pattern.entities_involved:
                if entity.startswith(org_id) or any(d in entity for d in departments):
                    relevant.append(pattern)
                    break

        # Sort by severity and impact
        severity_order = {
            PatternSeverity.CRITICAL: 0,
            PatternSeverity.WARNING: 1,
            PatternSeverity.OPTIMIZATION: 2,
            PatternSeverity.LEARNING: 3,
            PatternSeverity.INFO: 4,
        }
        relevant.sort(key=lambda p: (severity_order.get(p.severity, 5), -p.impact_score))
        return relevant[:20]  # Top 20 most relevant

    def _filter_recommendations_for_exec(
        self,
        recs: List[LearningRecommendation],
        org_id: str,
        departments: List[str],
    ) -> List[LearningRecommendation]:
        """Filter recommendations relevant to an executive's domain."""
        relevant = []

        for rec in recs:
            # Check target entity matches org/departments
            if rec.target_entity_id.startswith(org_id) or \
               any(d in rec.target_entity_id for d in departments):
                relevant.append(rec)
            elif rec.target_entity_type in ("executive", "org", "organization"):
                # Executive-level recommendations
                if rec.target_entity_id == org_id:
                    relevant.append(rec)

        # Sort by status priority and confidence
        status_priority = {
            RecommendationStatus.APPROVED: 0,
            RecommendationStatus.PROPOSED: 1,
            RecommendationStatus.DRAFT: 2,
            RecommendationStatus.APPLIED: 3,
            RecommendationStatus.REJECTED: 4,
            RecommendationStatus.SUPERSEDED: 5,
        }
        relevant.sort(key=lambda r: (status_priority.get(r.status, 6), -r.confidence))
        return relevant[:15]

    def _get_workflow_scores_for_exec(
        self,
        org_id: str,
        departments: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """Get performance scores for workflows in executive's domain."""
        scores = {}
        for history in self.learning.score_tracker.get_all():
            if history.entity_type == "workflow":
                # Check if workflow belongs to this org
                if history.entity_id.startswith(org_id) or \
                   any(d in history.entity_id for d in departments):
                    scores[history.entity_id] = {
                        "running_average": history.running_average,
                        "trend": history.trend,
                        "total_scores": len(history.scores),
                    }
        return scores

    def _get_workflow_analytics_for_exec(
        self,
        org_id: str,
        departments: List[str],
    ) -> List[WorkflowAnalyticsSummary]:
        """Get workflow analytics for executive's domain."""
        all_analytics = self.learning.get_workflow_analytics()
        relevant = []

        for summary in all_analytics:
            if summary.workflow_id.startswith(org_id) or \
               any(d in summary.workflow_id for d in departments):
                relevant.append(summary)

        return relevant

    # ── Intelligence Building ─────────────────────────────────────────────────

    def _build_intelligence_summary(
        self,
        exec_id: str,
        org_id: str,
        patterns: List[DetectedPattern],
        recommendations: List[LearningRecommendation],
        workflow_scores: Dict[str, Dict[str, Any]],
        workflow_analytics: List[WorkflowAnalyticsSummary],
    ) -> Dict[str, Any]:
        """Build actionable intelligence summary for an executive."""
        # Critical alerts
        critical_patterns = [p for p in patterns if p.severity == PatternSeverity.CRITICAL]
        urgent_recs = [
            r for r in recommendations
            if r.status in (RecommendationStatus.PROPOSED, RecommendationStatus.APPROVED)
            and r.confidence > 0.8
        ]

        # Key metrics
        total_workflows = len(workflow_scores)
        avg_score = sum(s["running_average"] for s in workflow_scores.values()) / max(total_workflows, 1)
        improving = sum(1 for s in workflow_scores.values() if s["trend"] == "improving")
        declining = sum(1 for s in workflow_scores.values() if s["trend"] == "declining")

        # Top successful workflows
        top_workflows = sorted(
            workflow_analytics,
            key=lambda w: w.success_rate,
            reverse=True
        )[:5]

        # Most problematic workflows
        problem_workflows = sorted(
            [w for w in workflow_analytics if w.success_rate < 0.8],
            key=lambda w: w.success_rate
        )[:5]

        # Learning opportunities
        learning_patterns = [p for p in patterns if p.severity == PatternSeverity.LEARNING]

        return {
            "executive_id": exec_id,
            "org_id": org_id,
            "summary": {
                "total_workflows_tracked": total_workflows,
                "average_performance_score": round(avg_score, 3),
                "improving_workflows": improving,
                "declining_workflows": declining,
                "critical_patterns": len(critical_patterns),
                "urgent_recommendations": len(urgent_recs),
                "learning_opportunities": len(learning_patterns),
            },
            "critical_alerts": [
                {
                    "title": p.title,
                    "description": p.description[:200],
                    "impact": p.impact_score,
                    "entities": p.entities_involved,
                }
                for p in critical_patterns[:5]
            ],
            "urgent_recommendations": [
                {
                    "title": r.title,
                    "confidence": r.confidence,
                    "action": r.suggested_action,
                    "target": r.target_entity_id,
                }
                for r in urgent_recs[:5]
            ],
            "top_performing_workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "success_rate": round(w.success_rate, 3),
                    "avg_duration": round(w.avg_duration_seconds, 1),
                    "trend": w.trend,
                }
                for w in top_workflows
            ],
            "problem_workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "success_rate": round(w.success_rate, 3),
                    "avg_retries": round(w.avg_retries_per_run, 1),
                    "failure_reasons": list(w.failure_reasons.keys())[:3],
                    "trend": w.trend,
                }
                for w in problem_workflows
            ],
            "learning_opportunities": [
                {
                    "title": p.title,
                    "description": p.description[:200],
                    "entities": p.entities_involved,
                }
                for p in learning_patterns[:5]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _compute_launch_confidence(
        self,
        summary: Optional[WorkflowAnalyticsSummary],
        patterns: List[DetectedPattern],
        recs: List[LearningRecommendation],
    ) -> float:
        """Compute confidence score for launching a workflow."""
        if not summary or summary.total_runs == 0:
            return 0.5  # No history = neutral

        base = summary.success_rate

        # Penalize for critical patterns
        for p in patterns:
            if p.severity == PatternSeverity.CRITICAL:
                base -= 0.2 * p.impact_score
            elif p.severity == PatternSeverity.WARNING:
                base -= 0.1 * p.impact_score

        # Boost for positive learning patterns
        for p in patterns:
            if p.severity == PatternSeverity.LEARNING:
                base += 0.1 * p.impact_score

        # Adjust for recommendations
        for r in recs:
            if r.status == RecommendationStatus.APPROVED and r.change_type == "modify":
                base += 0.05 * r.confidence
            elif r.status == RecommendationStatus.REJECTED:
                base -= 0.05

        return max(0.0, min(1.0, base))

    def _analyze_launch_risks(
        self,
        workflow_id: str,
        summary: Optional["WorkflowAnalyticsSummary"],
        patterns: List["DetectedPattern"],
        recs: List["LearningRecommendation"],
    ) -> "tuple[List[str], List[str]]":
        """Analyze risks and insights for a workflow launch."""
        warnings = []
        insights = []

        if summary:
            if summary.success_rate < 0.5:
                warnings.append(f"Low historical success rate: {summary.success_rate:.0%}")
            if summary.avg_retries_per_run > 2:
                warnings.append(f"High average retries: {summary.avg_retries_per_run:.1f}")
            if summary.trend == "declining":
                warnings.append("Performance trend is declining")

            if summary.failure_reasons:
                top_reason = max(summary.failure_reasons.items(), key=lambda x: x[1])
                warnings.append(f"Top failure reason: {top_reason[0]} ({top_reason[1]} occurrences)")

        for p in patterns:
            if p.severity in (PatternSeverity.CRITICAL, PatternSeverity.WARNING):
                warnings.append(f"Pattern: {p.title} — {p.description[:150]}")
            elif p.severity == PatternSeverity.LEARNING:
                insights.append(f"Successful pattern: {p.title} — {p.description[:150]}")

        for r in recs:
            if r.status == RecommendationStatus.APPROVED:
                insights.append(f"Approved improvement: {r.suggested_action}")
            elif r.status == RecommendationStatus.PROPOSED and r.confidence > 0.8:
                insights.append(f"High-confidence recommendation: {r.suggested_action}")

        return warnings, insights


class ExecutiveGreeter:
    """Generates personalized greetings from executives when Founder switches workstations."""

    def __init__(self, runtime: Any = None) -> None:
        self.runtime = runtime

    async def greet_founder(self, exec_id: str) -> str:
        """Generate a greeting from an executive to the Founder.

        Includes:
        - What the executive has completed since last interaction
        - What's currently running
        - Today's priorities/operations
        """
        loop = None
        if self.runtime and self.runtime.executive_board:
            loop = self.runtime.executive_board.get_loop(exec_id)

        if not loop:
            return self._get_default_greeting(exec_id)

        status = loop.get_status()
        memory = loop.memory

        # Get recent completions
        recent_work = []
        if memory:
            try:
                recent_decisions = memory.get_recent_decisions(limit=5)
                recent_work = [
                    {
                        "type": d.get("decision_type", ""),
                        "description": d.get("description", ""),
                        "outcome": d.get("outcome", ""),
                    }
                    for d in recent_decisions
                ]
            except Exception:
                pass

        # Get active workflows
        active_workflows = []
        if self.runtime and self.runtime.workflow:
            try:
                from axiom.models.workflows import WorkflowStatus
                instances = self.runtime.workflow.list_instances(status=WorkflowStatus.RUNNING)
                org_id = EXECUTIVE_ORGS.get(exec_id, "")
                active_workflows = [
                    {
                        "workflow_id": i.workflow_id,
                        "instance_id": i.instance_id,
                        "current_step": i.current_step_index,
                        "total_steps": len(i.steps) if hasattr(i, "steps") else 0,
                    }
                    for i in instances
                    if getattr(i, "org", "") == org_id
                ][:5]
            except Exception:
                pass

        # Get today's priorities from schedule
        priorities = []
        if exec_id == "yamako" and loop._schedule_coordinator:
            try:
                schedule = loop._schedule_coordinator.get_dashboard()
                priorities = schedule.get("today_blocks", [])[:3]
            except Exception:
                pass

        return self._format_greeting(
            exec_id=exec_id,
            cycle_count=status.get("cycle_count", 0),
            recent_work=recent_work,
            active_workflows=active_workflows,
            priorities=priorities,
        )

    def _format_greeting(
        self,
        exec_id: str,
        cycle_count: int,
        recent_work: List[Dict[str, Any]],
        active_workflows: List[Dict[str, Any]],
        priorities: List[Any],
    ) -> str:
        """Format a personalized executive greeting."""
        exec_names = {
            "jenson": "Jenson",
            "valta_prime": "Valta Prime",
            "yamako": "Yamako",
        }
        exec_orgs = {
            "jenson": "Bleval Inc",
            "valta_prime": "House of Valta",
            "yamako": "Personal",
        }
        name = exec_names.get(exec_id, exec_id)
        org = exec_orgs.get(exec_id, "")

        lines = [
            f"Good to see you, Founder. This is {name} from {org}.",
            f"I've completed {cycle_count} executive cycles so far.",
            "",
        ]

        if recent_work:
            lines.append("Recent accomplishments:")
            for work in recent_work[:3]:
                outcome_emoji = "✅" if "SUCCESS" in work.get("outcome", "").upper() else "📋"
                lines.append(f"  {outcome_emoji} {work.get('description', 'Task completed')[:80]}")
        else:
            lines.append("No recent cycles recorded yet.")

        if active_workflows:
            lines.append(
                f"Currently running {len(active_workflows)} workflow(s):"
            )
            for wf in active_workflows[:3]:
                progress = f"{wf['current_step']}/{wf['total_steps']}" if wf['total_steps'] else "?"
                lines.append(f"  🔄 {wf['workflow_id']} — Step {progress}")
        else:
            lines.append("No active workflows at the moment.")

        if priorities:
            lines.append("Today's priorities:")
            for p in priorities[:3]:
                desc = p.get("description", p.get("title", str(p)))[:80]
                lines.append(f"  📌 {desc}")

        lines.extend([
            "",
            "What would you like me to focus on?",
        ])

        return "\n".join(lines)

    def _get_default_greeting(self, exec_id: str) -> str:
        """Fallback greeting when runtime data unavailable."""
        exec_names = {
            "jenson": "Jenson",
            "valta_prime": "Valta Prime",
            "yamako": "Yamako",
        }
        name = exec_names.get(exec_id, exec_id)
        return f"Welcome back, Founder. {name} here — ready to assist with {name}'s operations."