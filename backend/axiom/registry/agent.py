"""Registry loader for agents."""

from pathlib import Path
from typing import Dict, List, Optional

from axiom.config import agents_path
from axiom.models.configs import (
    AgentDetail,
    AgentEntry,
    AgentRegistry,
)
from axiom.registry.loader import YAMLLoader


class AgentRegistryLoader:
    """Loads agent definitions from YAML and Markdown files."""

    def __init__(self) -> None:
        self._base = agents_path()

    def load_registry(self) -> AgentRegistry:
        """Load the master agents/agent-registry.yaml."""
        data = YAMLLoader.load_yaml(self._base / "agent-registry.yaml")
        return AgentRegistry(**data)

    def list_agents(self) -> List[AgentEntry]:
        """Return all registered agents."""
        return self.load_registry().agents

    def get_agent(self, agent_id: str) -> Optional[AgentEntry]:
        """Find a single agent by id in the registry."""
        for agent in self.list_agents():
            if agent.id == agent_id:
                return agent
        return None

    def load_detail(self, agent_id: str) -> Optional[AgentDetail]:
        """Load the detailed agent.yml for a given agent id.

        Searches top-level (executives) then nested (specialists).
        """
        path = self._resolve_agent_yml(agent_id)
        if path is None:
            return None
        data = YAMLLoader.load_yaml(path)
        return AgentDetail(**data)

    def _resolve_agent_yml(self, agent_id: str) -> Optional[Path]:
        """Find agent.yml for the given agent_id."""
        # Top-level executive agents
        top = self._base / f"{agent_id}.yml"
        if top.exists():
            return top

        # Nested specialist agents: agents/<org>/<dept>/<agent_id>/agent.yml
        for org_dir in self._base.iterdir():
            if not org_dir.is_dir() or org_dir.name.startswith("."):
                continue
            for dept_dir in org_dir.iterdir():
                if not dept_dir.is_dir():
                    continue
                candidate = dept_dir / agent_id / "agent.yml"
                if candidate.exists():
                    return candidate
        return None

    def _agent_dir(self, agent_id: str) -> Optional[Path]:
        """Return the agent's directory path."""
        yml = self._resolve_agent_yml(agent_id)
        if yml is None:
            return None
        return yml.parent

    def load_identity(self, agent_id: str) -> str:
        """Load the agent's identity.md file."""
        d = self._agent_dir(agent_id)
        if d is None:
            return ""
        return YAMLLoader.load_markdown(d / "identity.md")

    def load_instructions(self, agent_id: str) -> str:
        """Load the agent's instructions.md file."""
        d = self._agent_dir(agent_id)
        if d is None:
            return ""
        return YAMLLoader.load_markdown(d / "instructions.md")

    def load_memory(self, agent_id: str) -> str:
        """Load the agent's memory.md file."""
        d = self._agent_dir(agent_id)
        if d is None:
            return ""
        return YAMLLoader.load_markdown(d / "memory.md")

    def load_permissions(self, agent_id: str) -> str:
        """Load the agent's permissions.md file."""
        d = self._agent_dir(agent_id)
        if d is None:
            return ""
        return YAMLLoader.load_markdown(d / "permissions.md")

    def load_outputs(self, agent_id: str) -> str:
        """Load the agent's outputs.md file."""
        d = self._agent_dir(agent_id)
        if d is None:
            return ""
        return YAMLLoader.load_markdown(d / "outputs.md")

    def find_agents_by_capability(self, capability_id: str) -> List[AgentEntry]:
        """Return all agents that have a given capability."""
        results: List[AgentEntry] = []
        for agent in self.list_agents():
            if capability_id in agent.capabilities:
                results.append(agent)
        return results

    def find_agents_by_department(self, org: str, dept: str) -> List[AgentEntry]:
        """Return all agents in a given department."""
        return [
            a for a in self.list_agents()
            if a.org == org and a.department == dept
        ]

    def find_executives(self) -> List[AgentEntry]:
        """Return all executive-type agents."""
        return [a for a in self.list_agents() if a.type == "executive"]

    def get_all_agent_details(self) -> Dict[str, AgentDetail]:
        """Load all agent detail files and return as {id: detail}."""
        results: Dict[str, AgentDetail] = {}
        for agent in self.list_agents():
            detail = self.load_detail(agent.id)
            if detail is not None:
                results[agent.id] = detail
        return results