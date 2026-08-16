"""Provider Registry — Load, manage, and provide access to providers."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from axiom.config import settings
from axiom.config import get_secrets_manager, SecretsManager
from axiom.engine.provider import Provider, ExternalAPIProvider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationRequest,
    ToolInvocationResult,
    CapabilityMapping,
)
from axiom.runtime.logging import RuntimeLogger


class ProviderRegistry:
    """Registry for loading and managing providers per organization.

    Loads provider definitions from YAML configs and instantiates
    provider implementations. Handles capability-to-provider-tool mapping.
    """

    def __init__(self, logger: Optional[RuntimeLogger] = None) -> None:
        self.logger = logger or RuntimeLogger()
        self._providers: Dict[str, Provider] = {}
        self._provider_configs: Dict[str, ProviderModel] = {}
        self._capability_mappings: Dict[str, List[CapabilityMapping]] = {}
        self._org_providers: Dict[str, Set[str]] = {}  # org_id -> provider_ids
        self._provider_implementations: Dict[str, type] = {}
        self._secrets = get_secrets_manager()
        self._initialized = False

    def register_implementation(self, provider_type: str, impl_class: type) -> None:
        """Register a provider implementation class."""
        self._provider_implementations[provider_type] = impl_class

    def load_provider_configs(self, org_id: str) -> List[ProviderModel]:
        """Load provider configurations for an organization."""
        if org_id in self._provider_configs:
            return list(self._provider_configs.values())

        org_path = Path(settings.registry_dir) / "organizations" / org_id / "tools"
        configs = []

        # Load from organization's tools.yaml (legacy tool interfaces)
        tools_file = org_path / "tools.yaml"
        if tools_file.exists():
            with open(tools_file) as f:
                data = yaml.safe_load(f) or {}
                for tool_data in data.get("tools", []):
                    # Each tool in tools.yaml can be a provider or reference one
                    # For now, we'll create a provider config from each
                    pass

        # Also load global provider configs from engine/providers/
        providers_dir = Path(settings.registry_dir).parent / "engine" / "providers"
        if providers_dir.exists():
            # Look for org-specific provider config
            org_provider_file = providers_dir / f"{org_id}.yaml"
            if org_provider_file.exists():
                with open(org_provider_file) as f:
                    data = yaml.safe_load(f) or {}
                    for provider_data in data.get("providers", []):
                        config = ProviderModel(**provider_data)
                        self._provider_configs[config.id] = config
                        configs.append(config)

        return configs

    async def initialize_providers(self, org_id: str) -> List[Provider]:
        """Initialize all providers for an organization."""
        configs = self.load_provider_configs(org_id)
        providers = []

        for config in configs:
            if not config.enabled:
                continue

            provider = await self._create_provider(config)
            if provider:
                await provider.initialize()
                self._providers[config.id] = provider
                self._org_providers.setdefault(org_id, set()).add(config.id)
                # Register capability mappings
                for capability in config.capabilities:
                    self._capability_mappings.setdefault(capability, []).append(
                        CapabilityMapping(
                            capability=capability,
                            provider_id=config.id,
                            tool_id=capability,  # Default: capability name = tool_id
                            priority=0,
                            org_ids=[org_id],
                        )
                    )
                providers.append(provider)

        self._initialized = True
        return providers

    async def _create_provider(self, config: ProviderModel) -> Optional[Provider]:
        """Create a provider instance from config."""
        # Try to find registered implementation
        impl_class = self._provider_implementations.get(config.id)

        # Fallback: try to infer from type
        if impl_class is None:
            type_to_impl = {
                "development": "GitHubProvider",  # Will register explicitly
                "business": "EmailProvider",
                "trading": "TradingViewProvider",
                "personal": "PersonalCalendarProvider",
            }
            impl_name = type_to_impl.get(config.type.value)
            if impl_name:
                impl_class = self._provider_implementations.get(impl_name)

        # Default to ExternalAPIProvider for HTTP-based providers
        if impl_class is None and config.base_url:
            impl_class = ExternalAPIProvider

        if impl_class is None:
            self.logger.warning(f"No implementation for provider {config.id}, skipping")
            return None

        try:
            # Instantiate with config
            provider = impl_class(config, self.logger)
            return provider
        except Exception as e:
            self.logger.error(f"Failed to create provider {config.id}: {e}")
            return None

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get a provider by ID."""
        return self._providers.get(provider_id)

    def get_providers_for_org(self, org_id: str) -> List[Provider]:
        """Get all providers for an organization."""
        provider_ids = self._org_providers.get(org_id, set())
        return [self._providers[pid] for pid in provider_ids if pid in self._providers]

    def get_tool(self, provider_id: str, tool_id: str) -> Optional[ProviderToolDefinition]:
        """Get a tool definition from a provider."""
        provider = self._providers.get(provider_id)
        if provider:
            return provider.get_tool(tool_id)
        return None

    def find_providers_for_capability(
        self, capability: str, org_id: Optional[str] = None
    ) -> List[Provider]:
        """Find providers that offer a capability."""
        mappings = self._capability_mappings.get(capability, [])
        if org_id:
            mappings = [m for m in mappings if not m.org_ids or org_id in m.org_ids]

        # Sort by priority
        mappings.sort(key=lambda m: -m.priority)

        providers = []
        for mapping in mappings:
            provider = self.get_provider(mapping.provider_id)
            if provider:
                providers.append(provider)
        return providers

    async def execute_tool(
        self,
        request: ToolInvocationRequest,
    ) -> ToolInvocationResult:
        """Execute a tool via the appropriate provider.

        This is the main entry point for tool execution.
        It finds the provider, checks permissions, and executes.
        """
        # Find provider for this tool
        provider = None
        for p in self._providers.values():
            if p.get_tool(request.tool_id):
                provider = p
                break

        if not provider:
            return ToolInvocationResult(
                success=False,
                error=f"No provider found for tool {request.tool_id}",
                error_code="no_provider",
                provider_id="unknown",
                tool_id=request.tool_id,
            )

        # Execute via provider (handles rate limit, circuit breaker, retries, audit)
        return await provider.execute_tool(request)

    async def health_check_all(self) -> Dict[str, ProviderHealth]:
        """Run health checks on all providers."""
        results = {}
        for pid, provider in self._providers.items():
            try:
                results[pid] = await provider.health_check()
            except Exception as e:
                results[pid] = ProviderHealth(
                    provider_id=pid,
                    status=ProviderStatus.UNHEALTHY,
                    error_message=str(e),
                )
        return results

    def get_provider_health(self, provider_id: str) -> Optional[ProviderHealth]:
        """Get cached health for a provider."""
        provider = self._providers.get(provider_id)
        if provider:
            return provider.health
        return None

    def list_tools(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools, optionally filtered by org."""
        tools = []
        provider_ids = set()
        if org_id:
            provider_ids = self._org_providers.get(org_id, set())
        else:
            provider_ids = set(self._providers.keys())

        for pid in provider_ids:
            provider = self._providers.get(pid)
            if provider:
                for tool in provider._tools.values():
                    tools.append(
                        {
                            "provider_id": pid,
                            "tool_id": tool.tool_id,
                            "name": tool.name,
                            "description": tool.description,
                            "capability": tool.capability,
                            "requires_approval": tool.requires_approval,
                            "risk_level": tool.risk_level,
                            "enabled": tool.enabled,
                        }
                    )
        return tools

    def get_capability_mappings(self) -> Dict[str, List[CapabilityMapping]]:
        """Get all capability mappings."""
        return self._capability_mappings.copy()

    def list_providers(self) -> Dict[str, Provider]:
        """List all registered providers."""
        return self._providers.copy()

    def has_provider(self, provider_id: str) -> bool:
        """Check if a provider is registered."""
        return provider_id in self._providers

    async def shutdown_all(self) -> None:
        """Shutdown all providers."""
        for provider in self._providers.values():
            try:
                await provider.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down provider {provider.provider_id}: {e}")
        self._providers.clear()
        self._initialized = False


# Global registry instance
_provider_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ProviderRegistry()
    return _provider_registry