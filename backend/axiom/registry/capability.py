"""Registry loader for capabilities."""

from typing import Dict, List, Optional

from axiom.config import capabilities_path
from axiom.models.configs import (
    CapabilityCatalog,
    CapabilityCategory,
    CapabilityEntry,
)
from axiom.registry.loader import YAMLLoader


class CapabilityRegistryLoader:
    """Loads capability definitions from YAML files."""

    def __init__(self) -> None:
        self._base = capabilities_path()

    def load_catalog(self) -> CapabilityCatalog:
        """Load the master capabilities/capability-catalog.yaml."""
        data = YAMLLoader.load_yaml(self._base / "capability-catalog.yaml")
        return CapabilityCatalog(**data)

    def list_capabilities(self) -> List[CapabilityEntry]:
        """Return all known capabilities."""
        return self.load_catalog().capabilities

    def find_capability(self, cap_id: str) -> Optional[CapabilityEntry]:
        """Find a single capability by id."""
        for cap in self.list_capabilities():
            if cap.id == cap_id:
                return cap
        return None

    def find_by_agent(self, agent_id: str) -> List[CapabilityEntry]:
        """Return all capabilities possessed by a given agent."""
        return [c for c in self.list_capabilities() if agent_id in c.agents]

    def find_by_category(self, category: str) -> List[CapabilityEntry]:
        """Return all capabilities in a given category."""
        return [c for c in self.list_capabilities() if c.category == category]

    def find_by_workflow(self, workflow_id: str) -> List[CapabilityEntry]:
        """Return all capabilities used by a given workflow."""
        return [c for c in self.list_capabilities() if workflow_id in c.workflows]

    def resolve_agents_for_capability(self, cap_id: str) -> List[str]:
        """Return agent IDs that have a given capability."""
        cap = self.find_capability(cap_id)
        if cap is None:
            return []
        return cap.agents

    def load_search_index(self) -> Dict[str, List[str]]:
        """Load the capabilities/search-index.yaml keyword-to-capability mapping."""
        path = self._base / "search-index.yaml"
        if not path.exists():
            return {}
        data = YAMLLoader.load_yaml(path)
        return data.get("keywords", {})

    def search(self, query: str) -> List[CapabilityEntry]:
        """Search for capabilities by keyword.

        Tokenizes the query into individual words and matches each against
        the search index.  Also falls back to matching against capability
        names and descriptions.
        """
        search_index = self.load_search_index()
        query_lower = query.lower()
        matched_ids: set = set()

        # Tokenise query into individual search terms
        tokens = [t.strip() for t in query_lower.replace("-", " ").replace("_", " ").split() if t.strip()]

        # Direct keyword match — check if ANY token matches any keyword
        for keyword, cap_ids in search_index.items():
            keyword_lower = keyword.lower()
            matched = False
            # Check entire query as substring of keyword
            if query_lower in keyword_lower:
                matched = True
            # Check each token as substring of keyword
            for token in tokens:
                if token in keyword_lower:
                    matched = True
                    break
            if matched:
                matched_ids.update(cap_ids)

        # Partial description match — check each token against name/desc
        for cap in self.list_capabilities():
            name_lower = cap.name.lower()
            desc_lower = cap.description.lower()
            if any(token in name_lower or token in desc_lower for token in tokens):
                matched_ids.add(cap.id)

        return [c for c in self.list_capabilities() if c.id in matched_ids]

    def load_categories(self) -> List[CapabilityCategory]:
        """Load all category definitions from capabilities/categories/*.yaml."""
        categories: List[CapabilityCategory] = []
        cat_dir = self._base / "categories"
        if not cat_dir.exists():
            return categories
        for path in sorted(cat_dir.glob("*.yaml")):
            data = YAMLLoader.load_yaml(path)
            categories.append(CapabilityCategory(**data))
        return categories