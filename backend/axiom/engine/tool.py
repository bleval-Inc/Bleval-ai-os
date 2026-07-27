"""Tool Engine — permission checking and capability resolution.

The Tool Engine provides:
- Tool discovery per organization
- Permission checking (can/cannot rules)
- Capability-to-agent resolution
- Audit logging

In this phase the engine is a permission checker and capability resolver,
not a tool executor.  Actual tool execution (Slack API, GitHub API, etc.)
would be the Provider Abstraction layer in a future phase.
"""

from datetime import datetime, timezone
from typing import Dict, List, Tuple

from axiom.config import settings
from axiom.models.configs import ToolDef
from axiom.registry.agent import AgentRegistryLoader
from axiom.registry.capability import CapabilityRegistryLoader
from axiom.registry.organization import OrganizationRegistryLoader


class ToolEngine:
    """Permission checking, capability resolution, and audit logging."""

    def __init__(self) -> None:
        self._org_loader = OrganizationRegistryLoader()
        self._agent_loader = AgentRegistryLoader()
        self._cap_loader = CapabilityRegistryLoader()

        # Cache: org_id -> tools
        self._tool_cache: Dict[str, List[ToolDef]] = {}

    def get_available_tools(self, org_id: str) -> List[ToolDef]:
        """Return all tools enabled for an organization."""
        if org_id not in self._tool_cache:
            registry = self._org_loader.load_tools(org_id)
            self._tool_cache[org_id] = registry.tools if registry else []
        return self._tool_cache[org_id]

    def check_permission(self, agent_id: str, action: str) -> bool:
        """Check if an agent is permitted to perform an action.

        Returns True if the action is in the agent's 'can' list and
        NOT in the agent's 'cannot' list.
        """
        detail = self._agent_loader.load_detail(agent_id)
        if detail is None:
            return False

        # Check cannot rules first (they are explicit prohibitions)
        for rule in detail.permissions.cannot:
            if self._match_rule(rule, action):
                return False

        # Check can rules
        for rule in detail.permissions.can:
            if self._match_rule(rule, action):
                return True

        # Default deny
        return False

    def check_tool_permission(self, agent_id: str, tool_id: str, capability: str) -> bool:
        """Check if an agent can use a specific tool capability.

        Verifies:
        1. The agent has the interface for the tool
        2. The agent's permissions allow the action
        """
        # Check the agent has the right permissions
        if not self.check_permission(agent_id, capability):
            return False

        # Verify the tool exists
        detail = self._agent_loader.load_detail(agent_id)
        if detail is None:
            return False

        return True

    def resolve_capability_to_agents(self, capability: str) -> List[str]:
        """Find all agents that have a given capability."""
        return self._cap_loader.resolve_agents_for_capability(capability)

    def find_agents_for_task(self, action_description: str) -> List[Tuple[str, int]]:
        """Find agents that could perform a task described in natural language.

        Returns a list of (agent_id, match_score) tuples, sorted by score.
        """
        # Use the capability search index to find relevant capabilities
        capabilities = self._cap_loader.search(action_description)

        # Score each agent by how many matching capabilities they have
        agent_scores: Dict[str, int] = {}
        for cap in capabilities:
            for agent_id in cap.agents:
                agent_scores[agent_id] = agent_scores.get(agent_id, 0) + 1

        # Sort by score descending
        sorted_agents = sorted(agent_scores.items(), key=lambda x: -x[1])
        return sorted_agents

    def audit_log(self, agent_id: str, tool_id: str, action: str, success: bool) -> None:
        """Record a tool usage audit entry.

        Writes to the runtime log directory.
        """
        log_dir = settings.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"[{timestamp}] agent={agent_id} tool={tool_id} action={action} success={success}\n"

        log_path = log_dir / "tool_audit.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def _match_rule(self, rule: str, action: str) -> bool:
        """Check if a rule matches an action.

        Supports simple wildcard matching where the rule ends with '*' to
        match any action that starts with the given prefix.
        """
        if rule.endswith("*"):
            return action.startswith(rule[:-1])
        return action == rule