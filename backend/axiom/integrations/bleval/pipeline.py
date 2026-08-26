"""BLEVAL Pipeline — Orchestrates lead acquisition, deal tracking, campaigns."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from axiom.data.models import (
    Lead,
    LeadStatus,
    LeadSource,
    Deal,
    DealStage,
    Campaign,
    CampaignStatus,
)
from axiom.data.repositories import BlevalRepository
from axiom.integrations.bleval import (
    CRMSyncProvider,
    CRMSyncConfig,
    LeadAcquisitionEngine,
    LeadAcquisitionConfig,
    DealTracker,
    DealTrackerConfig,
    CampaignManager,
    CampaignConfig,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class BlevalPipeline:
    """Complete BLEVAL acquisition pipeline."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        repository: BlevalRepository,
        crm_config: Optional[CRMSyncConfig] = None,
        lead_config: Optional[LeadAcquisitionConfig] = None,
        deal_config: Optional[DealTrackerConfig] = None,
        campaign_config: Optional[CampaignConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        # Initialize components
        self.crm_sync = CRMSyncProvider(
            integration_layer, crm_config or CRMSyncConfig(
                provider="custom", base_url="", enabled=False
            ), repository, self.logger
        )

        self.lead_engine = LeadAcquisitionEngine(
            integration_layer, repository, lead_config or LeadAcquisitionConfig(), self.logger
        )

        self.deal_tracker = DealTracker(
            integration_layer, repository, deal_config or DealTrackerConfig(), self.logger
        )

        self.campaign_manager = CampaignManager(
            integration_layer, repository, campaign_config or CampaignConfig(), self.logger
        )

        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Start the pipeline."""
        if self._running:
            return

        self._running = True
        self.logger.info("Starting BLEVAL Pipeline")

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._crm_sync_loop()),
            asyncio.create_task(self._followup_loop()),
            asyncio.create_task(self._pipeline_health_loop()),
        ]

    async def stop(self):
        """Stop the pipeline."""
        self._running = False
        self.logger.info("Stopping BLEVAL Pipeline")

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _crm_sync_loop(self):
        """Periodic CRM synchronization."""
        while self._running:
            try:
                if self.crm_sync.config.enabled:
                    await self.crm_sync.full_sync()
                await asyncio.sleep(self.crm_sync.config.sync_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"CRM sync loop error: {e}")
                await asyncio.sleep(300)

    async def _followup_loop(self):
        """Check for leads needing follow-up."""
        while self._running:
            try:
                leads = await self.lead_engine.get_leads_needing_followup()
                for lead in leads:
                    self.logger.info(f"Lead {lead.id} ({lead.email}) needs follow-up")
                    # Would trigger notification
                await asyncio.sleep(3600)  # Check hourly
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Followup loop error: {e}")
                await asyncio.sleep(300)

    async def _pipeline_health_loop(self):
        """Monitor pipeline health."""
        while self._running:
            try:
                health = await self.health_check()
                if health.get("stale_deals", 0) > 10:
                    self.logger.warning(f"High stale deals: {health['stale_deals']}")
                if health.get("slipped_deals", 0) > 5:
                    self.logger.warning(f"Slipped deals: {health['slipped_deals']}")
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Pipeline health error: {e}")
                await asyncio.sleep(300)

    # ──────────────────────────────────────────────────────────────────────────────
    # Lead Operations
    # ──────────────────────────────────────────────────────────────────────────────

    async def capture_lead(
        self,
        source: LeadSource,
        data: Dict[str, Any],
        **kwargs
    ) -> Lead:
        """Capture a new lead."""
        return await self.lead_engine.capture_lead(source, data, **kwargs)

    async def capture_web_form(self, form_data: Dict[str, Any], **kwargs) -> Lead:
        """Capture lead from web form."""
        return await self.capture_lead(LeadSource.WEB_FORM, form_data, **kwargs)

    async def capture_chat(self, chat_data: Dict[str, Any], **kwargs) -> Lead:
        """Capture lead from chat."""
        return await self.capture_lead(LeadSource.CHAT, chat_data, **kwargs)

    async def capture_email(self, email_data: Dict[str, Any], **kwargs) -> Lead:
        """Capture lead from email."""
        return await self.capture_lead(LeadSource.EMAIL, email_data, **kwargs)

    async def get_lead(self, lead_id: int) -> Optional[Lead]:
        return await self.repository.get_lead(lead_id)

    async def get_lead_by_email(self, email: str) -> Optional[Lead]:
        return await self.repository.get_lead_by_email(email)

    async def update_lead(self, lead_id: int, **kwargs) -> Optional[Lead]:
        return await self.repository.update_lead(lead_id, **kwargs)

    async def list_leads(self, **filters) -> List[Lead]:
        return await self.repository.list_leads(**filters)

    async def score_lead(self, lead_id: int):
        """Re-score a lead."""
        await self.lead_engine._score_lead(lead_id)

    async def enrich_lead(self, lead_id: int):
        """Enrich a lead."""
        await self.lead_engine._enrich_lead(lead_id)

    # ──────────────────────────────────────────────────────────────────────────────
    # Deal Operations
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_deal_from_opp(self, opportunity_id: int, won: bool = True) -> Optional[Deal]:
        return await self.deal_tracker.create_deal_from_opportunity(opportunity_id, won)

    async def update_deal_stage(
        self, deal_id: int, stage: DealStage, reason: Optional[str] = None
    ) -> Optional[Deal]:
        return await self.deal_tracker.update_deal_stage(deal_id, stage, reason)

    async def get_deal_forecast(self, deal_id: int):
        return await self.deal_tracker.get_deal_forecast(deal_id)

    async def get_pipeline_snapshot(self, owner_id: Optional[str] = None):
        return await self.deal_tracker.get_pipeline_snapshot(owner_id)

    async def get_stale_deals(self, owner_id: Optional[str] = None) -> List[Deal]:
        return await self.deal_tracker.get_stale_deals(owner_id)

    async def get_slipped_deals(self, owner_id: Optional[str] = None) -> List[Deal]:
        return await self.deal_tracker.get_slipped_deals(owner_id)

    async def get_high_value_deals(self, owner_id: Optional[str] = None):
        return await self.deal_tracker.get_high_value_deals(owner_id)

    async def calculate_velocity(self, owner_id: Optional[str] = None):
        return await self.deal_tracker.calculate_velocity(owner_id)

    # ──────────────────────────────────────────────────────────────────────────────
    # Campaign Operations
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_campaign(
        self, name: str, description: str, owner_id: str, **kwargs
    ) -> Campaign:
        return await self.campaign_manager.create_campaign(name, description, owner_id, **kwargs)

    async def launch_campaign(self, campaign_id: int) -> bool:
        return await self.campaign_manager.launch_campaign(campaign_id)

    async def pause_campaign(self, campaign_id: int) -> bool:
        return await self.campaign_manager.pause_campaign(campaign_id)

    async def enroll_lead_in_campaign(self, campaign_id: int, lead_id: int) -> bool:
        return await self.campaign_manager.enroll_lead(campaign_id, lead_id)

    async def get_campaign_metrics(self, campaign_id: int):
        return await self.campaign_manager.get_campaign_metrics(campaign_id)

    # ──────────────────────────────────────────────────────────────────────────────
    # CRM Sync
    # ──────────────────────────────────────────────────────────────────────────────

    async def sync_crm(self) -> Dict[str, Any]:
        return await self.crm_sync.full_sync()

    async def push_to_crm(self) -> Dict[str, Any]:
        return await self.crm_sync.push_local_changes()

    # ──────────────────────────────────────────────────────────────────────────────
    # Analytics & Health
    # ──────────────────────────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive pipeline health check."""
        leads = await self.repository.list_leads(limit=1000)
        deals = await self.repository.list_deals(limit=1000)
        campaigns = await self.repository.list_campaigns(limit=100)

        # Lead health
        new_leads = [l for l in leads if l.status == LeadStatus.NEW]
        stale_leads = [
            l for l in leads
            if l.status in [LeadStatus.NEW, LeadStatus.QUALIFIED]
            and l.next_follow_up_at
            and l.next_follow_up_at < datetime.utcnow()
        ]

        # Deal health
        stale_deals = await self.deal_tracker.get_stale_deals()
        slipped_deals = await self.deal_tracker.get_slipped_deals()
        high_value = await self.deal_tracker.get_high_value_deals()

        # Campaign health
        active_campaigns = [c for c in campaigns if c.status == CampaignStatus.ACTIVE]

        return {
            "timestamp": datetime.utcnow(),
            "leads": {
                "total": len(leads),
                "new": len(new_leads),
                "stale_needing_followup": len(stale_leads),
            },
            "deals": {
                "total": len(deals),
                "stale": len(stale_deals),
                "slipped": len(slipped_deals),
                "high_value": len(high_value),
            },
            "campaigns": {
                "total": len(campaigns),
                "active": len(active_campaigns),
            },
            "alerts": [],
        }

    async def get_dashboard_data(self, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Get dashboard data for UI."""
        pipeline = await self.get_pipeline_snapshot(owner_id)
        velocity = await self.calculate_velocity(owner_id)
        health = await self.health_check()

        # Recent activity
        leads = await self.list_leads(limit=10)
        deals = await self.repository.list_deals(owner_id=owner_id, limit=10)

        return {
            "pipeline": {
                "total": float(pipeline.total_pipeline),
                "weighted": float(pipeline.weighted_pipeline),
                "by_stage": pipeline.by_stage,
            },
            "velocity": velocity,
            "health": health,
            "recent_leads": [
                {"id": l.id, "email": l.email, "company": l.company, "score": l.score, "status": l.status.value}
                for l in leads
            ],
            "recent_deals": [
                {"id": d.id, "name": d.name, "amount": float(d.amount), "stage": d.stage.value}
                for d in deals
            ],
            "forecast": [
                {
                    "deal_id": f.deal_id,
                    "name": f.deal_name,
                    "amount": float(f.amount),
                    "probability": f.probability,
                    "risk": f.risk_level,
                }
                for f in pipeline.forecast[:10]
            ],
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get pipeline status for executive integration."""
        # Don't call health_check - it does DB operations that may block
        return {
            "running": self._running,
            "pipeline_type": "bleval",
        }