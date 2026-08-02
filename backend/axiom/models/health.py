"""Health model entities — re-exported from AXIOM Core for backward compatibility.

All health models are now canonical in axiom.core.system_health.
This module provides backward-compatible imports for existing code.
"""

from axiom.core.system_health import (  # noqa: F401
    HealthState,
    ComponentHealth,
    SystemHealthSnapshot,
)