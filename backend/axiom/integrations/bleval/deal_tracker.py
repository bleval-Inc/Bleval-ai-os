"""Deal Tracker — Tracks deals through pipeline stages with forecasting."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from axiom.data.models import (
    Deal,
    DealStage,
    Opportunity,
    Activity,
    ActivityType,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class DealTrackerConfig(BaseModel):
    """Deal tracker configuration."""

    # Stage probabilities
    stage_probabilities: Dict[DealStage, float] = Field(default_factory=lambda: {
        DealStage.PROSPECTING: 0.10,
        DealStage.QUALIFICATION: 0.25,
        DealStage.PROPOSAL: 0.50,
        DealStage.NEGOTIATION: 0.75,
        DealStage.CLOSED_WON: 1.0,
        DealStage.CLOSED_LOST: 0.0,
    })

    # Forecasting
    forecast_horizon_days: int = 90
    min_deal_size_for_forecast: Decimal = Decimal("1000")

    # Alerts
    stale_deal_days: int = 30
    deal_slippage_alert: bool = True
    high_value_threshold: Decimal = Decimal("50000")

    # Automation
    auto_advance_stage: bool = False
    require_approval_for_stage: List[DealStage] = Field(default_factory=lambda: [
        DealStage.NEGOTIATION, DealStage.CLOSED_WON
    ])


class DealForecast(BaseModel):
    """Deal forecast entry."""

    deal_id: int
    deal_name: str
    stage: DealStage
    amount: Decimal
    weighted_amount: Decimal
    probability: float
    expected_close_date: Optional[datetime]
    days_in_stage: int
    risk_level: str  # low, medium, high, critical
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None


class PipelineSnapshot(BaseModel):
    """Pipeline snapshot for a point in time."""

    timestamp: datetime
    total_pipeline: Decimal
    weighted_pipeline: Decimal
    by_stage: Dict[str, Dict[str, Any]]
    forecast: List[DealForecast]
    conversion_rates: Dict[str, float]
    avg_deal_size: Decimal
    avg_sales_cycle_days: float


class DealTracker:
    """Deal tracking and forecasting engine."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        repository,  # BlevalRepository
        config: Optional[DealTrackerConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.config = config or DealTrackerConfig()
        self.logger = logger or RuntimeLogger()

    async def create_deal_from_opportunity(
        self, opportunity_id: int, won: bool = True
    ) -> Optional[Deal]:
        """Create a deal from a closed-won opportunity."""
        opp = await self.repository.get_opportunity(opportunity_id)
        if not opp:
            return None

        if won:
            stage = DealStage.CLOSED_WON
        else:
            stage = DealStage.CLOSED_LOST

        deal = await self.repository.create_deal(
            opportunity_id=opp.id,
            account_id=opp.account_id,
            owner_id=opp.owner_id,
            name=opp.name,
            amount=opp.amount,
            stage=stage,
            status="won" if won else "lost",
            closed_at=datetime.utcnow(),
            source=opp.source,
        )

        # Log activity
        await self.repository.create_activity(
            opportunity_id=opp.id,
            type=ActivityType.NOTE,
            subject=f"Deal {'won' if won else 'lost'}",
            description=f"Amount: {opp.amount}, Stage: {stage.value}",
            occurred_at=datetime.utcnow(),
        )

        return deal

    async def update_deal_stage(
        self,
        deal_id: int,
        new_stage: DealStage,
        reason: Optional[str] = None,
    ) -> Optional[Deal]:
        """Update deal stage with validation."""
        deal = await self.repository.get_deal(deal_id)
        if not deal:
            return None

        old_stage = deal.stage

        # Check if approval required
        if new_stage in self.config.require_approval_for_stage:
            # Would trigger approval workflow
            self.logger.info(f"Deal {deal_id} stage change to {new_stage.value} requires approval")
            # For now, just log
            pass

        # Update deal
        deal.stage = new_stage
        deal.probability = self.config.stage_probabilities.get(new_stage, 0.0)
        deal.weighted_amount = deal.amount * Decimal(str(deal.probability))
        deal.updated_at = datetime.utcnow()

        if new_stage == DealStage.CLOSED_WON:
            deal.status = "won"
            deal.closed_at = datetime.utcnow()
        elif new_stage == DealStage.CLOSED_LOST:
            deal.status = "lost"
            deal.closed_at = datetime.utcnow()
            deal.loss_reason = reason

        await self.repository.session.flush()

        # Log activity
        await self.repository.create_activity(
            deal_id=deal_id,
            type=ActivityType.NOTE,
            subject=f"Stage changed: {old_stage.value} -> {new_stage.value}",
            description=reason or "Stage updated",
            occurred_at=datetime.utcnow(),
        )

        return deal

    async def get_deal_forecast(self, deal_id: int) -> Optional[DealForecast]:
        """Get forecast for a single deal."""
        deal = await self.repository.get_deal(deal_id)
        if not deal:
            return None

        days_in_stage = (datetime.utcnow() - deal.updated_at).days if deal.updated_at else 0

        # Risk assessment
        risk = "low"
        if deal.stage in [DealStage.PROPOSAL, DealStage.NEGOTIATION]:
            if days_in_stage > 30:
                risk = "high"
            elif days_in_stage > 14:
                risk = "medium"

        if deal.amount >= self.config.high_value_threshold:
            risk = "high" if risk != "critical" else "critical"

        if deal.expected_close_date and deal.expected_close_date < datetime.utcnow():
            risk = "critical"

        next_action = None
        next_action_date = None
        if deal.stage == DealStage.PROSPECTING:
            next_action = "Qualify lead"
            next_action_date = datetime.utcnow() + timedelta(days=2)
        elif deal.stage == DealStage.QUALIFICATION:
            next_action = "Send proposal"
            next_action_date = datetime.utcnow() + timedelta(days=5)
        elif deal.stage == DealStage.PROPOSAL:
            next_action = "Follow up on proposal"
            next_action_date = datetime.utcnow() + timedelta(days=3)
        elif deal.stage == DealStage.NEGOTIATION:
            next_action = "Close negotiation"
            next_action_date = datetime.utcnow() + timedelta(days=7)

        return DealForecast(
            deal_id=deal.id,
            deal_name=deal.name,
            stage=deal.stage,
            amount=deal.amount,
            weighted_amount=deal.weighted_amount,
            probability=deal.probability,
            expected_close_date=deal.expected_close_date,
            days_in_stage=days_in_stage,
            risk_level=risk,
            next_action=next_action,
            next_action_date=next_action_date,
        )

    async def get_pipeline_snapshot(self, owner_id: Optional[str] = None) -> PipelineSnapshot:
        """Get current pipeline snapshot."""
        opportunities = await self.repository.list_opportunities(owner_id=owner_id)
        deals = await self.repository.list_deals(owner_id=owner_id)

        # Pipeline by stage
        by_stage = {}
        total_pipeline = Decimal("0")
        weighted_pipeline = Decimal("0")

        for opp in opportunities:
            stage_key = opp.stage.value
            if stage_key not in by_stage:
                by_stage[stage_key] = {"count": 0, "total_amount": Decimal("0"), "weighted": Decimal("0")}

            by_stage[stage_key]["count"] += 1
            by_stage[stage_key]["total_amount"] += opp.amount
            by_stage[stage_key]["weighted"] += opp.weighted_amount

            total_pipeline += opp.amount
            weighted_pipeline += opp.weighted_amount

        # Forecast
        forecast = []
        for opp in opportunities:
            if opp.amount >= self.config.min_deal_size_for_forecast:
                f = await self.get_deal_forecast(opp.id)
                if f:
                    forecast.append(f)

        # Also include open deals
        for deal in deals:
            if deal.stage not in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]:
                if deal.amount >= self.config.min_deal_size_for_forecast:
                    f = await self.get_deal_forecast(deal.id)
                    if f:
                        forecast.append(f)

        # Conversion rates (simplified)
        conversion_rates = {}
        stages = [DealStage.PROSPECTING, DealStage.QUALIFICATION, DealStage.PROPOSAL,
                  DealStage.NEGOTIATION, DealStage.CLOSED_WON]
        for i in range(len(stages) - 1):
            current = sum(1 for o in opportunities if o.stage == stages[i])
            next_stage = sum(1 for o in opportunities if o.stage == stages[i + 1])
            if current > 0:
                conversion_rates[f"{stages[i].value}_to_{stages[i+1].value}"] = next_stage / current

        # Average deal size
        won_deals = [d for d in deals if d.stage == DealStage.CLOSED_WON]
        avg_deal_size = Decimal("0")
        if won_deals:
            avg_deal_size = sum(d.amount for d in won_deals) / len(won_deals)

        # Average sales cycle
        cycle_days = 0
        if won_deals:
            cycles = [(d.closed_at - d.created_at).days for d in won_deals if d.closed_at]
            if cycles:
                cycle_days = sum(cycles) / len(cycles)

        return PipelineSnapshot(
            timestamp=datetime.utcnow(),
            total_pipeline=total_pipeline,
            weighted_pipeline=weighted_pipeline,
            by_stage={k: {kk: float(vv) if isinstance(vv, Decimal) else vv for kk, vv in v.items()}
                      for k, v in by_stage.items()},
            forecast=forecast,
            conversion_rates=conversion_rates,
            avg_deal_size=avg_deal_size,
            avg_sales_cycle_days=cycle_days,
        )

    async def get_stale_deals(self, owner_id: Optional[str] = None) -> List[Deal]:
        """Get deals that haven't moved in configured days."""
        cutoff = datetime.utcnow() - timedelta(days=self.config.stale_deal_days)

        deals = await self.repository.list_deals(owner_id=owner_id)
        stale = [
            d for d in deals
            if d.stage not in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]
            and d.updated_at < cutoff
        ]

        return stale

    async def get_slipped_deals(self, owner_id: Optional[str] = None) -> List[Deal]:
        """Get deals that slipped past expected close date."""
        now = datetime.utcnow()
        deals = await self.repository.list_deals(owner_id=owner_id)

        slipped = [
            d for d in deals
            if d.stage not in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]
            and d.expected_close_date
            and d.expected_close_date < now
        ]

        return slipped

    async def get_high_value_deals(
        self, owner_id: Optional[str] = None
    ) -> List[DealForecast]:
        """Get high-value deal forecasts."""
        snapshot = await self.get_pipeline_snapshot(owner_id)
        return [f for f in snapshot.forecast if f.amount >= self.config.high_value_threshold]

    async def calculate_velocity(self, owner_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate pipeline velocity metrics."""
        opportunities = await self.repository.list_opportunities(owner_id=owner_id)
        deals = await self.repository.list_deals(owner_id=owner_id)

        # Closed won in last 90 days
        cutoff = datetime.utcnow() - timedelta(days=90)
        recent_won = [
            d for d in deals
            if d.stage == DealStage.CLOSED_WON
            and d.closed_at
            and d.closed_at >= cutoff
        ]

        # Number of deals
        num_deals = len(recent_won)

        # Total revenue
        total_revenue = sum(d.amount for d in recent_won)

        # Average deal size
        avg_size = total_revenue / num_deals if num_deals > 0 else Decimal("0")

        # Average sales cycle
        cycles = [(d.closed_at - d.created_at).days for d in recent_won if d.closed_at]
        avg_cycle = sum(cycles) / len(cycles) if cycles else 0

        # Win rate
        total_closed = len([d for d in deals if d.stage in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST] and d.closed_at and d.closed_at >= cutoff])
        win_rate = num_deals / total_closed if total_closed > 0 else 0

        # Velocity = (num_deals * avg_size * win_rate) / avg_cycle
        velocity = (num_deals * float(avg_size) * win_rate) / avg_cycle if avg_cycle > 0 else 0

        return {
            "period_days": 90,
            "deals_won": num_deals,
            "total_revenue": float(total_revenue),
            "avg_deal_size": float(avg_size),
            "avg_sales_cycle_days": avg_cycle,
            "win_rate": win_rate,
            "velocity_per_day": velocity,
        }

    async def predict_close_probability(self, deal_id: int) -> Dict[str, Any]:
        """Predict probability of closing based on historical data."""
        deal = await self.repository.get_deal(deal_id)
        if not deal:
            return {}

        # Base probability from stage
        base_prob = self.config.stage_probabilities.get(deal.stage, 0.0)

        # Adjust for time in stage
        days_in_stage = (datetime.utcnow() - deal.updated_at).days if deal.updated_at else 0
        if days_in_stage > 30:
            base_prob *= 0.7
        elif days_in_stage > 14:
            base_prob *= 0.9

        # Adjust for deal size vs average
        # Would compare to historical

        # Adjust for competitor presence
        # Would check activities

        return {
            "deal_id": deal_id,
            "base_probability": base_prob,
            "adjusted_probability": base_prob,
            "days_in_stage": days_in_stage,
            "recommendation": "nurture" if base_prob < 0.5 else "push",
        }