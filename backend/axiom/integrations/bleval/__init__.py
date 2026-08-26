"""BLEVAL Acquisition Pipeline — CRM, Leads, Deals, Campaigns."""

from .crm_sync import CRMSyncProvider, CRMSyncConfig, SyncResult
from .lead_acquisition import LeadAcquisitionEngine, LeadAcquisitionConfig, EnrichmentResult
from .deal_tracker import DealTracker, DealTrackerConfig, DealForecast, PipelineSnapshot
from .campaign_manager import CampaignManager, CampaignConfig, SequenceStep, CampaignSequence, CampaignMetrics
from .pipeline import BlevalPipeline

__all__ = [
    "CRMSyncProvider",
    "CRMSyncConfig",
    "SyncResult",
    "LeadAcquisitionEngine",
    "LeadAcquisitionConfig",
    "EnrichmentResult",
    "DealTracker",
    "DealTrackerConfig",
    "DealForecast",
    "PipelineSnapshot",
    "CampaignManager",
    "CampaignConfig",
    "SequenceStep",
    "CampaignSequence",
    "CampaignMetrics",
    "BlevalPipeline",
]