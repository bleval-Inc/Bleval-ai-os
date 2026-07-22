"""Core YAML loading utility used by all registry loaders."""

from pathlib import Path
from typing import Any, Dict, List

import yaml


class YAMLLoader:
    """Static methods for loading YAML and Markdown configuration files."""

    @staticmethod
    def load_yaml(path: Path) -> dict:
        """Load a single YAML file and return as a dict.

        Raises FileNotFoundError if the path does not exist.
        Raises yaml.YAMLError if the file is malformed.
        """
        if not path.exists():
            raise FileNotFoundError(f"YAML file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        return data

    @staticmethod
    def load_yamls(pattern: str, base: Path) -> Dict[str, dict]:
        """Load multiple YAML files matching a glob pattern.

        Returns a dict mapping filename stem -> parsed content.
        """
        results: Dict[str, dict] = {}
        for path in sorted(base.glob(pattern)):
            if path.is_file() and path.suffix in (".yaml", ".yml"):
                try:
                    data = YAMLLoader.load_yaml(path)
                    results[path.stem] = data
                except (FileNotFoundError, yaml.YAMLError) as e:
                    raise RuntimeError(f"Failed to load {path}: {e}")
        return results

    @staticmethod
    def load_markdown(path: Path) -> str:
        """Read a Markdown file as raw text.

        Returns empty string if the file does not exist.
        """
        if not path.exists():
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def resolve_agent_path(agent_id: str) -> Path:
        """Search the agents directory for a given agent_id.

        Searches agents/<org>/<department>/<agent_id>/agent.yml
        and agents/<agent_id>.yml (top-level executives).
        Returns the path if found, raises FileNotFoundError otherwise.
        """
        from axiom.config import agents_path

        base = agents_path()
        # Check top-level (executive agents)
        top = base / f"{agent_id}.yml"
        if top.exists():
            return top

        # Search nested specialist agents
        for org_dir in base.iterdir():
            if not org_dir.is_dir() or org_dir.name.startswith("."):
                continue
            for dept_dir in org_dir.iterdir():
                if not dept_dir.is_dir():
                    continue
                agent_dir = dept_dir / agent_id
                candidate = agent_dir / "agent.yml"
                if candidate.exists():
                    return candidate

        raise FileNotFoundError(f"Agent not found for id: {agent_id}")

    @staticmethod
    def find_agent_detail_dirs() -> List[Path]:
        """Return a list of all agent detail directories.

        Each item is an agents/<org>/<dept>/<agent>/ directory.
        """
        from axiom.config import agents_path

        dirs: List[Path] = []
        base = agents_path()
        for org_dir in base.iterdir():
            if not org_dir.is_dir() or org_dir.name.startswith("."):
                continue
            for dept_dir in org_dir.iterdir():
                if not dept_dir.is_dir():
                    continue
                for agent_dir in dept_dir.iterdir():
                    candidate = agent_dir / "agent.yml"
                    if candidate.exists():
                        dirs.append(agent_dir)
        return dirs