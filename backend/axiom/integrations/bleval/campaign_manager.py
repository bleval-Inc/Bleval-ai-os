"""Campaign Manager — Manages marketing campaigns and sequences."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from axiom.data.models import (
    Campaign,
    CampaignStatus,
    Lead,
    Activity,
    ActivityType,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class CampaignConfig(BaseModel):
    """Campaign configuration."""

    # Defaults
    default_sender: str = "marketing@bleval.ai"
    default_reply_to: str = "sales@bleval.ai"

    # Tracking
    track_opens: bool = True
    track_clicks: bool = True
    track_replies: bool = True

    # Limits
    max_emails_per_day: int = 500
    max_emails_per_hour: int = 50
    bounce_rate_limit: float = 0.05
    complaint_rate_limit: float = 0.01

    # Sequences
    default_sequence_delay_days: int = 2
    max_sequence_steps: int = 10

    # A/B Testing
    enable_ab_testing: bool = True
    min_sample_size: int = 100
    confidence_level: float = 0.95


class SequenceStep(BaseModel):
    """Email sequence step."""

    step: int
    subject_template: str
    body_template: str
    delay_days: int = 2
    conditions: Dict[str, Any] = Field(default_factory=dict)
    ab_variants: List[Dict[str, str]] = Field(default_factory=list)


class CampaignSequence(BaseModel):
    """Email sequence for a campaign."""

    campaign_id: int
    name: str
    steps: List[SequenceStep] = Field(default_factory=list)
    trigger: str = "lead_created"  # lead_created, stage_changed, manual
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class CampaignMetrics(BaseModel):
    """Campaign performance metrics."""

    campaign_id: int
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0
    complained: int = 0
    unsubscribed: int = 0

    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    conversion_rate: float = 0.0

    revenue_attributed: Decimal = Decimal("0")
    roi: float = 0.0


class CampaignManager:
    """Campaign and sequence management."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        repository,  # BlevalRepository
        config: Optional[CampaignConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.config = config or CampaignConfig()
        self.logger = logger or RuntimeLogger()

        self._sequences: Dict[int, CampaignSequence] = {}

    async def create_campaign(
        self,
        name: str,
        description: str,
        owner_id: str,
        sequence: Optional[CampaignSequence] = None,
        **kwargs
    ) -> Campaign:
        """Create a new campaign."""
        campaign = await self.repository.create_campaign(
            name=name,
            description=description,
            owner_id=owner_id,
            status=CampaignStatus.DRAFT,
            **kwargs
        )

        if sequence:
            sequence.campaign_id = campaign.id
            self._sequences[campaign.id] = sequence

        return campaign

    async def launch_campaign(self, campaign_id: int) -> bool:
        """Launch a campaign."""
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            return False

        if campaign.status != CampaignStatus.DRAFT:
            self.logger.warning(f"Campaign {campaign_id} not in DRAFT status")
            return False

        campaign.status = CampaignStatus.ACTIVE
        campaign.launched_at = datetime.utcnow()
        await self.repository.session.flush()

        # Enroll leads matching criteria
        if campaign.target_criteria:
            await self._enroll_leads(campaign_id)

        return True

    async def pause_campaign(self, campaign_id: int) -> bool:
        """Pause a campaign."""
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            return False

        campaign.status = CampaignStatus.PAUSED
        await self.repository.session.flush()
        return True

    async def complete_campaign(self, campaign_id: int) -> bool:
        """Complete a campaign."""
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            return False

        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.utcnow()
        await self.repository.session.flush()
        return True

    def add_sequence(self, sequence: CampaignSequence):
        """Add a sequence to a campaign."""
        self._sequences[sequence.campaign_id] = sequence

    async def enroll_lead(self, campaign_id: int, lead_id: int) -> bool:
        """Enroll a lead in a campaign sequence."""
        sequence = self._sequences.get(campaign_id)
        if not sequence or not sequence.is_active:
            return False

        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return False

        # Check if already enrolled
        # Would track enrollment in separate table

        # Schedule first step
        await self._schedule_sequence_step(campaign_id, lead_id, 0)

        return True

    async def _enroll_leads(self, campaign_id: int):
        """Enroll all matching leads."""
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign or not campaign.target_criteria:
            return

        # Would query leads matching criteria
        # For now, placeholder
        pass

    async def _schedule_sequence_step(
        self, campaign_id: int, lead_id: int, step_index: int
    ):
        """Schedule a sequence step for a lead."""
        sequence = self._sequences.get(campaign_id)
        if not sequence or step_index >= len(sequence.steps):
            return

        step = sequence.steps[step_index]
        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return

        # Check conditions
        if not self._check_conditions(lead, step.conditions):
            # Skip to next step
            await self._schedule_sequence_step(campaign_id, lead_id, step_index + 1)
            return

        # Render templates
        subject = self._render_template(step.subject_template, lead)
        body = self._render_template(step.body_template, lead)

        # Schedule send
        send_at = datetime.utcnow() + timedelta(days=step.delay_days)

        # Would integrate with email provider
        # For now, log activity
        await self.repository.create_activity(
            lead_id=lead_id,
            type=ActivityType.EMAIL_SENT,
            subject=f"Campaign: {subject}",
            description=f"Sequence step {step.step}: {body[:200]}",
            occurred_at=send_at,
            extra_data={
                "campaign_id": campaign_id,
                "sequence_step": step.step,
                "subject": subject,
                "body": body,
            },
        )

        # Schedule next step
        if step_index + 1 < len(sequence.steps):
            asyncio.create_task(self._delayed_schedule(campaign_id, lead_id, step_index + 1))

    async def _delayed_schedule(
        self, campaign_id: int, lead_id: int, step_index: int
    ):
        """Schedule next step after delay."""
        sequence = self._sequences.get(campaign_id)
        if not sequence:
            return

        step = sequence.steps[step_index - 1]
        await asyncio.sleep(step.delay_days * 86400)  # days to seconds
        await self._schedule_sequence_step(campaign_id, lead_id, step_index)

    def _check_conditions(self, lead: Lead, conditions: Dict[str, Any]) -> bool:
        """Check if lead matches conditions."""
        for field, value in conditions.items():
            lead_value = getattr(lead, field, None)
            if isinstance(value, list):
                if lead_value not in value:
                    return False
            elif isinstance(value, dict):
                # Operator: { "operator": "gte", "value": 50 }
                op = value.get("operator", "eq")
                val = value.get("value")
                if op == "gte" and (lead_value or 0) < val:
                    return False
                elif op == "lte" and (lead_value or 0) > val:
                    return False
                elif op == "eq" and lead_value != val:
                    return False
                elif op == "neq" and lead_value == val:
                    return False
            elif lead_value != value:
                return False
        return True

    def _render_template(self, template: str, lead: Lead) -> str:
        """Render template with lead data."""
        replacements = {
            "{{first_name}}": lead.first_name or "",
            "{{last_name}}": lead.last_name or "",
            "{{email}}": lead.email or "",
            "{{company}}": lead.company or "",
            "{{title}}": lead.title or "",
            "{{owner_name}}": lead.owner_id or "",
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result

    async def track_email_event(
        self,
        campaign_id: int,
        lead_id: int,
        event_type: str,  # sent, delivered, open, click, reply, bounce, complain, unsubscribe
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track email event."""
        activity_type_map = {
            "sent": ActivityType.EMAIL_SENT,
            "delivered": ActivityType.EMAIL_DELIVERED,
            "open": ActivityType.EMAIL_OPEN,
            "click": ActivityType.EMAIL_CLICK,
            "reply": ActivityType.EMAIL_REPLY,
            "bounce": ActivityType.EMAIL_BOUNCE,
            "complain": ActivityType.SPAM_COMPLAINT,
            "unsubscribe": ActivityType.UNSUBSCRIBE,
        }

        activity_type = activity_type_map.get(event_type, ActivityType.NOTE)

        await self.repository.create_activity(
            lead_id=lead_id,
            type=activity_type,
            subject=f"Email {event_type}",
            description=metadata.get("description", "") if metadata else "",
            occurred_at=datetime.utcnow(),
            extra_data={
                "campaign_id": campaign_id,
                "event_type": event_type,
                **(metadata or {}),
            },
        )

    async def get_campaign_metrics(self, campaign_id: int) -> CampaignMetrics:
        """Get campaign metrics."""
        campaign = await self.repository.get_campaign(campaign_id)
        if not campaign:
            return CampaignMetrics(campaign_id=campaign_id)

        # Get activities for this campaign
        # Would query activities with campaign_id in extra_data
        # For now, placeholder metrics

        metrics = CampaignMetrics(campaign_id=campaign_id)

        # Calculate rates
        if metrics.sent > 0:
            metrics.open_rate = metrics.opened / metrics.sent
            metrics.click_rate = metrics.clicked / metrics.sent
            metrics.reply_rate = metrics.replied / metrics.sent
            metrics.bounce_rate = metrics.bounced / metrics.sent

        return metrics

    async def run_ab_test(
        self,
        campaign_id: int,
        variant_a: Dict[str, str],
        variant_b: Dict[str, str],
        sample_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run A/B test on campaign emails."""
        # Simplified - would split leads and send variants
        return {
            "campaign_id": campaign_id,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "status": "running",
            "results": {},
        }

    async def get_campaign_performance(
        self, owner_id: Optional[str] = None, days: int = 30
    ) -> List[CampaignMetrics]:
        """Get performance for all campaigns."""
        campaigns = await self.repository.list_campaigns(owner_id=owner_id)
        metrics = []

        for campaign in campaigns:
            m = await self.get_campaign_metrics(campaign.id)
            metrics.append(m)

        return metrics