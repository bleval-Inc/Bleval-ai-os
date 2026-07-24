"""Continuous Learning Engine — observes, measures, learns, and improves.

Every workflow produces learning. Every executive improves.
Memory evolves. Playbooks evolve. Performance is measurable.

Learning Loop:
    Execute → Observe → Measure → Learn → Improve → Repeat

Architecture Law 10: Learning is separate from memory.
  - Memory stores knowledge.
  - Learning improves future decisions.
  - Learning updates Memory through controlled interfaces.
  - Only executives approve permanent changes to Memory.
"""

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from axiom.engine.memory import MemoryEngine
from axiom.models.learning import (
    AgentPerformanceRecord,
    DetectedPattern,
    ExecutiveDecisionRecord,
    KnowledgeEntry,
    LearningCycle,
    LearningEngineState,
    LearningSource,
    PerformanceScore,
    PlaybookEvolution,
    Recommendation,
    RecommendationStatus,
    ScoreCategory,
    ScoreHistory,
    PatternSeverity,
    WorkflowAnalyticsSummary,
    WorkflowExecutionRecord,
)


class ScoreTracker:
    """Tracks and aggregates performance scores across entities."""

    def __init__(self) -> None:
        self._scores: Dict[str, ScoreHistory] = {}

    def record(self, score: PerformanceScore) -> None:
        """Record a performance score and update running stats."""
        key = f"{score.entity_type}:{score.entity_id}"
        if key not in self._scores:
            self._scores[key] = ScoreHistory(
                entity_id=score.entity_id,
                entity_type=score.entity_type,
                last_updated=score.timestamp,
            )
        history = self._scores[key]
        history.scores.append(score)

        # Recompute running average
        total = sum(s.overall_score for s in history.scores)
        count = len(history.scores)
        history.running_average = total / count if count else 0.0

        # Compute trend (compare last 5 vs previous 5)
        recent = [s.overall_score for s in history.scores[-5:]]
        older = [s.overall_score for s in history.scores[-10:-5]]
        if len(recent) >= 3 and len(older) >= 3:
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            diff = recent_avg - older_avg
            if diff > 0.05:
                history.trend = "improving"
            elif diff < -0.05:
                history.trend = "declining"
            else:
                history.trend = "stable"

        history.last_updated = score.timestamp

    def get_history(self, entity_id: str, entity_type: str) -> Optional[ScoreHistory]:
        """Get the score history for an entity."""
        return self._scores.get(f"{entity_type}:{entity_id}")

    def get_all(self) -> List[ScoreHistory]:
        """Return all tracked score histories."""
        return list(self._scores.values())


class PatternDetector:
    """Detects patterns from recorded execution data.

    Patterns can be:
      - Performance regressions or improvements
      - Recurring errors or bottlenecks
      - Efficiency opportunities
      - Learning signals (repeatable successes)
    """

    def __init__(self) -> None:
        self._patterns: Dict[str, DetectedPattern] = {}

    def detect_from_workflows(
        self,
        summaries: List[WorkflowAnalyticsSummary],
    ) -> List[DetectedPattern]:
        """Analyze workflow analytics to detect patterns."""
        new_patterns: List[DetectedPattern] = []
        now = datetime.now(timezone.utc)

        for summary in summaries:
            # Check for high failure rate
            if summary.total_runs >= 3 and summary.success_rate < 0.6:
                pattern = self._get_or_create(
                    pattern_type="error",
                    title=f"High failure rate in {summary.workflow_id}",
                    severity=PatternSeverity.CRITICAL,
                    entities=[summary.workflow_id],
                )
                pattern.description = (
                    f"Workflow {summary.workflow_id} has {summary.success_rate:.0%} "
                    f"success rate over {summary.total_runs} runs."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                pattern.evidence.append(
                    f"success_rate={summary.success_rate:.2f}, runs={summary.total_runs}"
                )
                new_patterns.append(pattern)

            # Check for slow execution
            if summary.total_runs >= 3 and summary.avg_duration_seconds > 300:
                pattern = self._get_or_create(
                    pattern_type="bottleneck",
                    title=f"Slow execution in {summary.workflow_id}",
                    severity=PatternSeverity.WARNING,
                    entities=[summary.workflow_id],
                )
                pattern.description = (
                    f"Workflow {summary.workflow_id} averages "
                    f"{summary.avg_duration_seconds:.1f}s per run."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                pattern.evidence.append(
                    f"avg_duration={summary.avg_duration_seconds:.1f}s"
                )
                new_patterns.append(pattern)

            # Check for declining trend
            if summary.trend == "declining" and summary.total_runs >= 5:
                pattern = self._get_or_create(
                    pattern_type="performance",
                    title=f"Declining performance in {summary.workflow_id}",
                    severity=PatternSeverity.WARNING,
                    entities=[summary.workflow_id],
                )
                pattern.description = (
                    f"Workflow {summary.workflow_id} is on a declining trend "
                    f"after {summary.total_runs} runs."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                new_patterns.append(pattern)

            # Check for consistent success (positive pattern)
            if summary.total_runs >= 5 and summary.success_rate == 1.0:
                pattern = self._get_or_create(
                    pattern_type="learning",
                    title=f"Consistent success in {summary.workflow_id}",
                    severity=PatternSeverity.LEARNING,
                    entities=[summary.workflow_id],
                )
                pattern.description = (
                    f"Workflow {summary.workflow_id} has 100% success rate "
                    f"over {summary.total_runs} runs — repeatable pattern."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                new_patterns.append(pattern)

        return new_patterns

    def detect_from_executives(
        self,
        decisions: List[ExecutiveDecisionRecord],
    ) -> List[DetectedPattern]:
        """Analyze executive decisions to detect patterns."""
        new_patterns: List[DetectedPattern] = []
        now = datetime.now(timezone.utc)

        # Group decisions by executive
        by_exec: Dict[str, List[ExecutiveDecisionRecord]] = defaultdict(list)
        for d in decisions:
            by_exec[d.exec_id].append(d)

        for exec_id, exec_decisions in by_exec.items():
            if len(exec_decisions) < 3:
                continue

            # Check approval/rejection ratio
            approvals = sum(1 for d in exec_decisions if d.outcome == "success")
            ratio = approvals / len(exec_decisions)
            if ratio < 0.5:
                pattern = self._get_or_create(
                    pattern_type="performance",
                    title=f"Low decision success for {exec_id}",
                    severity=PatternSeverity.WARNING,
                    entities=[exec_id],
                )
                pattern.description = (
                    f"Executive {exec_id} has {ratio:.0%} decision success rate "
                    f"over {len(exec_decisions)} decisions."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                pattern.evidence.append(f"approval_ratio={ratio:.2f}")
                new_patterns.append(pattern)

        return new_patterns

    def detect_from_agents(
        self,
        records: List[AgentPerformanceRecord],
    ) -> List[DetectedPattern]:
        """Analyze agent task performance to detect patterns."""
        new_patterns: List[DetectedPattern] = []
        now = datetime.now(timezone.utc)

        by_agent: Dict[str, List[AgentPerformanceRecord]] = defaultdict(list)
        for r in records:
            by_agent[r.agent_id].append(r)

        for agent_id, agent_records in by_agent.items():
            if len(agent_records) < 3:
                continue

            failures = sum(1 for r in agent_records if not r.success)
            failure_rate = failures / len(agent_records)
            total_retries = sum(r.retries for r in agent_records)

            if failure_rate > 0.3:
                pattern = self._get_or_create(
                    pattern_type="error",
                    title=f"High error rate for agent {agent_id}",
                    severity=PatternSeverity.CRITICAL,
                    entities=[agent_id],
                )
                pattern.description = (
                    f"Agent {agent_id} has {failure_rate:.0%} failure rate "
                    f"over {len(agent_records)} tasks ({total_retries} retries)."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                pattern.evidence.append(
                    f"failure_rate={failure_rate:.2f}, retries={total_retries}"
                )
                new_patterns.append(pattern)

            if total_retries > len(agent_records) * 2:
                pattern = self._get_or_create(
                    pattern_type="bottleneck",
                    title=f"Excessive retries for agent {agent_id}",
                    severity=PatternSeverity.OPTIMIZATION,
                    entities=[agent_id],
                )
                pattern.description = (
                    f"Agent {agent_id} required {total_retries} retries "
                    f"across {len(agent_records)} tasks."
                )
                pattern.frequency += 1
                pattern.last_detected = now
                pattern.evidence.append(
                    f"retries_per_task={total_retries / len(agent_records):.1f}"
                )
                new_patterns.append(pattern)

        return new_patterns

    def _get_or_create(
        self,
        pattern_type: str,
        title: str,
        severity: PatternSeverity,
        entities: List[str],
    ) -> DetectedPattern:
        """Get existing pattern by type+title or create a new one."""
        key = f"{pattern_type}:{title}"
        if key in self._patterns:
            return self._patterns[key]

        now = datetime.now(timezone.utc)
        pattern = DetectedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=pattern_type,
            severity=severity,
            title=title,
            description="",
            entities_involved=list(entities),
            frequency=0,
            impact_score=0.5,
            first_detected=now,
            last_detected=now,
        )
        self._patterns[key] = pattern
        return pattern

    def get_all_patterns(
        self,
        severity: Optional[PatternSeverity] = None,
    ) -> List[DetectedPattern]:
        """Return all detected patterns, optionally filtered by severity."""
        patterns = list(self._patterns.values())
        if severity:
            patterns = [p for p in patterns if p.severity == severity]
        return sorted(patterns, key=lambda p: p.last_detected, reverse=True)


class RecommendationEngine:
    """Generates and tracks recommendations from detected patterns.

    Every recommendation has a lifecycle:
      DRAFT → PROPOSED → APPROVED → APPLIED
                        → REJECTED
                        → SUPERSEDED
    """

    def __init__(self) -> None:
        self._recommendations: Dict[str, Recommendation] = {}

    def generate(
        self,
        pattern: DetectedPattern,
    ) -> Optional[Recommendation]:
        """Generate a recommendation from a detected pattern."""
        now = datetime.now(timezone.utc)

        if pattern.pattern_type == "error":
            return Recommendation(
                recommendation_id=str(uuid.uuid4()),
                title=f"Investigate {pattern.title}",
                description=(
                    f"Pattern detected: {pattern.description}. "
                    f"Review and address the root cause."
                ),
                rationale=(
                    f"The system detected a recurring issue affecting "
                    f"{', '.join(pattern.entities_involved)}. "
                    f"Impact score: {pattern.impact_score:.1f}. "
                    f"Evidence: {'; '.join(pattern.evidence[-3:])}."
                ),
                expected_impact="Reduce error rate and improve reliability",
                source_pattern_id=pattern.pattern_id,
                target_entity_id=pattern.entities_involved[0] if pattern.entities_involved else "",
                target_entity_type="workflow",
                change_type="modify",
                suggested_action="Review error patterns and adjust workflow configuration or agent instructions",
                confidence=min(0.9, 0.5 + pattern.frequency * 0.1),
                status=RecommendationStatus.DRAFT,
                created_at=now,
            )

        if pattern.pattern_type == "bottleneck":
            return Recommendation(
                recommendation_id=str(uuid.uuid4()),
                title=f"Optimize {pattern.title}",
                description=pattern.description,
                rationale=(
                    f"Performance bottleneck detected. "
                    f"Duration: {pattern.evidence[-1] if pattern.evidence else 'N/A'}. "
                    f"Frequency: {pattern.frequency} detections."
                ),
                expected_impact="Improve execution speed and reduce duration",
                source_pattern_id=pattern.pattern_id,
                target_entity_id=pattern.entities_involved[0] if pattern.entities_involved else "",
                target_entity_type="workflow",
                change_type="modify",
                suggested_action="Review workflow steps for parallelization or simplification opportunities",
                confidence=min(0.8, 0.4 + pattern.frequency * 0.1),
                status=RecommendationStatus.DRAFT,
                created_at=now,
            )

        if pattern.pattern_type == "learning":
            return Recommendation(
                recommendation_id=str(uuid.uuid4()),
                title=f"Promote learning: {pattern.title}",
                description=pattern.description,
                rationale=(
                    f"A repeatable successful pattern was detected. "
                    f"This knowledge should be promoted to organizational memory "
                    f"for reuse across the organization."
                ),
                expected_impact="Enable knowledge reuse and improve consistency",
                source_pattern_id=pattern.pattern_id,
                target_entity_id=pattern.entities_involved[0] if pattern.entities_involved else "",
                target_entity_type="playbook",
                change_type="create",
                suggested_action="Document the successful pattern and promote to playbook memory",
                confidence=min(0.95, 0.6 + pattern.frequency * 0.05),
                status=RecommendationStatus.DRAFT,
                created_at=now,
            )

        return None

    def propose(self, recommendation_id: str) -> bool:
        """Move a recommendation from DRAFT to PROPOSED."""
        rec = self._recommendations.get(recommendation_id)
        if rec and rec.status == RecommendationStatus.DRAFT:
            rec.status = RecommendationStatus.PROPOSED
            return True
        return False

    def approve(self, recommendation_id: str, by: str = "system") -> bool:
        """Approve a recommendation — executive-level action."""
        rec = self._recommendations.get(recommendation_id)
        if rec and rec.status == RecommendationStatus.PROPOSED:
            rec.status = RecommendationStatus.APPROVED
            rec.approved_by = by
            return True
        return False

    def reject(self, recommendation_id: str) -> bool:
        """Reject a recommendation."""
        rec = self._recommendations.get(recommendation_id)
        if rec and rec.status in (RecommendationStatus.PROPOSED, RecommendationStatus.DRAFT):
            rec.status = RecommendationStatus.REJECTED
            return True
        return False

    def mark_applied(self, recommendation_id: str) -> bool:
        """Mark a recommendation as applied."""
        rec = self._recommendations.get(recommendation_id)
        if rec:
            rec.status = RecommendationStatus.APPLIED
            rec.applied_at = datetime.now(timezone.utc)
            return True
        return False

    def get_all(
        self,
        status: Optional[RecommendationStatus] = None,
    ) -> List[Recommendation]:
        """Return all recommendations, optionally filtered by status."""
        recs = list(self._recommendations.values())
        if status:
            recs = [r for r in recs if r.status == status]
        return sorted(recs, key=lambda r: r.created_at, reverse=True)

    def register(self, recommendation: Recommendation) -> None:
        """Register a recommendation for tracking."""
        self._recommendations[recommendation.recommendation_id] = recommendation


class KnowledgeConsolidator:
    """Consolidates learnings into memory entries.

    Learning flows upward: agent → department → organization → global.
    Only consolidated, reviewed knowledge is promoted to memory.
    """

    def __init__(self, memory: Optional[MemoryEngine] = None) -> None:
        self._memory = memory
        self._entries: Dict[str, KnowledgeEntry] = {}

    def set_memory_engine(self, memory: MemoryEngine) -> None:
        """Inject memory engine after construction."""
        self._memory = memory

    def promote_recommendation(
        self,
        recommendation: Recommendation,
        content: str,
    ) -> Optional[KnowledgeEntry]:
        """Promote an approved recommendation to a knowledge entry."""
        now = datetime.now(timezone.utc)
        entry = KnowledgeEntry(
            entry_id=str(uuid.uuid4()),
            title=recommendation.title,
            content=content,
            source=LearningSource.WORKFLOW,
            source_entity=recommendation.target_entity_id,
            tags=[recommendation.change_type, recommendation.target_entity_type],
            confidence=recommendation.confidence,
            created_at=now,
        )
        self._entries[entry.entry_id] = entry

        # Write to memory if engine is available
        if self._memory:
            try:
                self._memory.write_agent_memory(
                    agent_id="system",
                    key=f"learning-{entry.entry_id[:8]}",
                    content=(
                        f"# {entry.title}\n\n"
                        f"{entry.content}\n\n"
                        f"**Source:** {entry.source.value}\n"
                        f"**Confidence:** {entry.confidence:.2f}\n"
                        f"**Tags:** {', '.join(entry.tags)}\n"
                        f"**Created:** {now.isoformat()}"
                    ),
                )
            except Exception:
                pass

        return entry

    def get_all_entries(self) -> List[KnowledgeEntry]:
        """Return all consolidated knowledge entries."""
        return list(self._entries.values())


class LearningEngine:
    """Continuous Learning Engine for Axiom OS.

    The Learning Engine observes every execution cycle — workflows,
    executive decisions, and agent tasks — and produces:

      1. Performance scores for every entity
      2. Analytics summaries (workflow, executive, agent)
      3. Detected patterns (errors, bottlenecks, opportunities)
      4. Recommendations for improvement
      5. Consolidated knowledge written to memory
      6. Long-term learning state

    Learning flow:
      Execute → Observe → Measure → Learn → Improve → Repeat

    Integration:
      - Receives data from WorkflowEngine, ExecutiveBoard, Dispatcher
      - Writes learnings to MemoryEngine (executive-approved only)
      - Emits learning events via EventEngine
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime

        # Sub-engines
        self.score_tracker = ScoreTracker()
        self.pattern_detector = PatternDetector()
        self.recommendation_engine = RecommendationEngine()
        self.knowledge_consolidator = KnowledgeConsolidator()

        # Record stores
        self._workflow_records: List[WorkflowExecutionRecord] = []
        self._executive_records: List[ExecutiveDecisionRecord] = []
        self._agent_records: List[AgentPerformanceRecord] = []
        self._playbook_evolutions: List[PlaybookEvolution] = []
        self._learning_cycles: List[LearningCycle] = []
        self._workflow_analytics: Dict[str, WorkflowAnalyticsSummary] = {}

        # Consolidation state
        self._state = LearningEngineState()

        # Background consolidation task
        self._consolidation_task: Optional[asyncio.Task] = None
        self._running = False
        self._consolidation_interval = 600  # Every 10 minutes

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def set_runtime(self, runtime: Any) -> None:
        """Inject runtime reference after construction."""
        self._runtime = runtime
        mem = getattr(runtime, "memory", None)
        if mem:
            self.knowledge_consolidator.set_memory_engine(mem)

    async def start(self) -> None:
        """Start the background consolidation loop."""
        if self._running:
            return
        self._running = True
        self._consolidation_task = asyncio.create_task(
            self._run_consolidation_loop()
        )

    async def stop(self) -> None:
        """Stop the background consolidation loop."""
        self._running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
            self._consolidation_task = None

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Data Recording ────────────────────────────────────────────────────

    async def record_workflow_execution(
        self,
        workflow_id: str,
        instance_id: str,
        status: str,
        total_duration: float = 0.0,
        total_steps: int = 0,
        completed_steps: int = 0,
        failed_steps: int = 0,
        retries: int = 0,
        approval_requests: int = 0,
        agents_involved: Optional[List[str]] = None,
        triggered_by: str = "",
        org: str = "",
        department: str = "",
        coordinator: str = "",
        error: Optional[str] = None,
    ) -> PerformanceScore:
        """Record a workflow execution and compute performance score."""
        now = datetime.now(timezone.utc)

        record = WorkflowExecutionRecord(
            instance_id=instance_id,
            workflow_id=workflow_id,
            org=org,
            department=department,
            coordinator=coordinator,
            status=status,
            total_duration_seconds=total_duration,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            retries=retries,
            approval_requests=approval_requests,
            agents_involved=agents_involved or [],
            triggered_by=triggered_by,
            started_at=None,
            completed_at=now,
            error=error,
        )
        self._workflow_records.append(record)

        # Compute performance score
        score = self._score_workflow(record)
        self.score_tracker.record(score)

        # Update workflow analytics
        self._update_workflow_analytics(record, score)

        # Run quick pattern detection
        self._run_quick_patterns()

        self._state.workflow_runs_tracked += 1
        return score

    async def record_executive_cycle(
        self,
        exec_id: str,
        decision_type: str,
        outcome: str,
        target: str = "",
        reasoning: str = "",
        duration: float = 0.0,
        workflow_instance_id: str = "",
    ) -> PerformanceScore:
        """Record an executive decision cycle and compute performance score."""
        now = datetime.now(timezone.utc)

        record = ExecutiveDecisionRecord(
            exec_id=exec_id,
            decision_type=decision_type,
            workflow_instance_id=workflow_instance_id,
            target=target,
            outcome=outcome,
            reasoning=reasoning,
            duration_seconds=duration,
            timestamp=now,
        )
        self._executive_records.append(record)

        # Compute executive performance score
        score = self._score_executive(exec_id, record)
        self.score_tracker.record(score)

        return score

    async def record_agent_task(
        self,
        agent_id: str,
        success: bool,
        duration: float = 0.0,
        retries: int = 0,
        action: str = "",
        task_id: str = "",
        workflow_instance_id: str = "",
        error: Optional[str] = None,
    ) -> PerformanceScore:
        """Record an agent task execution and compute performance score."""
        now = datetime.now(timezone.utc)

        record = AgentPerformanceRecord(
            agent_id=agent_id,
            task_id=task_id,
            workflow_instance_id=workflow_instance_id,
            action=action,
            duration_seconds=duration,
            success=success,
            error=error,
            retries=retries,
            timestamp=now,
        )
        self._agent_records.append(record)

        # Compute agent performance score
        score = self._score_agent(agent_id, record)
        self.score_tracker.record(score)

        return score

    # ── Learning Cycles ──────────────────────────────────────────────────

    async def run_learning_cycle(
        self,
        source_entity_id: str,
        source_entity_type: str,
        execution_ref: str = "",
    ) -> LearningCycle:
        """Run a complete learning cycle: Measure → Learn → Improve.

        This is the core learning loop:
          1. Measure: Score the execution
          2. Learn: Detect patterns, generate recommendations
          3. Improve: Consolidate knowledge, propose changes
        """
        now = datetime.now(timezone.utc)
        cycle_id = str(uuid.uuid4())

        cycle = LearningCycle(
            cycle_id=cycle_id,
            source_entity_id=source_entity_id,
            source_entity_type=source_entity_type,
            execution_ref=execution_ref,
            started_at=now,
        )

        try:
            # Get scores for this entity
            score_history = self.score_tracker.get_history(
                source_entity_id, source_entity_type,
            )
            if score_history:
                for s in score_history.scores[-5:]:
                    for cat, val in s.categories.items():
                        cycle.scores[f"{cat.value}_{s.instance_id[:8]}"] = val

            # Detect patterns from all available data
            patterns = self._run_full_pattern_detection()
            cycle.patterns_detected = [p.pattern_id for p in patterns]
            self._state.total_patterns_detected += len(patterns)

            # Generate recommendations from patterns
            for pattern in patterns:
                rec = self.recommendation_engine.generate(pattern)
                if rec:
                    self.recommendation_engine.register(rec)
                    try:
                        self.recommendation_engine.propose(rec.recommendation_id)
                    except Exception:
                        pass
                    cycle.recommendations_generated.append(rec.recommendation_id)
                    self._state.total_recommendations += 1

            # Auto-consolidate high-confidence learnings
            for rec in self.recommendation_engine.get_all(status=RecommendationStatus.PROPOSED):
                if rec.confidence >= 0.85:
                    try:
                        self.recommendation_engine.approve(
                            rec.recommendation_id, by="system"
                        )
                    except Exception:
                        pass

            # Consolidate approved recommendations to knowledge
            for rec in self.recommendation_engine.get_all(status=RecommendationStatus.APPROVED):
                if rec.status == RecommendationStatus.APPROVED:
                    entry = self.knowledge_consolidator.promote_recommendation(
                        rec,
                        content=(
                            f"{rec.description}\n\n"
                            f"**Rationale:** {rec.rationale}\n"
                            f"**Suggested Action:** {rec.suggested_action}"
                        ),
                    )
                    if entry:
                        cycle.knowledge_written.append(entry.entry_id)
                        self._state.total_knowledge_entries += 1

            cycle.success = True
            self._state.total_cycles += 1

        except Exception as exc:
            cycle.success = False

        cycle.completed_at = datetime.now(timezone.utc)
        cycle.duration_seconds = (
            cycle.completed_at - cycle.started_at
        ).total_seconds()

        self._learning_cycles.append(cycle)
        self._state.last_consolidation = cycle.completed_at

        return cycle

    # ── Analytics ─────────────────────────────────────────────────────────

    def get_workflow_analytics(
        self, workflow_id: Optional[str] = None,
    ) -> List[WorkflowAnalyticsSummary]:
        """Get workflow analytics, optionally filtered by workflow_id."""
        if workflow_id:
            summary = self._workflow_analytics.get(workflow_id)
            return [summary] if summary else []
        return list(self._workflow_analytics.values())

    def get_executive_analytics(
        self, exec_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get executive performance analytics."""
        records = self._executive_records
        if exec_id:
            records = [r for r in records if r.exec_id == exec_id]

        by_exec: Dict[str, Dict[str, Any]] = {}
        for r in records:
            if r.exec_id not in by_exec:
                by_exec[r.exec_id] = {
                    "exec_id": r.exec_id,
                    "total_decisions": 0,
                    "successes": 0,
                    "failures": 0,
                    "decisions_by_type": defaultdict(int),
                }
            by_exec[r.exec_id]["total_decisions"] += 1
            if r.outcome == "success":
                by_exec[r.exec_id]["successes"] += 1
            else:
                by_exec[r.exec_id]["failures"] += 1
            by_exec[r.exec_id]["decisions_by_type"][r.decision_type] += 1

        result = []
        for eid, data in by_exec.items():
            total = data["total_decisions"]
            data["success_rate"] = data["successes"] / total if total else 0
            score = self.score_tracker.get_history(eid, "executive")
            data["trend"] = score.trend if score else "stable"
            data["running_average"] = score.running_average if score else 0.0
            data["decisions_by_type"] = dict(data["decisions_by_type"])
            result.append(data)

        return result

    def get_agent_analytics(
        self, agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get agent performance analytics."""
        records = self._agent_records
        if agent_id:
            records = [r for r in records if r.agent_id == agent_id]

        by_agent: Dict[str, Dict[str, Any]] = {}
        for r in records:
            if r.agent_id not in by_agent:
                by_agent[r.agent_id] = {
                    "agent_id": r.agent_id,
                    "total_tasks": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_retries": 0,
                    "total_duration": 0.0,
                }
            by_agent[r.agent_id]["total_tasks"] += 1
            by_agent[r.agent_id]["total_duration"] += r.duration_seconds
            if r.success:
                by_agent[r.agent_id]["successes"] += 1
            else:
                by_agent[r.agent_id]["failures"] += 1
            by_agent[r.agent_id]["total_retries"] += r.retries

        result = []
        for aid, data in by_agent.items():
            total = data["total_tasks"]
            data["success_rate"] = data["successes"] / total if total else 0
            data["avg_duration"] = data["total_duration"] / total if total else 0
            score = self.score_tracker.get_history(aid, "agent")
            data["trend"] = score.trend if score else "stable"
            data["running_average"] = score.running_average if score else 0.0
            result.append(data)

        return result

    def get_patterns(
        self, severity: Optional[PatternSeverity] = None,
    ) -> List[DetectedPattern]:
        """Return all detected patterns."""
        return self.pattern_detector.get_all_patterns(severity)

    def get_recommendations(
        self, status: Optional[RecommendationStatus] = None,
    ) -> List[Recommendation]:
        """Return all generated recommendations."""
        return self.recommendation_engine.get_all(status)

    def get_knowledge(self) -> List[KnowledgeEntry]:
        """Return all consolidated knowledge entries."""
        return self.knowledge_consolidator.get_all_entries()

    def get_learning_cycles(
        self, limit: int = 10,
    ) -> List[LearningCycle]:
        """Return recent learning cycles."""
        return self._learning_cycles[-limit:]

    def get_state(self) -> LearningEngineState:
        """Return the current learning engine state."""
        return self._state

    # ── Playbook Evolution ────────────────────────────────────────────────

    def record_playbook_evolution(
        self,
        playbook_name: str,
        version: str,
        change_description: str,
        triggered_by_pattern: str = "",
        recommendation_id: str = "",
        approved_by: str = "",
    ) -> PlaybookEvolution:
        """Record a playbook change driven by learning."""
        now = datetime.now(timezone.utc)
        evolution = PlaybookEvolution(
            playbook_name=playbook_name,
            version=version,
            change_description=change_description,
            triggered_by_pattern=triggered_by_pattern,
            recommendation_id=recommendation_id,
            applied_at=now,
            approved_by=approved_by,
        )
        self._playbook_evolutions.append(evolution)
        return evolution

    def get_playbook_evolutions(self) -> List[PlaybookEvolution]:
        """Return all recorded playbook evolutions."""
        return list(self._playbook_evolutions)

    # ── Internal Scoring ─────────────────────────────────────────────────

    def _score_workflow(
        self, record: WorkflowExecutionRecord,
    ) -> PerformanceScore:
        """Compute a performance score for a workflow execution."""
        now = datetime.now(timezone.utc)

        # Speed score (lower duration = higher score)
        speed = 1.0
        if record.total_duration_seconds > 0:
            speed = max(0.0, 1.0 - (record.total_duration_seconds / 600.0))

        # Quality score (step completion ratio)
        quality = 1.0
        if record.total_steps > 0:
            quality = record.completed_steps / max(record.total_steps, 1)

        # Reliability score (retries + errors)
        reliability = 1.0
        retry_penalty = record.retries * 0.1
        if record.error:
            retry_penalty += 0.3
        reliability = max(0.0, 1.0 - retry_penalty)

        # Efficiency score
        efficiency = 1.0
        if record.completed_steps > 0:
            efficiency = record.total_steps / max(
                record.total_duration_seconds, 1
            ) * 10
            efficiency = min(1.0, efficiency)

        # Overall score (weighted average)
        overall = (
            speed * 0.25 +
            quality * 0.30 +
            reliability * 0.25 +
            efficiency * 0.20
        )

        return PerformanceScore(
            entity_id=record.workflow_id,
            entity_type="workflow",
            instance_id=record.instance_id,
            categories={
                ScoreCategory.SPEED: round(speed, 4),
                ScoreCategory.QUALITY: round(quality, 4),
                ScoreCategory.RELIABILITY: round(reliability, 4),
                ScoreCategory.EFFICIENCY: round(efficiency, 4),
            },
            overall_score=round(overall, 4),
            duration_seconds=record.total_duration_seconds,
            step_count=record.total_steps,
            error_count=record.failed_steps,
            retry_count=record.retries,
            had_approval_hold=record.approval_requests > 0,
            timestamp=now,
        )

    def _score_executive(
        self, exec_id: str, record: ExecutiveDecisionRecord,
    ) -> PerformanceScore:
        """Compute a performance score for an executive decision."""
        now = datetime.now(timezone.utc)

        # Autonomy score (lower duration = faster decision)
        autonomy = 1.0
        if record.duration_seconds > 0:
            autonomy = max(0.0, 1.0 - (record.duration_seconds / 120.0))

        # Quality based on outcome
        quality = 1.0 if record.outcome == "success" else 0.3
        reliability = 1.0 if record.outcome in ("success", "pending") else 0.5

        overall = autonomy * 0.3 + quality * 0.4 + reliability * 0.3

        return PerformanceScore(
            entity_id=exec_id,
            entity_type="executive",
            instance_id=record.workflow_instance_id or str(uuid.uuid4()),
            categories={
                ScoreCategory.AUTONOMY: round(autonomy, 4),
                ScoreCategory.QUALITY: round(quality, 4),
                ScoreCategory.RELIABILITY: round(reliability, 4),
            },
            overall_score=round(overall, 4),
            duration_seconds=record.duration_seconds,
            timestamp=now,
        )

    def _score_agent(
        self, agent_id: str, record: AgentPerformanceRecord,
    ) -> PerformanceScore:
        """Compute a performance score for an agent task."""
        now = datetime.now(timezone.utc)

        speed = 1.0
        if record.duration_seconds > 0:
            speed = max(0.0, 1.0 - (record.duration_seconds / 180.0))

        reliability = 1.0 if record.success else 0.2
        retry_penalty = record.retries * 0.15
        reliability = max(0.0, reliability - retry_penalty)

        overall = speed * 0.3 + reliability * 0.7

        return PerformanceScore(
            entity_id=agent_id,
            entity_type="agent",
            instance_id=record.task_id or str(uuid.uuid4()),
            categories={
                ScoreCategory.SPEED: round(speed, 4),
                ScoreCategory.RELIABILITY: round(reliability, 4),
            },
            overall_score=round(overall, 4),
            duration_seconds=record.duration_seconds,
            retry_count=record.retries,
            error_count=0 if record.success else 1,
            timestamp=now,
        )

    # ── Pattern Detection Internals ───────────────────────────────────────

    def _run_quick_patterns(self) -> None:
        """Run lightweight pattern detection on current data (no async)."""
        if len(self._workflow_records) < 2:
            return

        # Rebuild workflow summaries and run pattern detection
        summaries = list(self._workflow_analytics.values())
        self.pattern_detector.detect_from_workflows(summaries)

    def _run_full_pattern_detection(self) -> List[DetectedPattern]:
        """Run full pattern detection across all data sources."""
        patterns: List[DetectedPattern] = []

        # Workflow patterns
        summaries = list(self._workflow_analytics.values())
        patterns.extend(
            self.pattern_detector.detect_from_workflows(summaries)
        )

        # Executive patterns
        patterns.extend(
            self.pattern_detector.detect_from_executives(self._executive_records)
        )

        # Agent patterns
        patterns.extend(
            self.pattern_detector.detect_from_agents(self._agent_records)
        )

        return patterns

    def _update_workflow_analytics(
        self,
        record: WorkflowExecutionRecord,
        score: PerformanceScore,
    ) -> None:
        """Update the running analytics summary for a workflow."""
        wf_id = record.workflow_id

        if wf_id not in self._workflow_analytics:
            self._workflow_analytics[wf_id] = WorkflowAnalyticsSummary(
                workflow_id=wf_id,
            )

        summary = self._workflow_analytics[wf_id]
        prev_total = summary.total_runs
        summary.total_runs += 1

        # Update running averages
        if record.status == "completed":
            summary.success_rate = (
                (summary.success_rate * prev_total) + 1.0
            ) / summary.total_runs
        else:
            summary.success_rate = (
                (summary.success_rate * prev_total) + 0.0
            ) / summary.total_runs

        summary.avg_duration_seconds = (
            (summary.avg_duration_seconds * prev_total) + record.total_duration_seconds
        ) / summary.total_runs

        summary.avg_retries_per_run = (
            (summary.avg_retries_per_run * prev_total) + record.retries
        ) / summary.total_runs

        # Track failure reasons
        if record.error:
            reason = record.error.split(":")[0] if ":" in record.error else record.error
            summary.failure_reasons[reason] = (
                summary.failure_reasons.get(reason, 0) + 1
            )

        # Track trend from score tracker
        score_hist = self.score_tracker.get_history(wf_id, "workflow")
        if score_hist:
            summary.trend = score_hist.trend

        summary.last_run = record.completed_at
        summary.recent_runs.append(record)
        if len(summary.recent_runs) > 20:
            summary.recent_runs = summary.recent_runs[-20:]

    # ── Background Consolidation ─────────────────────────────────────────

    async def _run_consolidation_loop(self) -> None:
        """Background loop that periodically runs learning cycles."""
        while self._running:
            try:
                # Run consolidation on all tracked entities
                for wf_id in self._workflow_analytics:
                    await self.run_learning_cycle(
                        source_entity_id=wf_id,
                        source_entity_type="workflow",
                    )
                    await asyncio.sleep(0.1)  # Throttle

                await asyncio.sleep(self._consolidation_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self._consolidation_interval)

    # ── Status ───────────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of the learning engine state."""
        return {
            "total_cycles": self._state.total_cycles,
            "total_patterns": self._state.total_patterns_detected,
            "total_recommendations": self._state.total_recommendations,
            "total_knowledge_entries": self._state.total_knowledge_entries,
            "workflow_runs_tracked": self._state.workflow_runs_tracked,
            "workflows_with_analytics": len(self._workflow_analytics),
            "executive_decisions": len(self._executive_records),
            "agent_tasks": len(self._agent_records),
            "learning_cycles": len(self._learning_cycles),
            "playbook_evolutions": len(self._playbook_evolutions),
            "last_consolidation": (
                self._state.last_consolidation.isoformat()
                if self._state.last_consolidation else None
            ),
        }