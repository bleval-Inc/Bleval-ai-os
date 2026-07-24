"""Registry package — YAML configuration loaders.

Every registry loader reads configuration files from disk and returns typed
Pydantic models.  Loaders are independent of the runtime engines.
"""

from axiom.registry.loader import YAMLLoader

__all__ = ["YAMLLoader"]