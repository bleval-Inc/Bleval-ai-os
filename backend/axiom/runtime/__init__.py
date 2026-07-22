"""Runtime package — lifecycle management, scheduling, dispatching, monitoring.

The runtime is the execution layer that connects all engines together.
It manages the system lifecycle, schedules events, dispatches tasks,
monitors health, and handles recovery.
"""

from axiom.runtime.lifecycle import AxiomRuntime

__all__ = ["AxiomRuntime"]