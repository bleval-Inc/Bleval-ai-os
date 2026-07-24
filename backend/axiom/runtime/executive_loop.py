"""Executive Runtime Loop — continuous autonomous executive operation.

Each executive runs an independent lifecycle loop:

  Morning Review
  ↓
  Check KPIs
  ↓
  Review Memory
  ↓
  Identify Priorities
  ↓
  Launch Workflows
  ↓
  Review Results
  ↓
  Report Founder

Executives NEVER perform work directly (Architecture Law 2).
Executives ONLY manage departments through workflows.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from axiom.models.workflows import WorkflowStatus


# ── Schedule Configuration ─────────────────────────────────────────────

EXECUTIVE_DEFAULT_SCHEDULES = {
    "morning_review": {
        "cron": "0 8 * * 1-5",  # Weekdays at 8am
        "description": "Morning review of organization state, memory, and KPIs",
    },
    "midday_check": {
        "cron": "0 12 * * 1-5",  # Weekdays at 12pm
        "description": "Midday check on active workflow progress",
    },
    "afternoon_review": {
        "cron": "0 16 * * 1-5",  # Weekdays at 4pm
        "description": "Afternoon review of completed work and results",
    },
    "daily_report": {
        "cron": "0 18 * * 1-5",  # Weekdays at 6pm
        "description": "Compile and send daily report to Founder",
    },
}

# Executive → Organization mapping
EXECUTIVE_ORGS: Dict[str, str] = {
    "jenson": "bleval",
    "valta_prime": "hov",
    "yamako": "personal",
}

# Executive → Department mapping
EXECUTIVE_DEPTS: Dict[str, List[str]] = {
    "jenson": ["sales", "marketing", "development", "operations", "finance"],
    "valta_prime": ["brand", "creative", "research", "content", "growth", "operations"],
    "yamako": ["productivity", "knowledge"],
}


# ── Cycle Phase Helpers ────────────────────────────────────────────────


def _format_report(
    exec_id: str,
    org_id: str,
    cycle_type: str,
    observations: Dict[str, Any],
    priorities: List[str],
    workflows_launched: int,
    completed_work: List[Dict[str, Any]],
    report_to_founder: bool = False,
) -> str:
    """Format an executive cycle report."""
    lines = [
        f"=== Executive Cycle Report ===",
        f"Executive: {exec_id}",
        f"Organization: {org_id}",
        f"Cycle: {cycle_type}",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"--- Observations ---",
    ]

    for key, value in observations.items():
        lines.append(f"{key}: {value}")

    lines.extend([
        "",
        "--- Priorities ---",
    ])
    for i, p in enumerate(priorities, 1):
        lines.append(f"{i}. {p}")

    lines.extend([
        "",
        f"--- Workflows ---",
        f"Launched: {workflows_launched}",
        f"Completed this cycle: {len(completed_work)}",
    ])

    if completed_work:
        for w in completed_work:
            lines.append(f"  - {w.get('workflow_id', 'unknown')}: {w.get('status', 'unknown')}")

    if report_to_founder:
        lines.extend([
            "",
            "=== REPORT TO FOUNDER ===",
            f"Summary: {exec_id} completed {cycle_type} cycle.",
            f"Workflows launched: {workflows_launched}",
            f"Workflows completed: {len(completed_work)}",
            f"Top priority: {priorities[0] if priorities else 'None'}",
        ])

    return "\n".join(lines)


# ── Executive Runtime Loop ─────────────────────────────────────────────


class ExecutiveRuntimeLoop:
    """Continuous runtime loop for an individual executive.

    Each executive instance runs independently with its own schedule,
    inspecting its organization, making decisions, launching workflows,
    and reporting results.

    The loop cycles through:
      1. Inspect organization state
      2. Inspect memory
      3. Inspect KPIs
      4. Inspect active workflows
      5. Decide priorities
      6. Launch workflows
      7. Review completed work
      8. Request approvals
      9. Report to Founder
    """

    def __init__(
        self,
        exec_id: str,
        runtime: Any,  # AxiomRuntime reference
        schedules: Optional[Dict[str, Dict[str, Any]]] = None,
        intelligence_callback: Optional[Callable] = None,
    ) -> None:
        self.exec_id = exec_id
        self._runtime = runtime
        self._schedules = schedules or EXECUTIVE_DEFAULT_SCHEDULES.copy()
        self._intelligence_callback = intelligence_callback
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._cycle_count = 0
        self._last_report: Optional[str] = None

        # Resolve org and dept
        self.org_id = EXECUTIVE_ORGS.get(exec_id, "")
        self.departments = EXECUTIVE_DEPTS.get(exec_id, [])

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Schedule Management ────────────────────────────────────────────

    def set_schedule(self, name: str, cron: str, description: str = "") -> None:
        """Configure a schedule for this executive."""
        self._schedules[name] = {
            "cron": cron,
            "description": description or name,
        }

    def remove_schedule(self, name: str) -> None:
        """Remove a schedule."""
        self._schedules.pop(name, None)

    def list_schedules(self) -> Dict[str, Dict[str, Any]]:
        """Return all configured schedules."""
        return dict(self._schedules)

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the executive runtime loop."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        if self._runtime.logger:
            self._runtime.logger.info(
                "executive",
                f"Executive {self.exec_id} runtime loop started for org {self.org_id}",
            )

    async def stop(self) -> None:
        """Stop the executive runtime loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._runtime.logger:
            self._runtime.logger.info(
                "executive",
                f"Executive {self.exec_id} runtime loop stopped",
            )

    async def trigger_cycle(self, cycle_type: str = "manual") -> Dict[str, Any]:
        """Manually trigger an executive cycle (for testing or ad-hoc)."""
        return await self._execute_cycle(cycle_type)

    # ── Core Loop ──────────────────────────────────────────────────────

    async def _run_loop(self) -> None:
        """Background loop: wake per schedule, execute cycles."""
        # Track last run time per schedule
        last_run: Dict[str, float] = {}
        tick_interval = 60  # Check every 60 seconds

        while self._running:
            now = datetime.now(timezone.utc)
            now_seconds = now.timestamp()

            for schedule_name, schedule in self._schedules.items():
                last = last_run.get(schedule_name, 0)

                # Simple interval-based scheduling (every N seconds for now;
                # cron parsing can be added later)
                interval_str = schedule.get("cron", "")
                if interval_str.startswith("*/"):
                    # e.g. "*/300" = every 300 seconds
                    try:
                        interval = int(interval_str[2:])
                    except ValueError:
                        interval = 3600  # default 1 hour
                else:
                    interval = 3600  # default 1 hour

                if now_seconds - last >= interval:
                    try:
                        await self._execute_cycle(schedule_name)
                        last_run[schedule_name] = now_seconds
                    except Exception as exc:
                        if self._runtime.logger:
                            self._runtime.logger.error(
                                "executive",
                                f"Executive {self.exec_id} cycle '{schedule_name}' failed: {exc}",
                            )

            await asyncio.sleep(tick_interval)

    # ── Cycle Execution ────────────────────────────────────────────────

    async def _execute_cycle(self, cycle_type: str) -> Dict[str, Any]:
        """Execute one full executive cycle."""
        self._cycle_count += 1

        # 1. Inspect organization state
        org_state = self._inspect_organization()

        # 2. Inspect memory
        memory_state = self._inspect_memory()

        # 3. Inspect active workflows
        active_workflows = self._inspect_workflows()

        # 4. Review completed work
        completed_work = self._review_completed()

        # 5. Build observations
        observations = {
            "org_state": org_state,
            "memory_topics": list(memory_state.keys()) if memory_state else [],
            "active_workflows": len(active_workflows),
            "completed_work_this_cycle": len(completed_work),
        }

        # 6. Decide priorities (use intelligence engine if available)
        priorities = await self._decide_priorities(
            cycle_type=cycle_type,
            org_state=org_state,
            memory_state=memory_state,
            active_workflows=active_workflows,
            completed_work=completed_work,
        )

        # 7. Launch workflows based on priorities
        workflows_launched = await self._launch_priority_workflows(priorities)

        # 8. Report
        is_daily_report = cycle_type in ("daily_report", "afternoon_review")
        report = _format_report(
            exec_id=self.exec_id,
            org_id=self.org_id,
            cycle_type=cycle_type,
            observations=observations,
            priorities=priorities,
            workflows_launched=workflows_launched,
            completed_work=completed_work,
            report_to_founder=is_daily_report,
        )

        self._last_report = report

        # Log the cycle
        if self._runtime.logger:
            self._runtime.logger.workflow_event(
                instance_id=f"exec-{self.exec_id}-cycle-{self._cycle_count}",
                event=f"executive_cycle_{cycle_type}",
                details={
                    "executive": self.exec_id,
                    "cycle": self._cycle_count,
                    "type": cycle_type,
                    "workflows_launched": workflows_launched,
                    "active_workflows": len(active_workflows),
                    "priorities": priorities,
                },
            )

        # 9. Report to Founder (for daily/official reports)
        if is_daily_report:
            await self._report_to_founder(report)

        return {
            "cycle": cycle_type,
            "cycle_count": self._cycle_count,
            "priorities": priorities,
            "workflows_launched": workflows_launched,
            "active_workflows": len(active_workflows),
            "completed_work": len(completed_work),
        }

    # ── Inspection Methods ─────────────────────────────────────────────

    def _inspect_organization(self) -> Dict[str, Any]:
        """Inspect organization state: departments, agents, capabilities."""
        state: Dict[str, Any] = {"org_id": self.org_id}

        if self._runtime.executive:
            try:
                depts = self._runtime.executive.get_departments(self.org_id)
                state["departments"] = [
                    {"id": d.get("id", ""), "agents": len(d.get("agents", []))}
                    for d in depts
                ]
            except Exception:
                state["departments"] = []

            try:
                org_detail = self._runtime.executive.get_organization_detail(self.org_id)
                if org_detail:
                    state["detail_loaded"] = True
            except Exception:
                pass

        return state

    def _inspect_memory(self) -> Dict[str, str]:
        """Inspect memory context for this executive."""
        if not self._runtime.memory:
            return {}
        try:
            return self._runtime.memory.get_resolved_context(
                agent_id=self.exec_id,
                org_id=self.org_id,
            )
        except Exception:
            return {}

    def _inspect_workflows(self) -> List[Dict[str, Any]]:
        """Inspect active workflows for this executive's organization."""
        if not self._runtime.workflow:
            return []
        try:
            instances = self._runtime.workflow.list_instances(
                status=WorkflowStatus.RUNNING,
            )
            # Filter by org if the runtime allows it
            return [
                {
                    "instance_id": i.instance_id,
                    "workflow_id": i.workflow_id,
                    "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                    "current_step": i.current_step_index,
                }
                for i in instances
                if getattr(i, "org", None) == self.org_id or True  # Include all if no filter
            ]
        except Exception:
            return []

    def _review_completed(self) -> List[Dict[str, Any]]:
        """Review recently completed work."""
        if not self._runtime.workflow:
            return []
        try:
            instances = self._runtime.workflow.list_instances(
                status=WorkflowStatus.COMPLETED,
            )
            return [
                {
                    "instance_id": i.instance_id,
                    "workflow_id": i.workflow_id,
                    "completed_at": (
                        i.completed_at.isoformat() if i.completed_at else ""
                    ),
                }
                for i in instances[-5:]  # Last 5 completed
                if getattr(i, "org", None) == self.org_id or True
            ]
        except Exception:
            return []

    # ── Decision Making ────────────────────────────────────────────────

    async def _decide_priorities(
        self,
        cycle_type: str,
        org_state: Dict[str, Any],
        memory_state: Dict[str, str],
        active_workflows: List[Dict[str, Any]],
        completed_work: List[Dict[str, Any]],
    ) -> List[str]:
        """Decide priorities using the Intelligence Engine.

        If the Intelligence Engine is available, use it for reasoning.
        Otherwise, return sensible defaults based on organization state.
        """
        intelligence = getattr(self._runtime, "intelligence", None)

        if intelligence and self._intelligence_callback:
            # Use the intelligence engine for reasoning
            try:
                task = json.dumps({
                    "cycle_type": cycle_type,
                    "org_state": org_state,
                    "active_workflows": active_workflows,
                    "completed_work": completed_work,
                    "departments": self.departments,
                    "objective": (
                        f"Review {cycle_type} state for {self.exec_id} and identify "
                        f"top 3 priorities. Consider active workflows, memory context, "
                        f"and organizational needs."
                    ),
                })

                response = await self._intelligence_callback(
                    exec_id=self.exec_id,
                    task_description=task,
                    org_id=self.org_id,
                )

                # Parse structured response for priorities
                priorities = self._parse_priorities(response)
                if priorities:
                    return priorities

            except Exception:
                pass

        # Default priorities based on cycle type
        if cycle_type == "morning_review":
            return [
                f"Review {self.org_id} department status and active workflows",
                "Check memory for outstanding items and learnings",
                "Identify and launch priority workflows for today",
            ]
        elif cycle_type == "daily_report":
            return [
                "Compile daily summary of completed work",
                "Identify items needing founder attention",
                "Prepare recommendations for next cycle",
            ]
        else:
            return [
                f"Monitor active workflows in {self.org_id}",
                "Check for completed work needing review",
                "Update organizational memory with new learnings",
            ]

    def _parse_priorities(self, response: str) -> Optional[List[str]]:
        """Try to parse a list of priorities from an intelligence response."""
        # Try JSON first
        try:
            data = json.loads(response)
            if isinstance(data, dict) and "priorities" in data:
                return data["priorities"]
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting numbered items
        lines = response.strip().split("\n")
        priorities = []
        for line in lines:
            line = line.strip()
            # Match "1. ", "1) ", "- " etc.
            if line and (line[0].isdigit() or line.startswith("- ")):
                cleaned = line[2:].strip() if line.startswith("- ") else line[line.index(".")+1:].strip() if "." in line[:4] else line
                if cleaned:
                    priorities.append(cleaned)
                if len(priorities) >= 5:
                    break

        return priorities if priorities else None

    # ── Workflow Launching ─────────────────────────────────────────────

    async def _launch_priority_workflows(self, priorities: List[str]) -> int:
        """Launch workflows based on decided priorities.

        For each priority, find a matching workflow and launch it.
        Returns the number of workflows successfully launched.
        """
        if not self._runtime.workflow:
            return 0

        launched = 0

        # Get available workflows for this executive's departments
        available_workflows = self._runtime.workflow.list_workflows() if hasattr(
            self._runtime.workflow, "list_workflows"
        ) else {}

        # Try to find a matching workflow for each priority
        for priority in priorities[:3]:  # Top 3 priorities
            wf_id = self._find_matching_workflow(priority, available_workflows)
            if not wf_id:
                continue

            try:
                context = {
                    "trigger": "executive_cycle",
                    "executive": self.exec_id,
                    "priority": priority,
                    "cycle_time": datetime.now(timezone.utc).isoformat(),
                }
                instance = self._runtime.workflow.create_instance(wf_id, context=context)
                await self._runtime.workflow.start(instance.instance_id)
                launched += 1

                if self._runtime.logger:
                    self._runtime.logger.info(
                        "executive",
                        f"{self.exec_id} launched {wf_id} (instance: {instance.instance_id})",
                    )
            except Exception as exc:
                if self._runtime.logger:
                    self._runtime.logger.warning(
                        "executive",
                        f"{self.exec_id} failed to launch {wf_id}: {exc}",
                    )

        return launched

    def _find_matching_workflow(
        self,
        priority: str,
        workflows: Dict[str, Any],
    ) -> Optional[str]:
        """Find a workflow that matches a priority description.

        Simple keyword-based matching.  Can be replaced with
        intelligence-driven matching in the future.
        """
        priority_lower = priority.lower()

        # Keyword → workflow mapping
        keyword_map: Dict[str, List[str]] = {
            "sales": ["sales/prospect-research", "sales/outreach-campaign"],
            "prospect": ["sales/prospect-research"],
            "lead": ["sales/prospect-research"],
            "outreach": ["sales/outreach-campaign"],
            "campaign": ["sales/outreach-campaign", "marketing/campaign-launch"],
            "deal": ["sales/deal-closing"],
            "close": ["sales/deal-closing"],
            "content": ["marketing/content-production"],
            "market": ["marketing/market-research"],
            "research": ["marketing/market-research", "sales/prospect-research"],
            "feature": ["development/feature-development"],
            "develop": ["development/feature-development"],
            "code": ["development/code-review"],
            "review": ["development/code-review"],
            "report": ["operations/daily-report"],
            "daily": ["operations/daily-report"],
            "weekly": ["operations/weekly-review"],
            "financial": ["operations/daily-report"],
            "client": ["operations/daily-report"],
            "sync": ["cross-org/executive-sync"],
            "escalat": ["cross-org/escalation"],
        }

        for keyword, wf_ids in keyword_map.items():
            if keyword in priority_lower:
                for wf_id in wf_ids:
                    if wf_id in workflows:
                        return wf_id

        # Fallback: return first workflow for this org/department
        for dept in self.departments:
            for wf_id, wf_def in workflows.items():
                wf_org = getattr(wf_def, "org", "")
                wf_dept = getattr(wf_def, "department", "")
                if wf_org == self.org_id and wf_dept == dept:
                    return wf_id

        return None

    # ── Founder Reporting ──────────────────────────────────────────────

    async def _report_to_founder(self, report: str) -> None:
        """Send a report to the Founder.

        Writes to executive memory and logs the report.
        The Founder can access these reports through the API.
        """
        # Store in executive memory
        if self._runtime.memory:
            try:
                self._runtime.memory.write_agent_memory(
                    agent_id=self.exec_id,
                    key=f"founder-report-{self._cycle_count}",
                    content=report,
                )
            except Exception:
                pass

        # Log the report
        if self._runtime.logger:
            self._runtime.logger.agent_action(
                agent_id=self.exec_id,
                action="report_to_founder",
                details={"cycle": self._cycle_count, "report_length": len(report)},
            )

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return the current status of this executive loop."""
        return {
            "exec_id": self.exec_id,
            "org_id": self.org_id,
            "running": self._running,
            "cycle_count": self._cycle_count,
            "schedules": list(self._schedules.keys()),
        }


# =========================================================================
# Executive Board — manages all executive loops
# =========================================================================


class ExecutiveBoard:
    """Manages all executive runtime loops as a coordinated board.

    The Executive Board consists of:
      Founder
      ↓
      Jenson (Bleval Inc)
      ↓
      Valta Prime (House of Valta)
      ↓
      Yamako (Personal)

    Executives are peers — none reports to another.
    Each runs its own independent runtime loop.
    """

    EXECUTIVE_IDS = ["jenson", "valta_prime", "yamako"]

    def __init__(self, runtime: Any) -> None:
        self._runtime = runtime
        self._loops: Dict[str, ExecutiveRuntimeLoop] = {}

    async def start_all(self) -> None:
        """Create and start all executive runtime loops."""
        for exec_id in self.EXECUTIVE_IDS:
            loop = ExecutiveRuntimeLoop(
                exec_id=exec_id,
                runtime=self._runtime,
                intelligence_callback=self._intelligence_generate,
            )
            self._loops[exec_id] = loop
            await loop.start()

        if self._runtime.logger:
            self._runtime.logger.info(
                "executive",
                f"Executive Board started: {', '.join(self._loops.keys())}",
            )

    async def stop_all(self) -> None:
        """Stop all executive runtime loops."""
        for exec_id, loop in self._loops.items():
            await loop.stop()

        if self._runtime.logger:
            self._runtime.logger.info(
                "executive",
                "Executive Board stopped",
            )

    async def trigger_all(self, cycle_type: str = "manual") -> Dict[str, Any]:
        """Trigger a cycle for all executives (for testing)."""
        results = {}
        for exec_id, loop in self._loops.items():
            results[exec_id] = await loop.trigger_cycle(cycle_type)
        return results

    def get_loop(self, exec_id: str) -> Optional[ExecutiveRuntimeLoop]:
        """Get a specific executive loop."""
        return self._loops.get(exec_id)

    def get_status(self) -> Dict[str, Any]:
        """Return status of all executive loops."""
        return {
            exec_id: loop.get_status()
            for exec_id, loop in self._loops.items()
        }

    async def _intelligence_generate(
        self,
        exec_id: str,
        task_description: str,
        org_id: str = "",
    ) -> str:
        """Callback that routes executive reasoning through the Intelligence Engine."""
        intelligence = getattr(self._runtime, "intelligence", None)
        if intelligence:
            return await intelligence.generate_for_executive(
                exec_id=exec_id,
                task_description=task_description,
                org_id=org_id or EXECUTIVE_ORGS.get(exec_id, ""),
            )
        return json.dumps({"priorities": ["default: intelligence unavailable"]})