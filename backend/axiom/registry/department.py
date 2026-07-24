"""Registry loader for departments."""

from pathlib import Path
from typing import List, Optional

from axiom.config import departments_path
from axiom.models.configs import (
    DepartmentDetail,
    DepartmentEntry,
    DepartmentRegistry,
)
from axiom.registry.loader import YAMLLoader


class DepartmentRegistryLoader:
    """Loads department definitions from YAML and Markdown files."""

    def __init__(self) -> None:
        self._base = departments_path()

    def load_registry(self) -> DepartmentRegistry:
        """Load the master departments/departments.yaml cross-org index."""
        data = YAMLLoader.load_yaml(self._base / "departments.yaml")
        return DepartmentRegistry(**data)

    def list_departments(self, org_id: Optional[str] = None) -> List[DepartmentEntry]:
        """List all departments, optionally filtered by organization."""
        registry = self.load_registry()
        if org_id:
            return [d for d in registry.departments if d.org == org_id]
        return registry.departments

    def get_department(self, org_id: str, dept_id: str) -> Optional[DepartmentEntry]:
        """Find a single department by org + id."""
        for dept in self.list_departments(org_id):
            if dept.id == dept_id:
                return dept
        return None

    def load_detail(self, org_id: str, dept_id: str) -> Optional[DepartmentDetail]:
        """Load the detailed departments/<org>/<dept>/department.yaml."""
        path = self._base / org_id / dept_id / "department.yaml"
        if not path.exists():
            return None
        data = YAMLLoader.load_yaml(path)
        return DepartmentDetail(**data)

    def _dept_path(self, org_id: str, dept_id: str) -> Path:
        return self._base / org_id / dept_id

    def load_mission(self, org_id: str, dept_id: str) -> str:
        """Load the department mission.md file."""
        return YAMLLoader.load_markdown(self._dept_path(org_id, dept_id) / "mission.md")

    def load_processes(self, org_id: str, dept_id: str) -> str:
        """Load the department processes.md file."""
        return YAMLLoader.load_markdown(self._dept_path(org_id, dept_id) / "processes.md")

    def load_playbook(self, org_id: str, dept_id: str) -> str:
        """Load the department playbook.md file."""
        return YAMLLoader.load_markdown(self._dept_path(org_id, dept_id) / "playbook.md")

    def load_metrics(self, org_id: str, dept_id: str) -> str:
        """Load the department metrics.md file."""
        return YAMLLoader.load_markdown(self._dept_path(org_id, dept_id) / "metrics.md")