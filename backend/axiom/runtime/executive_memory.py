"""Executive Memory Manager — persistent memory for each executive.

Each executive has persistent memory stored in core/executives/memory/:
  - {exec_id}-kpis.md           — KPI definitions and current values
  - {exec_id}-decision-history.md — decision log with outcomes and learnings
  - {exec_id}-learnings.md      — learning history (patterns, insights)
  - {exec_id}-state.json        — runtime state (last cycle, active context)

The MemoryManager loads from these files on bootstrap and writes back
after each executive cycle, giving each executive genuine persistent state
that survives restarts.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from axiom.models.executive import (
    DecisionOutcome,
    ExecutiveDecision,
    ExecutiveKPIDefinition,
    ExecutiveLearning,
    KPIStatus,
)


# ── Paths ──────────────────────────────────────────────────────────────────────

MEMORY_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "../../../core/executives/memory"
MEMORY_DIR = MEMORY_DIR.resolve()

KPIS_FILE_TEMPLATE = "{exec_id}-kpis.md"
DECISIONS_FILE_TEMPLATE = "{exec_id}-decision-history.md"
LEARNINGS_FILE_TEMPLATE = "{exec_id}-learnings.md"
STATE_FILE_TEMPLATE = "{exec_id}-state.json"


# ── Executive Memory Manager ───────────────────────────────────────────────────


class ExecutiveMemoryManager:
    """Persistent memory for a single executive.

    Loads from markdown files on init, provides runtime read/write access,
    and supports serialising back to files for durability.
    """

    def __init__(self, exec_id: str, runtime: Any = None) -> None:
        self.exec_id = exec_id
        self._runtime = runtime
        self._memory_dir = MEMORY_DIR

        # In-memory state
        self._kpis: Dict[str, ExecutiveKPIDefinition] = {}
        self._decisions: List[ExecutiveDecision] = []
        self._learnings: List[ExecutiveLearning] = []
        self._state: Dict[str, Any] = {}
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Loading ────────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load all persistent memory for this executive from disk."""
        self._load_kpis()
        self._load_decisions()
        self._load_learnings()
        self._load_state()
        self._loaded = True

        if self._runtime and hasattr(self._runtime, "logger") and self._runtime.logger:
            self._runtime.logger.info(
                "executive_memory",
                f"Loaded memory for {self.exec_id}: "
                f"{len(self._kpis)} KPIs, {len(self._decisions)} decisions, "
                f"{len(self._learnings)} learnings",
            )

    def _load_kpis(self) -> None:
        """Load KPIs from markdown file."""
        kpi_file = self._memory_dir / KPIS_FILE_TEMPLATE.format(exec_id=self.exec_id)
        if not kpi_file.exists():
            return

        content = kpi_file.read_text(encoding="utf-8")
        # Parse KPI entries from the markdown — extract definitions by section
        self._kpis = self._parse_kpis_from_markdown(content, self.exec_id)

    def _load_decisions(self) -> None:
        """Load decision history from markdown file."""
        dec_file = self._memory_dir / DECISIONS_FILE_TEMPLATE.format(exec_id=self.exec_id)
        if not dec_file.exists():
            return

        content = dec_file.read_text(encoding="utf-8")
        self._decisions = self._parse_decisions_from_markdown(content, self.exec_id)

    def _load_learnings(self) -> None:
        """Load learning history from file."""
        learn_file = self._memory_dir / LEARNINGS_FILE_TEMPLATE.format(exec_id=self.exec_id)
        if not learn_file.exists():
            return
        content = learn_file.read_text(encoding="utf-8")
        self._learnings = self._parse_learnings_from_markdown(content, self.exec_id)

    def _load_state(self) -> None:
        """Load runtime state from JSON file."""
        state_file = self._memory_dir / STATE_FILE_TEMPLATE.format(exec_id=self.exec_id)
        if not state_file.exists():
            self._state = {
                "exec_id": self.exec_id,
                "last_cycle": None,
                "cycle_count": 0,
                "last_board_meeting": None,
            }
            return
        try:
            self._state = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._state = {"exec_id": self.exec_id}

    # ── Saving ─────────────────────────────────────────────────────────────────

    def save_state(self) -> None:
        """Save runtime state to JSON file."""
        state_file = self._memory_dir / STATE_FILE_TEMPLATE.format(exec_id=self.exec_id)
        try:
            self._ensure_memory_dir()
            state_file.write_text(json.dumps(self._state, indent=2, default=str), encoding="utf-8")
        except OSError:
            pass

    def _ensure_memory_dir(self) -> None:
        """Ensure the memory directory exists."""
        self._memory_dir.mkdir(parents=True, exist_ok=True)

    # ── KPI Access ─────────────────────────────────────────────────────────────

    def get_kpis(self) -> Dict[str, ExecutiveKPIDefinition]:
        """Get all KPIs for this executive."""
        return dict(self._kpis)

    def get_kpi(self, kpi_id: str) -> Optional[ExecutiveKPIDefinition]:
        """Get a specific KPI by ID."""
        return self._kpis.get(kpi_id)

    def update_kpi(self, kpi_id: str, current_value: float, status: Optional[KPIStatus] = None) -> None:
        """Update a KPI's current value and status."""
        kpi = self._kpis.get(kpi_id)
        if not kpi:
            return
        kpi.previous_value = kpi.current_value
        kpi.current_value = current_value
        kpi.last_updated = datetime.now(timezone.utc)
        if status:
            kpi.status = status
        # Update trend
        if kpi.current_value > kpi.previous_value:
            kpi.trend = "improving"
        elif kpi.current_value < kpi.previous_value:
            kpi.trend = "declining"
        else:
            kpi.trend = "stable"

    def get_kpi_snapshot(self) -> Dict[str, float]:
        """Get a simple KPI name → value snapshot for board room publishing."""
        return {
            kpi.name: kpi.current_value
            for kpi in self._kpis.values()
        }

    # ── Decision Recording ─────────────────────────────────────────────────────

    def record_decision(
        self,
        decision_type: str,
        description: str,
        reasoning: str = "",
        outcome: DecisionOutcome = DecisionOutcome.PENDING,
        context: Optional[Dict[str, Any]] = None,
        alternatives: Optional[List[str]] = None,
        impact_score: float = 0.0,
        tags: Optional[List[str]] = None,
    ) -> ExecutiveDecision:
        """Record a new executive decision."""
        import uuid

        decision = ExecutiveDecision(
            decision_id=f"{self.exec_id.upper()[:4]}-DEC-{len(self._decisions) + 1:04d}",
            exec_id=self.exec_id,
            decision_type=decision_type,
            description=description,
            reasoning=reasoning,
            context=context or {},
            alternatives_considered=alternatives or [],
            outcome=outcome,
            impact_score=impact_score,
            tags=tags or [],
        )
        self._decisions.append(decision)
        self._state["last_decision_id"] = decision.decision_id
        self.save_state()
        return decision

    def get_decisions(self, limit: int = 20) -> List[ExecutiveDecision]:
        """Get recent decisions, newest first."""
        return sorted(
            self._decisions,
            key=lambda d: d.timestamp,
            reverse=True,
        )[:limit]

    # ── Learning Recording ────────────────────────────────────────────────────

    def record_learning(
        self,
        pattern_type: str,
        description: str,
        context: str = "",
        impact: str = "",
        source_decision_id: str = "",
    ) -> ExecutiveLearning:
        """Record a new learning."""
        import uuid

        learning = ExecutiveLearning(
            learning_id=f"LRN-{len(self._learnings) + 1:04d}",
            exec_id=self.exec_id,
            pattern_type=pattern_type,
            description=description,
            context=context,
            impact=impact,
            source_decision_id=source_decision_id,
        )
        self._learnings.append(learning)
        return learning

    def get_learnings(self, limit: int = 10) -> List[ExecutiveLearning]:
        """Get recent learnings, newest first."""
        return sorted(
            self._learnings,
            key=lambda l: l.timestamp,
            reverse=True,
        )[:limit]

    def get_unincorporated_learnings(self) -> List[ExecutiveLearning]:
        """Get learnings that haven't been incorporated yet."""
        return [l for l in self._learnings if not l.incorporated]

    # ── State Management ──────────────────────────────────────────────────────

    def update_state(self, key: str, value: Any) -> None:
        """Update a state field and persist."""
        self._state[key] = value
        self.save_state()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state field."""
        return self._state.get(key, default)

    # ── Markdown Parsing (simple section-based) ───────────────────────────────

    def _parse_kpis_from_markdown(
        self, content: str, exec_id: str
    ) -> Dict[str, ExecutiveKPIDefinition]:
        """Parse KPI definitions from markdown files.

        Scans for ## headers containing KPI names and extracts
        key-value pairs from tables.
        """
        kpis: Dict[str, ExecutiveKPIDefinition] = {}
        lines = content.split("\n")

        current_section = ""
        current_kpi_name = ""
        current_target = 0.0
        current_category = "general"

        for i, line in enumerate(lines):
            # Track sections (## Department headers)
            if line.startswith("## "):
                current_section = line[3:].strip().lower().replace(" ", "_")

            # Track KPI entries (### headers inside sections)
            if line.startswith("### "):
                # Save previous KPI if exists
                if current_kpi_name:
                    kpi_id = self._make_kpi_id(current_section, current_kpi_name)
                    kpis[kpi_id] = ExecutiveKPIDefinition(
                        kpi_id=kpi_id,
                        name=current_kpi_name,
                        target=current_target,
                        category=current_section,
                        status=KPIStatus.NOT_TRACKED,
                    )
                current_kpi_name = line[4:].strip()
                current_target = 0.0

            # Extract Current Target from tables
            if "| Current Target " in line and "|" in line:
                parts = [p.strip() for p in line.split("|")]
                for p in parts:
                    if p and p[0].isdigit():
                        try:
                            current_target = float(p.split("/")[0].split("%")[0].strip())
                        except ValueError:
                            pass

            # Extract Metric name from row data
            if "| **Metric** |" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) > 2:
                    metric_name = parts[2].strip()
                    if metric_name:
                        current_kpi_name = metric_name

        # Save last KPI
        if current_kpi_name:
            kpi_id = self._make_kpi_id(current_section, current_kpi_name)
            kpis[kpi_id] = ExecutiveKPIDefinition(
                kpi_id=kpi_id,
                name=current_kpi_name,
                target=current_target,
                category=current_section,
                status=KPIStatus.NOT_TRACKED,
            )

        return kpis

    def _parse_decisions_from_markdown(
        self, content: str, exec_id: str
    ) -> List[ExecutiveDecision]:
        """Parse decisions from markdown table rows."""
        decisions: List[ExecutiveDecision] = []
        lines = content.split("\n")
        in_table = False

        for line in lines:
            # Detect table rows with pipe separators containing dates
            if line.startswith("|") and "|" in line[1:]:
                parts = [p.strip() for p in line.split("|")]
                parts = [p for p in parts if p]  # Remove empty strings

                if len(parts) >= 4:
                    date_str = parts[0]
                    # Check if first part looks like a date
                    if self._looks_like_date(date_str):
                        dec_type = parts[2] if len(parts) > 2 else "general"
                        description = parts[3] if len(parts) > 3 else ""
                        outcome_str = parts[4] if len(parts) > 4 else "pending"

                        outcome = DecisionOutcome.PENDING
                        if "success" in outcome_str.lower() or "profit" in outcome_str.lower():
                            outcome = DecisionOutcome.SUCCESS
                        elif "fail" in outcome_str.lower() or "loss" in outcome_str.lower():
                            outcome = DecisionOutcome.FAILED

                        decisions.append(
                            ExecutiveDecision(
                                decision_id=f"{exec_id.upper()[:4]}-DEC-{len(decisions) + 1:04d}",
                                exec_id=exec_id,
                                decision_type=dec_type,
                                description=description[:200],
                                outcome=outcome,
                            )
                        )

            elif line.startswith("---"):
                in_table = not in_table

        return decisions

    def _parse_learnings_from_markdown(
        self, content: str, exec_id: str
    ) -> List[ExecutiveLearning]:
        """Parse learnings from markdown file."""
        learnings: List[ExecutiveLearning] = []
        lines = content.split("\n")

        for line in lines:
            if line.startswith("- ") and ":" in line:
                parts = line[2:].split(":", 1)
                pattern_type = parts[0].strip().lower()
                description = parts[1].strip()
                # Categorize by common pattern types
                ptype = "insight"
                if any(w in pattern_type for w in ["fail", "error", "mistake"]):
                    ptype = "failure"
                elif any(w in pattern_type for w in ["success", "win", "profit"]):
                    ptype = "success"
                elif any(w in pattern_type for w in ["optimize", "improve", "better"]):
                    ptype = "optimization"

                learnings.append(
                    ExecutiveLearning(
                        learning_id=f"LRN-{len(learnings) + 1:04d}",
                        exec_id=exec_id,
                        pattern_type=ptype,
                        description=description[:200],
                    )
                )

        return learnings

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_kpi_id(self, section: str, name: str) -> str:
        """Create a KPI ID from section and name."""
        prefix = "".join(w[0] for w in section.split("_") if w).upper()[:3]
        short_name = name.lower().replace(" ", "_").replace("%", "pct")[:20]
        return f"{prefix}_{short_name}"

    def _looks_like_date(self, s: str) -> bool:
        """Check if a string looks like a date (YYYY-MM-DD)."""
        s = s.strip()
        if len(s) < 8:
            return False
        parts = s.split("-")
        if len(parts) == 3:
            try:
                int(parts[0])
                int(parts[1])
                int(parts[2])
                return True
            except ValueError:
                pass
        return False