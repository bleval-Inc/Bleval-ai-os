"""Recovery model entities — re-exported from AXIOM Core for backward compatibility.

All recovery models are now canonical in axiom.core.self_healer.
This module provides backward-compatible imports for existing code.
"""

from axiom.core.self_healer import (  # noqa: F401
    RecoveryAction,
    RecoveryResult,
    RecoveryEvent,
)