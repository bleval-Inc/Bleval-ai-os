"""Registry loader for workflows."""

from typing import Dict, List, Optional

from axiom.config import workflows_path
from axiom.models.configs import (
    WorkflowDetail,
    WorkflowEntry,
    WorkflowIndex,
)
from axiom.registry.loader import YAMLLoader


class WorkflowRegistryLoader:
    """Loads workflow definitions from workflow-index.yaml and detail files."""

    def __init__(self) -> None:
        self._base = workflows_path()

    def load_index(self) -> WorkflowIndex:
        """Load the master workflows/workflow-index.yaml."""
        data = YAMLLoader.load_yaml(self._base / "workflow-index.yaml")
        return WorkflowIndex(**data)

    def list_workflows(self) -> Dict[str, WorkflowEntry]:
        """Return all registered workflows as {id: entry}."""
        return self.load_index().workflows

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowEntry]:
        """Get a single workflow entry from the index by id."""
        return self.list_workflows().get(workflow_id)

    def load_detail(self, workflow_id: str) -> Optional[WorkflowDetail]:
        """Load the detailed workflow yaml from workflows/<dept>/<name>.yaml.

        The workflow_id format is "<department>/<name>", e.g. "sales/prospect-research".
        """
        path = self._base / f"{workflow_id}.yaml"
        if not path.exists():
            return None
        data = YAMLLoader.load_yaml(path)
        # Convert step ids from int to str for consistency
        steps = data.get("steps", [])
        for step in steps:
            if "id" in step:
                step["id"] = str(step["id"])
        return WorkflowDetail(**data)

    def find_by_department(self, org: str, dept: str) -> List[WorkflowEntry]:
        """Return all workflows in a given department."""
        return [
            wf for wf_id, wf in self.list_workflows().items()
            if wf.org == org and wf.department == dept
        ]

    def find_by_trigger_event(self, event_type: str) -> List[str]:
        """Return workflow IDs that are triggered by a given event."""
        return [
            wf_id for wf_id, wf in self.list_workflows().items()
            if wf.trigger_event == event_type
        ]

    def find_by_agent(self, agent_id: str) -> List[str]:
        """Return workflow IDs that involve a given agent."""
        return [
            wf_id for wf_id, wf in self.list_workflows().items()
            if agent_id in wf.agents
        ]

    def get_workflow_ids(self) -> List[str]:
        """Return all registered workflow IDs."""
        return list(self.list_workflows().keys())