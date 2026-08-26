"""BLEVAL Repository — Data access for sales, CRM, deals, campaigns."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.data.models import (
    BlevalBase,
    Lead,
    Contact,
    Account,
    Opportunity,
    Deal,
    Campaign,
    Activity,
    LeadStatus,
    DealStage,
    CampaignStatus,
)

if TYPE_CHECKING:
    from axiom.runtime.logging import RuntimeLogger


class BlevalRepository:
    """Repository for BLEVAL domain operations."""

    def __init__(self, session: AsyncSession, logger: Optional["RuntimeLogger"] = None) -> None:
        self.session = session
        from axiom.runtime.logging import RuntimeLogger
        self.logger = logger or RuntimeLogger()

    # ──────────────────────────────────────────────────────────────────────────────
    # LEADS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_lead(self, **kwargs) -> Lead:
        """Create a new lead."""
        lead = Lead(**kwargs)
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID."""
        result = await self.session.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def get_lead_by_uuid(self, uuid: str) -> Optional[Lead]:
        """Get lead by UUID."""
        result = await self.session.execute(select(Lead).where(Lead.uuid == uuid))
        return result.scalar_one_or_none()

    async def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email (most recent)."""
        result = await self.session.execute(
            select(Lead).where(Lead.email == email).order_by(desc(Lead.created_at))
        )
        return result.scalar_one_or_none()

    async def update_lead(self, lead_id: int, **kwargs) -> Optional[Lead]:
        """Update lead fields."""
        lead = await self.get_lead(lead_id)
        if lead:
            for key, value in kwargs.items():
                if hasattr(lead, key):
                    setattr(lead, key, value)
            lead.updated_at = datetime.utcnow()
            await self.session.flush()
        return lead

    async def list_leads(
        self,
        status: Optional[LeadStatus] = None,
        owner_id: Optional[str] = None,
        source: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Lead]:
        """List leads with filters."""
        query = select(Lead).order_by(desc(Lead.created_at))

        if status:
            query = query.where(Lead.status == status)
        if owner_id:
            query = query.where(Lead.owner_id == owner_id)
        if source:
            query = query.where(Lead.source == source)
        if min_score:
            query = query.where(Lead.score >= min_score)

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_leads(
        self,
        status: Optional[LeadStatus] = None,
        owner_id: Optional[str] = None,
    ) -> int:
        """Count leads with filters."""
        query = select(func.count(Lead.id))
        if status:
            query = query.where(Lead.status == status)
        if owner_id:
            query = query.where(Lead.owner_id == owner_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_leads_needing_followup(self, before: datetime, limit: int = 50) -> List[Lead]:
        """Get leads that need follow-up."""
        query = (
            select(Lead)
            .where(
                and_(
                    Lead.next_follow_up_at.is_not(None),
                    Lead.next_follow_up_at <= before,
                    Lead.status.in_([
                        LeadStatus.NEW,
                        LeadStatus.QUALIFIED,
                        LeadStatus.CONTACTED,
                        LeadStatus.NURTURING,
                    ]),
                )
            )
            .order_by(Lead.next_follow_up_at)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # CONTACTS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_contact(self, **kwargs) -> Contact:
        """Create a new contact."""
        contact = Contact(**kwargs)
        self.session.add(contact)
        await self.session.flush()
        return contact

    async def get_contact(self, contact_id: int) -> Optional[Contact]:
        """Get contact by ID."""
        result = await self.session.execute(select(Contact).where(Contact.id == contact_id))
        return result.scalar_one_or_none()

    async def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email."""
        result = await self.session.execute(
            select(Contact).where(Contact.email == email).order_by(desc(Contact.created_at))
        )
        return result.scalar_one_or_none()

    async def list_contacts(
        self,
        account_id: Optional[int] = None,
        owner_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Contact]:
        """List contacts."""
        query = select(Contact).order_by(desc(Contact.created_at))
        if account_id:
            query = query.where(Contact.account_id == account_id)
        if owner_id:
            query = query.where(Contact.owner_id == owner_id)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # ACCOUNTS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_account(self, **kwargs) -> Account:
        """Create a new account."""
        account = Account(**kwargs)
        self.session.add(account)
        await self.session.flush()
        return account

    async def get_account(self, account_id: int) -> Optional[Account]:
        """Get account by ID."""
        result = await self.session.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def get_account_by_domain(self, domain: str) -> Optional[Account]:
        """Get account by domain."""
        result = await self.session.execute(select(Account).where(Account.domain == domain))
        return result.scalar_one_or_none()

    # ──────────────────────────────────────────────────────────────────────────────
    # OPPORTUNITIES
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_opportunity(self, **kwargs) -> Opportunity:
        """Create a new opportunity."""
        opp = Opportunity(**kwargs)
        self.session.add(opp)
        await self.session.flush()
        return opp

    async def get_opportunity(self, opp_id: int) -> Optional[Opportunity]:
        """Get opportunity by ID."""
        result = await self.session.execute(select(Opportunity).where(Opportunity.id == opp_id))
        return result.scalar_one_or_none()

    async def list_opportunities(
        self,
        stage: Optional[DealStage] = None,
        owner_id: Optional[str] = None,
        account_id: Optional[int] = None,
        min_amount: Optional[Decimal] = None,
        expected_close_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Opportunity]:
        """List opportunities."""
        query = select(Opportunity).order_by(desc(Opportunity.created_at))

        if stage:
            query = query.where(Opportunity.stage == stage)
        if owner_id:
            query = query.where(Opportunity.owner_id == owner_id)
        if account_id:
            query = query.where(Opportunity.account_id == account_id)
        if min_amount:
            query = query.where(Opportunity.amount >= min_amount)
        if expected_close_before:
            query = query.where(Opportunity.expected_close_date <= expected_close_before)

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pipeline_summary(self, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pipeline summary by stage."""
        query = select(
            Opportunity.stage,
            func.count(Opportunity.id).label("count"),
            func.sum(Opportunity.amount).label("total_amount"),
            func.sum(Opportunity.weighted_amount).label("weighted_amount"),
        ).group_by(Opportunity.stage)

        if owner_id:
            query = query.where(Opportunity.owner_id == owner_id)

        result = await self.session.execute(query)
        return {
            row.stage.value: {
                "count": row.count,
                "total_amount": float(row.total_amount or 0),
                "weighted_amount": float(row.weighted_amount or 0),
            }
            for row in result.all()
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # DEALS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_deal(self, **kwargs) -> Deal:
        """Create a new deal."""
        deal = Deal(**kwargs)
        self.session.add(deal)
        await self.session.flush()
        return deal

    async def get_deal(self, deal_id: int) -> Optional[Deal]:
        """Get deal by ID."""
        result = await self.session.execute(select(Deal).where(Deal.id == deal_id))
        return result.scalar_one_or_none()

    async def list_deals(
        self,
        account_id: Optional[int] = None,
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Deal]:
        """List deals."""
        query = select(Deal).order_by(desc(Deal.created_at))
        if account_id:
            query = query.where(Deal.account_id == account_id)
        if owner_id:
            query = query.where(Deal.owner_id == owner_id)
        if status:
            query = query.where(Deal.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_revenue_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get revenue summary."""
        query = select(
            func.sum(Deal.amount).label("total_revenue"),
            func.count(Deal.id).label("deal_count"),
            func.avg(Deal.amount).label("avg_deal_size"),
        )

        if start_date:
            query = query.where(Deal.closed_at >= start_date)
        if end_date:
            query = query.where(Deal.closed_at <= end_date)

        result = await self.session.execute(query)
        row = result.one()
        return {
            "total_revenue": float(row.total_revenue or 0),
            "deal_count": row.deal_count or 0,
            "avg_deal_size": float(row.avg_deal_size or 0),
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # CAMPAIGNS
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_campaign(self, **kwargs) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(**kwargs)
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Get campaign by ID."""
        result = await self.session.execute(select(Campaign).where(Campaign.id == campaign_id))
        return result.scalar_one_or_none()

    async def list_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        owner_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Campaign]:
        """List campaigns."""
        query = select(Campaign).order_by(desc(Campaign.created_at))
        if status:
            query = query.where(Campaign.status == status)
        if owner_id:
            query = query.where(Campaign.owner_id == owner_id)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────────────────
    # ACTIVITIES
    # ──────────────────────────────────────────────────────────────────────────────

    async def create_activity(self, **kwargs) -> Activity:
        """Create a new activity."""
        activity = Activity(**kwargs)
        self.session.add(activity)
        await self.session.flush()
        return activity

    async def get_activities_for_lead(
        self, lead_id: int, limit: int = 50
    ) -> List[Activity]:
        """Get activities for a lead."""
        query = (
            select(Activity)
            .where(Activity.lead_id == lead_id)
            .order_by(desc(Activity.occurred_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_activities_for_opportunity(
        self, opp_id: int, limit: int = 50
    ) -> List[Activity]:
        """Get activities for an opportunity."""
        query = (
            select(Activity)
            .where(Activity.opportunity_id == opp_id)
            .order_by(desc(Activity.occurred_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_activities(
        self,
        owner_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        days: int = 7,
        limit: int = 100,
    ) -> List[Activity]:
        """Get recent activities."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = (
            select(Activity)
            .where(Activity.occurred_at >= cutoff)
            .order_by(desc(Activity.occurred_at))
        )

        if owner_id:
            query = query.where(Activity.owner_id == owner_id)
        if activity_type:
            query = query.where(Activity.type == activity_type)

        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())