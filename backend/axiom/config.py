"""Centralized path resolver and environment configuration.

Provides the repo root, all YAML locations by category, the runtime state
directory, and environment variable lookups. Every module in the system
imports from here rather than hardcoding paths.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self.secrets_dir: Optional[str] = os.getenv("AXIOM_SECRETS_DIR")

        # Production mode: only real providers allowed
        self.real_providers_only: bool = os.getenv("REAL_PROVIDERS_ONLY", "false").lower() in ("true", "1", "yes")

        # Debug mode
        self.debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

        # Environment
        self.env: str = os.getenv("AXIOM_ENV", "development")

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


# ── Secrets Management ───────────────────────────────────────────────────

class SecretNotFoundError(Exception):
    """Raised when a required secret is not found."""

    pass


class SecretsManager:
    """Manages secure secret loading for providers.

    Sources (in priority order):
    1. Environment variables (highest)
    2. .env file (via settings)
    3. Secret files (for container deployments)
    4. External vault (future: HashiCorp Vault, AWS Secrets Manager)
    """

    def __init__(self) -> None:
        self._cache: Dict[str, str] = {}
        self._secret_files_dir = getattr(settings, "secrets_dir", None)
        if self._secret_files_dir:
            self._secret_files_dir = Path(self._secret_files_dir)

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value.

        Args:
            key: Secret key (e.g., "GITHUB_TOKEN", "OPENAI_API_KEY")
            default: Default value if not found

        Returns:
            Secret value or default/None
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # 1. Environment variable (highest priority)
        value = os.getenv(key)

        # 2. Check settings (loads from .env)
        if value is None:
            value = getattr(settings, key.lower(), None)

        # 3. Secret file (Docker secrets, K8s secrets)
        if value is None and self._secret_files_dir:
            secret_file = self._secret_files_dir / key.lower()
            if secret_file.exists():
                try:
                    value = secret_file.read_text().strip()
                except Exception:
                    pass

        # Cache and return
        if value is not None:
            self._cache[key] = value
            return value

        return default

    def require_secret(self, key: str) -> str:
        """Get a required secret, raise if not found."""
        value = self.get_secret(key)
        if value is None:
            raise SecretNotFoundError(
                f"Required secret '{key}' not found in environment, .env, or secret files"
            )
        return value

    def get_provider_auth(
        self,
        token_env_var: Optional[str] = None,
        username_env_var: Optional[str] = None,
        password_env_var: Optional[str] = None,
        client_id_env_var: Optional[str] = None,
        client_secret_env_var: Optional[str] = None,
        cookie_env_var: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        """Extract auth credentials for a provider."""
        return {
            "token": self.get_secret(token_env_var) if token_env_var else None,
            "username": self.get_secret(username_env_var) if username_env_var else None,
            "password": self.get_secret(password_env_var) if password_env_var else None,
            "client_id": self.get_secret(client_id_env_var) if client_id_env_var else None,
            "client_secret": self.get_secret(client_secret_env_var) if client_secret_env_var else None,
            "cookie": self.get_secret(cookie_env_var) if cookie_env_var else None,
        }

    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from data before logging."""
        sanitized = {}
        sensitive_keys = {
            "token",
            "password",
            "secret",
            "key",
            "api_key",
            "access_token",
            "refresh_token",
            "client_secret",
            "authorization",
            "cookie",
        }

        for k, v in data.items():
            k_lower = k.lower()
            if any(s in k_lower for s in sensitive_keys):
                sanitized[k] = "***REDACTED***"
            elif isinstance(v, dict):
                sanitized[k] = self.sanitize_for_logging(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    self.sanitize_for_logging(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                sanitized[k] = v
        return sanitized

    def clear_cache(self) -> None:
        """Clear the secret cache (useful for rotation)."""
        self._cache.clear()


# Global instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager