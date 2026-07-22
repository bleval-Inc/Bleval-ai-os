"""Registry loader for organisations."""

from pathlib import Path
from typing import List, Optional

from axiom.config import organizations_path
from axiom.models.configs import (
    OrganizationEntry,
    OrganizationRegistry,
    OrgDetail,
    ToolDef,
    ToolRegistry,
)
from axiom.registry.loader import YAMLLoader


class OrganizationRegistryLoader:
    """Loads organisation definitions from YAML files."""

    def __init__(self) -> None:
        self._base = organizations_path()

    def load_registry(self) -> OrganizationRegistry:
        """Load the master organisations/organisation.yaml registry."""
        data = YAMLLoader.load_yaml(self._base / "organization.yaml")
        return OrganizationRegistry(**data)

    def list_organizations(self) -> List[OrganizationEntry]:
        """Return all registered organisations."""
        registry = self.load_registry()
        return registry.organizations

    def get_organization(self, org_id: str) -> Optional[OrganizationEntry]:
        """Find a single organisation by id."""
        for org in self.list_organizations():
            if org.id == org_id:
                return org
        return None

    def load_org_detail(self, org_id: str) -> Optional[OrgDetail]:
        """Load the detailed organisation/<org_id>/organization.yaml definition."""
        path = self._base / org_id / "organization.yaml"
        if not path.exists():
            return None
        data = YAMLLoader.load_yaml(path)
        return OrgDetail(**data)

    def load_tools(self, org_id: str) -> Optional[ToolRegistry]:
        """Load organisations/<org_id>/tools/tools.yaml."""
        path = self._base / org_id / "tools" / "tools.yaml"
        if not path.exists():
            return None
        data = YAMLLoader.load_yaml(path)
        return ToolRegistry(**data)

    def load_identity(self, org_id: str) -> str:
        """Load the organisation/<org_id>/identity.md file."""
        path = self._base / org_id / "identity.md"
        return YAMLLoader.load_markdown(path)

    def load_permissions(self, org_id: str) -> str:
        """Load the organisation/<org_id>/permissions.md file."""
        path = self._base / org_id / "permissions.md"
        return YAMLLoader.load_markdown(path)