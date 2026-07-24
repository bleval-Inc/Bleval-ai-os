"""Centralized path resolver and environment configuration.

Provides the repo root, all YAML locations by category, the runtime state
directory, and environment variable lookups. Every module in the system
imports from here rather than hardcoding paths.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

# ── Root path resolution ────────────────────────────────────────────────
# backend/axiom/config.py  ->  repo root
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent


# ── Environment settings ────────────────────────────────────────────────
class AxiomSettings:
    """Loads settings from environment variables with sensible defaults."""

    def __init__(self) -> None:
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

        self.state_dir: Path = Path(
            os.getenv("AXIOM_STATE_DIR", str(REPO_ROOT / "backend" / "runtime" / "state"))
        )
        self.event_log_dir: Path = Path(
            os.getenv("AXIOM_EVENT_LOG_DIR", str(REPO_ROOT / "backend" / "runtime" / "events"))
        )
        self.log_dir: Path = Path(
            os.getenv("AXIOM_LOG_DIR", str(REPO_ROOT / "backend" / "runtime" / "logs"))
        )

    def ensure_dirs(self) -> None:
        """Create runtime directories if they do not exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.event_log_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


settings = AxiomSettings()


# ── Path helpers ─────────────────────────────────────────────────────────

def organizations_path() -> Path:
    return REPO_ROOT / "organizations"


def agents_path() -> Path:
    return REPO_ROOT / "agents"


def workflows_path() -> Path:
    return REPO_ROOT / "workflows"


def events_path() -> Path:
    return REPO_ROOT / "events"


def capabilities_path() -> Path:
    return REPO_ROOT / "capabilities"


def memory_path() -> Path:
    return REPO_ROOT / "memory"


def departments_path() -> Path:
    return REPO_ROOT / "departments"


def executives_path() -> Path:
    return REPO_ROOT / "core"


def core_path() -> Path:
    return REPO_ROOT / "core"


def all_config_paths() -> List[Path]:
    """Return every YAML/MD config directory for bulk loading."""
    return [
        organizations_path(),
        agents_path(),
        workflows_path(),
        events_path(),
        capabilities_path(),
        memory_path(),
        departments_path(),
        executives_path(),
        core_path(),
    ]