"""Memory Engine — layered memory retrieval and persistence.

Architecture: Global -> Organization -> Department -> Agent
Knowledge flows downward.  Learning flows upward.

This implementation is file-based.  Every layer resolves to Markdown files
on disk.  The MemoryEngine provides a unified interface for reading and
writing across all layers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from axiom.config import memory_path as get_memory_root
from axiom.models.configs import MemoryIndex, MemoryLayer
from axiom.registry.loader import YAMLLoader


class MemoryEngine:
    """Unified interface for layered memory."""

    def __init__(self) -> None:
        self._base = get_memory_root()
        self._index: Optional[MemoryIndex] = None

    @property
    def index(self) -> MemoryIndex:
        if self._index is None:
            self._index = self._load_index()
        return self._index

    def _load_index(self) -> MemoryIndex:
        path = self._base / "memory-index.yaml"
        data = YAMLLoader.load_yaml(path)
        return MemoryIndex(**data)

    def get_layer(self, layer_name: str) -> Optional[MemoryLayer]:
        """Get a memory layer definition by name."""
        return self.index.layers.get(layer_name)

    # ── Layer readers ────────────────────────────────────────────────────

    def load_global_memory(self) -> Dict[str, str]:
        """Load all global memory files.  Returns {filename: content}."""
        layer = self.get_layer("global")
        if layer is None or layer.files is None:
            return {}
        return self._read_files(self._base, layer.files)

    def load_org_memory(self, org_id: str) -> Dict[str, str]:
        """Load all organization-level memory files for a given org."""
        layer = self.get_layer("organization")
        if layer is None or layer.locations is None:
            return {}
        org_path_str = layer.locations.get(org_id)
        if org_path_str is None:
            return {}
        org_path = self._base / org_path_str
        return self._read_all_markdown(org_path)

    def load_department_memory(self, org_id: str, dept_id: str) -> Dict[str, str]:
        """Load department-level memory files.

        Convention: department memory is stored under
        memory/<org>-departments/<dept>/.
        """
        layer = self.get_layer("department")
        if layer is None or layer.locations is None:
            return {}
        base_path_str = layer.locations.get(org_id)
        if base_path_str is None:
            return {}
        dept_path = self._base / base_path_str / dept_id
        return self._read_all_markdown(dept_path)

    def load_agent_memory(self, agent_id: str) -> Dict[str, str]:
        """Load agent-level memory files.

        Convention: agent memory is stored under
        memory/agents/<agent_name>/.
        """
        # Derive the path from the agent's own identity files
        from axiom.config import REPO_ROOT
        agent_memory_dir = REPO_ROOT / "memory" / "agents" / agent_id
        return self._read_all_markdown(agent_memory_dir)

    # ── Resolved context (the main retrieval API) ────────────────────────

    def get_resolved_context(
        self,
        agent_id: str,
        org_id: str = "",
        dept_id: str = "",
    ) -> Dict[str, str]:
        """Resolve memory context for an agent by merging layers.

        Priority order (highest wins):  agent -> department -> organization -> global
        """
        merged: Dict[str, str] = {}

        # Start with global (lowest priority)
        merged.update(self.load_global_memory())

        # Overlay organization memory
        if org_id:
            merged.update(self.load_org_memory(org_id))

        # Overlay department memory
        if org_id and dept_id:
            merged.update(self.load_department_memory(org_id, dept_id))

        # Overlay agent memory (highest priority)
        merged.update(self.load_agent_memory(agent_id))

        return merged

    def get_context_string(
        self,
        agent_id: str,
        org_id: str = "",
        dept_id: str = "",
        separator: str = "\n\n---\n\n",
    ) -> str:
        """Resolve memory context as a single formatted string, useful for
        building prompts."""
        mem = self.get_resolved_context(agent_id, org_id, dept_id)
        parts = []
        for filename, content in mem.items():
            if content.strip():
                parts.append(f"# {filename}\n{content.strip()}")
        return separator.join(parts)

    # ── Writers (learning flows upward) ──────────────────────────────────

    def write_agent_memory(self, agent_id: str, key: str, content: str) -> Path:
        """Write a memory entry at the agent layer.

        Learning flows upward: agents write at the agent layer, which may be
        promoted to the department layer during review.
        """
        from axiom.config import REPO_ROOT
        agent_dir = REPO_ROOT / "memory" / "agents" / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        path = agent_dir / f"{key}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_department_memory(self, org_id: str, dept_id: str, key: str, content: str) -> Path:
        """Write a memory entry at the department layer.

        Departments write organizational learnings upward.
        """
        dept_dir = self._base / f"{org_id}-departments" / dept_id
        dept_dir.mkdir(parents=True, exist_ok=True)
        path = dept_dir / f"{key}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    # ── Helpers ──────────────────────────────────────────────────────────

    def _read_files(self, base: Path, filenames: List[str]) -> Dict[str, str]:
        """Read specific files from a directory."""
        result: Dict[str, str] = {}
        for name in filenames:
            path = base / name
            content = YAMLLoader.load_markdown(path)
            if content:
                result[name] = content
        return result

    def _read_all_markdown(self, directory: Path) -> Dict[str, str]:
        """Read all Markdown files in a directory as {filename: content}."""
        result: Dict[str, str] = {}
        if not directory.exists() or not directory.is_dir():
            return result
        for path in sorted(directory.glob("*.md")):
            content = YAMLLoader.load_markdown(path)
            if content:
                result[path.stem] = content
        return result