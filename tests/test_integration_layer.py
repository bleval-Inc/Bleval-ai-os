"""Tests for the Unified Integration Layer."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from axiom.integrations.layer import (
    IntegrationLayer,
    IntegrationConfig,
    IntegrationState,
    ConnectionConfig,
    AuthConfig,
    FetchConfig,
    ValidationConfig,
    NormalizationConfig,
    DeduplicationConfig,
    CacheConfig,
    PersistenceConfig,
    MonitoringConfig,
)


class TestIntegrationConfig:
    """Test integration configuration models."""

    def test_basic_config_creation(self):
        """Test creating a basic integration config."""
        config = IntegrationConfig(
            integration_id="test-slack",
            name="Test Slack",
            provider_id="slack",
            org_id="bleval",
        )
        assert config.integration_id == "test-slack"
        assert config.name == "Test Slack"
        assert config.provider_id == "slack"
        assert config.org_id == "bleval"
        assert config.enabled is True

    def test_config_with_all_subconfigs(self):
        """Test config with all sub-configurations."""
        config = IntegrationConfig(
            integration_id="test-full",
            name="Full Config Test",
            provider_id="github",
            org_id="bleval",
            connection=ConnectionConfig(
                protocol="https",
                base_url="https://api.github.com",
                timeout_seconds=30,
            ),
            auth=AuthConfig(
                strategy="bearer_token",
                credentials={"token_env_var": "GITHUB_TOKEN"},
            ),
            fetch=FetchConfig(
                page_size=100,
                max_pages=10,
            ),
            validation=ValidationConfig(
                mode="strict",
                required_fields=["id", "name"],
            ),
            normalization=NormalizationConfig(
                field_mapping={"html_url": "url"},
                standardize_timestamps=True,
            ),
            deduplication=DeduplicationConfig(
                strategy="composite_key",
                composite_fields=["repo", "id"],
            ),
            cache=CacheConfig(
                strategy="tiered",
                memory_max_size=1000,
            ),
            persistence=PersistenceConfig(
                targets=["domain_database"],
                table_name="test_table",
            ),
            monitoring=MonitoringConfig(
                enabled=True,
                health_check_interval_seconds=60,
            ),
        )
        assert config.connection.base_url == "https://api.github.com"
        assert config.auth.strategy == "bearer_token"
        assert config.validation.mode == "strict"
        assert config.deduplication.strategy == "composite_key"


class TestIntegrationLayer:
    """Test the IntegrationLayer class."""

    @pytest.fixture
    def mock_event_engine(self):
        """Create a mock event engine."""
        engine = AsyncMock()
        engine.publish = AsyncMock()
        engine.subscribe = AsyncMock()
        engine.start = AsyncMock()
        return engine

    @pytest.fixture
    def sample_config(self):
        """Create a sample integration config."""
        return IntegrationConfig(
            integration_id="test-integration",
            name="Test Integration",
            provider_id="test-provider",
            org_id="test-org",
            enabled=True,
            schedule=None,
        )

    @pytest.mark.asyncio
    async def test_layer_initialization(self, mock_event_engine):
        """Test layer initialization."""
        layer = IntegrationLayer(config_dir="/tmp/nonexistent", logger=MagicMock())
        await layer.initialize(event_engine=mock_event_engine)

        assert layer.event_publisher._initialized is True
        assert layer._event_subscriber is not None

        await layer.shutdown()

    @pytest.mark.asyncio
    async def test_execute_nonexistent_integration(self, mock_event_engine):
        """Test executing a non-existent integration."""
        layer = IntegrationLayer(config_dir="/tmp/nonexistent", logger=MagicMock())
        await layer.initialize(event_engine=mock_event_engine)

        result = await layer.execute_integration("nonexistent")

        assert result.success is False
        assert result.state == IntegrationState.ERROR
        assert "not found" in result.errors[0]

        await layer.shutdown()

    @pytest.mark.asyncio
    async def test_execute_disabled_integration(self, mock_event_engine, sample_config):
        """Test executing a disabled integration."""
        sample_config.enabled = False
        layer = IntegrationLayer(config_dir="/tmp/nonexistent", logger=MagicMock())
        layer._configs[sample_config.integration_id] = sample_config

        # Create a mock lifecycle
        from axiom.integrations.layer.lifecycle import IntegrationLifecycle
        mock_lifecycle = AsyncMock(spec=IntegrationLifecycle)
        mock_lifecycle.config = sample_config
        mock_lifecycle.execute_full_cycle = AsyncMock()

        layer._lifecycles[sample_config.integration_id] = mock_lifecycle

        await layer.initialize(event_engine=mock_event_engine)

        result = await layer.execute_integration(sample_config.integration_id)

        assert result.success is False
        assert result.state == IntegrationState.DISABLED
        assert "disabled" in result.errors[0]

        await layer.shutdown()

    def test_list_integrations(self, sample_config):
        """Test listing integrations."""
        layer = IntegrationLayer(config_dir="/tmp/nonexistent", logger=MagicMock())
        layer._configs[sample_config.integration_id] = sample_config

        integrations = layer.list_integrations()

        assert len(integrations) == 1
        assert integrations[0]["integration_id"] == sample_config.integration_id
        assert integrations[0]["name"] == sample_config.name

    def test_get_summary(self, sample_config):
        """Test getting layer summary."""
        layer = IntegrationLayer(config_dir="/tmp/nonexistent", logger=MagicMock())
        layer._configs[sample_config.integration_id] = sample_config

        # Add mock lifecycle with status
        from axiom.integrations.layer.models import IntegrationStatus
        from axiom.integrations.layer.lifecycle import IntegrationLifecycle

        mock_lifecycle = MagicMock(spec=IntegrationLifecycle)
        mock_lifecycle.config = sample_config
        mock_lifecycle.get_status = MagicMock(return_value=IntegrationStatus(
            integration_id=sample_config.integration_id,
            state=IntegrationState.DISCONNECTED,
            health_score=1.0,
        ))
        layer._lifecycles[sample_config.integration_id] = mock_lifecycle

        summary = layer.get_summary()

        assert summary["total_integrations"] == 1
        assert summary["enabled"] == 1
        assert summary["healthy"] == 1
        assert "cache_stats" in summary
        assert "monitor_summary" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])