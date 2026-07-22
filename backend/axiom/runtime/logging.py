"""Structured logging for the runtime.

Provides a simple structured logging interface that writes timestamped
entries to the runtime log directory.  Designed to be swappable with
a full logging framework in production.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from axiom.config import settings


class RuntimeLogger:
    """Structured logger for runtime events."""

    def __init__(self) -> None:
        self._log_dir = settings.log_dir

    def info(self, component: str, message: str, **kwargs: Any) -> None:
        """Log an informational message."""
        self._log("INFO", component, message, **kwargs)

    def warning(self, component: str, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log("WARNING", component, message, **kwargs)

    def error(self, component: str, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log("ERROR", component, message, **kwargs)

    def debug(self, component: str, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log("DEBUG", component, message, **kwargs)

    def workflow_event(self, instance_id: str, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a workflow lifecycle event."""
        self.info(
            "workflow",
            f"Workflow {instance_id}: {event}",
            instance_id=instance_id,
            workflow_event=event,
            **(details or {}),
        )

    def agent_action(self, agent_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an agent action."""
        self.info(
            "agent",
            f"Agent {agent_id}: {action}",
            agent_id=agent_id,
            action=action,
            **(details or {}),
        )

    def get_logs(
        self,
        component: Optional[str] = None,
        limit: int = 100,
        level: Optional[str] = None,
    ) -> str:
        """Read recent log entries as a formatted string."""
        log_file = self._log_dir / "runtime.log"
        if not log_file.exists():
            return ""

        lines = []
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if component and entry.get("component") != component:
                        continue
                    if level and entry.get("level") != level:
                        continue
                    lines.append(entry)
                except (json.JSONDecodeError, Exception):
                    continue

        # Return most recent entries
        lines = lines[-limit:]
        return "\n".join(
            f"[{e.get('timestamp', '')}] {e.get('level', 'INFO')} {e.get('component', '')}: {e.get('message', '')}"
            for e in lines
        )

    def _log(self, level: str, component: str, message: str, **kwargs: Any) -> None:
        """Write a structured log entry as JSON."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "component": component,
            "message": message,
            **kwargs,
        }

        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self._log_dir / "runtime.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")