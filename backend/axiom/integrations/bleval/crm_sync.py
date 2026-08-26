"""CRM Sync Provider — Synchronizes with external CRM systems."""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import (
    Lead,
    Contact,
    Account,
    Opportunity,
    LeadStatus,
    LeadSource,
    DealStage,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class CRMSyncConfig(BaseModel):
    """CRM sync configuration."""

    provider: str  # hubspot, salesforce, pipedrive, close, custom
    enabled: bool = True
    api_key: Optional[SecretStr] = None
    api_secret: Optional[SecretStr] = None
    base_url: str
    webhook_secret: Optional[SecretStr] = None

    # Sync settings
    sync_interval_minutes: int = 15
    batch_size: int = 100
    conflict_resolution: str = "remote_wins"  # local_wins, remote_wins, merge, manual

    # Field mappings
    field_mappings: Dict[str, str] = Field(default_factory=dict)

    # Filters
    sync_leads: bool = True
    sync_contacts: bool = True
    sync_accounts: bool = True
    sync_opportunities: bool = True
    sync_activities: bool = True

    # Custom
    custom_params: Dict[str, Any] = Field(default_factory=dict)


class SyncResult(BaseModel):
    """Result of a sync operation."""

    entity_type: str
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class CRMProviderBase(ABC):
    """Abstract CRM provider."""

    def __init__(self, config: CRMSyncConfig, logger: Optional[RuntimeLogger] = None):
        self.config = config
        self.logger = logger or RuntimeLogger()

    @abstractmethod
    async def fetch_leads(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_accounts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch_opportunities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def push_contact(self, contact: Contact) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def push_opportunity(self, opp: Opportunity) -> Dict[str, Any]:
        pass


class HubSpotProvider(CRMProviderBase):
    """HubSpot CRM provider."""

    async def fetch_leads(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        # Simplified - would use HubSpot API
        return []

    async def fetch_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_accounts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_opportunities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        return {"id": "hubspot_" + lead.uuid}

    async def push_contact(self, contact: Contact) -> Dict[str, Any]:
        return {"id": "hubspot_" + str(contact.id)}

    async def push_opportunity(self, opp: Opportunity) -> Dict[str, Any]:
        return {"id": "hubspot_" + str(opp.id)}


class SalesforceProvider(CRMProviderBase):
    """Salesforce CRM provider."""

    async def fetch_leads(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_accounts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_opportunities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        return {"id": "sf_" + lead.uuid}

    async def push_contact(self, contact: Contact) -> Dict[str, Any]:
        return {"id": "sf_" + str(contact.id)}

    async def push_opportunity(self, opp: Opportunity) -> Dict[str, Any]:
        return {"id": "sf_" + str(opp.id)}


class PipedriveProvider(CRMProviderBase):
    """Pipedrive CRM provider."""

    async def fetch_leads(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_accounts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_opportunities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        return {"id": "pd_" + lead.uuid}

    async def push_contact(self, contact: Contact) -> Dict[str, Any]:
        return {"id": "pd_" + str(contact.id)}

    async def push_opportunity(self, opp: Opportunity) -> Dict[str, Any]:
        return {"id": "pd_" + str(opp.id)}


class CustomRESTProvider(CRMProviderBase):
    """Custom REST API CRM provider."""

    async def fetch_leads(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_contacts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_accounts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def fetch_opportunities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return []

    async def push_lead(self, lead: Lead) -> Dict[str, Any]:
        return {"id": "custom_" + lead.uuid}

    async def push_contact(self, contact: Contact) -> Dict[str, Any]:
        return {"id": "custom_" + str(contact.id)}

    async def push_opportunity(self, opp: Opportunity) -> Dict[str, Any]:
        return {"id": "custom_" + str(opp.id)}


class CRMSyncProvider:
    """CRM synchronization orchestrator."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: CRMSyncConfig,
        repository,  # BlevalRepository
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        # Initialize provider
        self.provider = self._create_provider(config)

        # State
        self._last_sync: Dict[str, datetime] = {}
        self._sync_hashes: Dict[str, str] = {}

    def _create_provider(self, config: CRMSyncConfig) -> CRMProviderBase:
        provider_map = {
            "hubspot": HubSpotProvider,
            "salesforce": SalesforceProvider,
            "pipedrive": PipedriveProvider,
            "custom": CustomRESTProvider,
        }
        provider_class = provider_map.get(config.provider.lower(), CustomRESTProvider)
        return provider_class(config, self.logger)

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash for change detection."""
        return hashlib.md5(str(sorted(data.items())).encode()).hexdigest()

    async def sync_leads(self, since: Optional[datetime] = None) -> SyncResult:
        """Sync leads from CRM."""
        start = datetime.utcnow()
        result = SyncResult(entity_type="leads")

        try:
            remote_leads = await self.provider.fetch_leads(since)
            self.logger.info(f"Fetched {len(remote_leads)} leads from {self.config.provider}")

            for remote in remote_leads:
                try:
                    local = await self._map_and_upsert_lead(remote)
                    if local:
                        result.updated += 1
                    else:
                        result.created += 1
                except Exception as e:
                    result.errors.append(f"Lead {remote.get('id', 'unknown')}: {e}")

        except Exception as e:
            result.errors.append(f"Fetch failed: {e}")
            self.logger.error(f"Lead sync failed: {e}")

        result.duration_seconds = (datetime.utcnow() - start).total_seconds()
        return result

    async def _map_and_upsert_lead(self, remote: Dict[str, Any]) -> Optional[Lead]:
        """Map remote lead to local and upsert."""
        # Extract fields based on provider
        field_map = self.config.field_mappings or {
            "email": "email",
            "first_name": "first_name",
            "last_name": "last_name",
            "company": "company",
            "phone": "phone",
            "source": "source",
            "status": "status",
            "score": "score",
        }

        lead_data = {}
        for local_field, remote_field in field_map.items():
            if remote_field in remote:
                lead_data[local_field] = remote[remote_field]

        # Required fields
        if not lead_data.get("email"):
            return None

        # Check if exists
        existing = await self.repository.get_lead_by_email(lead_data["email"])
        lead_hash = self._compute_hash(lead_data)

        if existing:
            if self._sync_hashes.get(f"lead_{existing.id}") == lead_hash:
                return existing  # No change
            if self.config.conflict_resolution == "remote_wins":
                await self.repository.update_lead(existing.id, **lead_data)
                self._sync_hashes[f"lead_{existing.id}"] = lead_hash
                return existing
            elif self.config.conflict_resolution == "local_wins":
                return existing
            # merge would combine
        else:
            # Create new
            lead_data["source"] = LeadSource(lead_data.get("source", "CRM_SYNC"))
            lead_data["status"] = LeadStatus(lead_data.get("status", "NEW"))
            lead = await self.repository.create_lead(**lead_data)
            self._sync_hashes[f"lead_{lead.id}"] = lead_hash
            return lead

        return None

    async def sync_contacts(self, since: Optional[datetime] = None) -> SyncResult:
        """Sync contacts from CRM."""
        start = datetime.utcnow()
        result = SyncResult(entity_type="contacts")

        try:
            remote_contacts = await self.provider.fetch_contacts(since)

            for remote in remote_contacts:
                try:
                    # Similar mapping logic
                    pass
                except Exception as e:
                    result.errors.append(f"Contact {remote.get('id')}: {e}")

        except Exception as e:
            result.errors.append(str(e))

        result.duration_seconds = (datetime.utcnow() - start).total_seconds()
        return result

    async def sync_accounts(self, since: Optional[datetime] = None) -> SyncResult:
        """Sync accounts from CRM."""
        start = datetime.utcnow()
        result = SyncResult(entity_type="accounts")

        try:
            remote_accounts = await self.provider.fetch_accounts(since)

            for remote in remote_accounts:
                try:
                    domain = remote.get("domain") or remote.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
                    existing = await self.repository.get_account_by_domain(domain) if domain else None

                    account_data = {
                        "name": remote.get("name"),
                        "domain": domain,
                        "industry": remote.get("industry"),
                        "size": remote.get("size"),
                        "revenue": remote.get("revenue"),
                    }

                    if existing:
                        if self.config.conflict_resolution == "remote_wins":
                            await self.repository.update_account(existing.id, **account_data)
                            result.updated += 1
                    else:
                        await self.repository.create_account(**account_data)
                        result.created += 1
                except Exception as e:
                    result.errors.append(f"Account {remote.get('id')}: {e}")

        except Exception as e:
            result.errors.append(str(e))

        result.duration_seconds = (datetime.utcnow() - start).total_seconds()
        return result

    async def sync_opportunities(self, since: Optional[datetime] = None) -> SyncResult:
        """Sync opportunities from CRM."""
        start = datetime.utcnow()
        result = SyncResult(entity_type="opportunities")

        try:
            remote_opps = await self.provider.fetch_opportunities(since)

            for remote in remote_opps:
                try:
                    # Map to opportunity
                    pass
                except Exception as e:
                    result.errors.append(f"Opportunity {remote.get('id')}: {e}")

        except Exception as e:
            result.errors.append(str(e))

        result.duration_seconds = (datetime.utcnow() - start).total_seconds()
        return result

    async def push_local_changes(self) -> Dict[str, SyncResult]:
        """Push local changes to CRM."""
        results = {}

        # Push new/updated leads
        # Would query for leads with external_id = None or updated_at > last_push
        pass

        return results

    async def full_sync(self) -> Dict[str, SyncResult]:
        """Run full synchronization."""
        results = {}

        if self.config.sync_leads:
            results["leads"] = await self.sync_leads()

        if self.config.sync_contacts:
            results["contacts"] = await self.sync_contacts()

        if self.config.sync_accounts:
            results["accounts"] = await self.sync_accounts()

        if self.config.sync_opportunities:
            results["opportunities"] = await self.sync_opportunities()

        return results