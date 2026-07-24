"""Executive Engine — coordination, delegation, and approval management.

Executives coordinate departments and launch workflows.  They never perform
operational work themselves (Architecture Law 2).

The Executive Engine provides the runtime for executive agents to:
- Plan and delegate work to departments
- Launch workflows based on events or directives
- Request and handle approvals
- Communicate with other executives
"""

from typing import Any, Dict, List, Optional, Tuple

from axiom.models.configs import AgentDetail, AgentEntry
from axiom.registry.agent import AgentRegistryLoader
from axiom.registry.capability import CapabilityRegistryLoader
from axiom.registry.department import DepartmentRegistryLoader
from axiom.registry.organization import OrganizationRegistryLoader
from axiom.registry.workflow import WorkflowRegistryLoader


class ExecutiveEngine:
    """Runtime for executive agents — coordination, delegation, approvals."""

    def __init__(self) -> None:
        self._org_loader = OrganizationRegistryLoader()
        self._agent_loader = AgentRegistryLoader()
        self._dept_loader = DepartmentRegistryLoader()
        self._wf_loader = WorkflowRegistryLoader()
        self._cap_loader = CapabilityRegistryLoader()

    # ── Executive Discovery ──────────────────────────────────────────────

    def list_executives(self) -> List[AgentEntry]:
        """Return all executive agents."""
        return self._agent_loader.find_executives()

    def get_executive(self, exec_id: str) -> Optional[AgentEntry]:
        """Get an executive agent by id."""
        return self._agent_loader.get_agent(exec_id)

    def get_executive_detail(self, exec_id: str) -> Optional[AgentDetail]:
        """Get the detailed definition for an executive."""
        return self._agent_loader.load_detail(exec_id)

    def get_executive_organization(self, exec_id: str) -> Optional[str]:
        """Return the org an executive manages."""
        orgs = self._org_loader.list_organizations()
        for org in orgs:
            if exec_id in org.executives:
                return org.id
        return None

    # ── Department Management ────────────────────────────────────────────

    def get_departments(self, org_id: str) -> List[Dict[str, Any]]:
        """Return all departments in an organization with agent info."""
        depts = self._dept_loader.list_departments(org_id)
        results: List[Dict[str, Any]] = []
        for dept in depts:
            detail = self._dept_loader.load_detail(org_id, dept.id)
            results.append({
                "id": dept.id,
                "manager": dept.manager,
                "agents": dept.agents,
                "workflows": detail.workflows if detail else [],
                "capabilities": dept.capabilities,
            })
        return results

    def get_agents_in_department(self, org_id: str, dept_id: str) -> List[AgentEntry]:
        """Return all agents in a specific department."""
        return self._agent_loader.find_agents_by_department(org_id, dept_id)

    # ── Delegation / Assignment ──────────────────────────────────────────

    def delegate_task(
        self,
        action_description: str,
        org_id: str,
        dept_id: str,
    ) -> List[Tuple[str, int]]:
        """Find the best agents for a task within a department.

        Returns a list of (agent_id, match_score) sorted by match quality.
        Uses the capability search index to match descriptions to capabilities.
        """
        dept_agents = self._agent_loader.find_agents_by_department(org_id, dept_id)
        agent_ids = {a.id for a in dept_agents}

        # Search for matching capabilities
        caps = self._cap_loader.search(action_description)

        # Score within the department
        scores: Dict[str, int] = {}
        for cap in caps:
            for agent_id in cap.agents:
                if agent_id in agent_ids:
                    scores[agent_id] = scores.get(agent_id, 0) + 1

        return sorted(scores.items(), key=lambda x: -x[1])

    def find_best_agent(self, action_description: str, org_id: str, dept_id: str) -> Optional[str]:
        """Find the single best agent for a task."""
        results = self.delegate_task(action_description, org_id, dept_id)
        if results:
            return results[0][0]
        return None

    # ── Workflow Launching ───────────────────────────────────────────────

    def find_workflows_for_event(self, event_type: str) -> List[str]:
        """Find workflows triggered by an event."""
        return self._wf_loader.find_by_trigger_event(event_type)

    def find_workflows_for_department(self, org_id: str, dept_id: str) -> List[Dict[str, Any]]:
        """Find all workflows owned by a department."""
        wfs = self._wf_loader.find_by_department(org_id, dept_id)
        result = []
        for entry in wfs:
            wf_id = getattr(entry, 'id', entry) if not isinstance(entry, str) else entry
            wf = self._wf_loader.get_workflow(wf_id)
            if wf is not None:
                result.append({
                    "id": wf_id,
                    "description": wf.description,
                    "steps": len(wf.steps),
                })
        return result

    # ── Public API wrappers ──────────────────────────────────────────────

    def list_organizations(self) -> List[Any]:
        """Return all registered organizations (public API)."""
        return self._org_loader.list_organizations()

    def get_organization_detail(self, org_id: str) -> Optional[Any]:
        """Return organization detail (public API)."""
        return self._org_loader.load_org_detail(org_id)

    def list_all_agents(self) -> List[AgentEntry]:
        """Return all agents, not just executives (public API)."""
        return self._agent_loader.list_agents()

    def get_agent_detail(self, agent_id: str) -> Optional[AgentDetail]:
        """Return agent detail (public API)."""
        return self._agent_loader.load_detail(agent_id)

    def list_capabilities(self) -> List[Any]:
        """Return all capabilities (public API)."""
        return self._cap_loader.list_capabilities()

    def search_capabilities(self, query: str) -> List[Any]:
        """Search capabilities by query (public API)."""
        return self._cap_loader.search(query)

    def get_capability(self, cap_id: str) -> Optional[Any]:
        """Get a specific capability (public API)."""
        return self._cap_loader.find_capability(cap_id)

    # ── Executive Communication ──────────────────────────────────────────

    def format_message(
        self,
        from_exec: str,
        to_exec: str,
        objective: str,
        request: str,
        context: str = "",
    ) -> str:
        """Format an executive-to-executive message per the protocol."""
        parts = [
            f"FROM: {from_exec}",
            f"TO: {to_exec}",
            f"OBJECTIVE: {objective}",
            f"REQUEST: {request}",
        ]
        if context:
            parts.append(f"CONTEXT: {context}")
        parts.append(f"EXPECTED RESPONSE: Acknowledgement within 1 cycle")
        return "\n\n".join(parts)