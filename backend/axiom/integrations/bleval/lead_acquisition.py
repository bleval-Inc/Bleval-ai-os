"""Lead Acquisition Engine — Captures, enriches, and scores leads."""

import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from pydantic import BaseModel, Field

from axiom.data.models import (
    Lead,
    Contact,
    Account,
    LeadStatus,
    LeadSource,
    Activity,
    ActivityType,
)
from axiom.integrations.layer import IntegrationLayer, DataNormalizer, Deduplicator, NormalizationConfig, DeduplicationConfig
from axiom.runtime.logging import RuntimeLogger

if TYPE_CHECKING:
    from axiom.integrations.research import NewsArticleRaw, ContentProcessor


class LeadAcquisitionConfig(BaseModel):
    """Lead acquisition configuration."""

    # Sources
    enable_web_forms: bool = True
    enable_chat: bool = True
    enable_email: bool = True
    enable_social: bool = True
    enable_referral: bool = True
    enable_events: bool = True
    enable_partners: bool = True

    # Enrichment
    enable_enrichment: bool = True
    enrichment_providers: List[str] = Field(default_factory=lambda: ["clearbit", "apollo", "hunter"])
    enrich_on_create: bool = True
    enrich_on_score_change: bool = True

    # Scoring
    scoring_model: str = "default"  # default, ml, custom
    score_weights: Dict[str, float] = Field(default_factory=lambda: {
        "demographic": 0.3,
        "firmographic": 0.2,
        "behavioral": 0.3,
        "engagement": 0.2,
    })
    score_threshold_mql: int = 60
    score_threshold_sql: int = 80

    # Deduplication
    dedup_window_hours: int = 24
    dedup_fields: List[str] = Field(default_factory=lambda: ["email", "domain", "phone"])

    # Routing
    auto_assign: bool = True
    assignment_rules: List[Dict[str, Any]] = Field(default_factory=list)
    sla_hours: Dict[LeadStatus, int] = Field(default_factory=lambda: {
        LeadStatus.NEW: 1,
        LeadStatus.QUALIFIED: 4,
        LeadStatus.CONTACTED: 24,
    })


class EnrichmentResult(BaseModel):
    """Lead enrichment result."""

    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    provider: str = ""
    error: Optional[str] = None


class LeadAcquisitionEngine:
    """Lead capture, enrichment, and scoring engine."""

    def __init__(
        self,
        integration_layer: "IntegrationLayer",
        repository,  # BlevalRepository
        config: Optional[LeadAcquisitionConfig] = None,
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.repository = repository
        self.config = config or LeadAcquisitionConfig()
        self.logger = logger or RuntimeLogger()

        # Components
        self.normalizer = DataNormalizer(NormalizationConfig())
        self.deduplicator = Deduplicator(DeduplicationConfig())
        # Lazy import to avoid circular dependency
        from axiom.integrations.research import ContentProcessor
        self.processor = ContentProcessor(integration_layer)

        # Enrichment cache
        self._enrichment_cache: Dict[str, EnrichmentResult] = {}

    async def capture_lead(
        self,
        source: LeadSource,
        raw_data: Dict[str, Any],
        utm_params: Optional[Dict[str, str]] = None,
        referrer: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Lead:
        """Capture a new lead from any source."""
        # Normalize data
        normalized = self.normalizer.normalize_lead(raw_data)

        # Create lead object
        lead_data = {
            "email": normalized.get("email"),
            "first_name": normalized.get("first_name"),
            "last_name": normalized.get("last_name"),
            "company": normalized.get("company"),
            "phone": normalized.get("phone"),
            "title": normalized.get("title"),
            "source": source,
            "status": LeadStatus.NEW,
            "score": 0,
            "utm_source": utm_params.get("utm_source") if utm_params else None,
            "utm_medium": utm_params.get("utm_medium") if utm_params else None,
            "utm_campaign": utm_params.get("utm_campaign") if utm_params else None,
            "utm_content": utm_params.get("utm_content") if utm_params else None,
            "utm_term": utm_params.get("utm_term") if utm_params else None,
            "referrer": referrer,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "raw_data": raw_data,
        }

        # Deduplication check
        existing = await self._check_duplicate(lead_data)
        if existing:
            self.logger.info(f"Duplicate lead detected: {existing.email}")
            # Update existing lead with new touchpoint
            await self._add_touchpoint(existing.id, source, raw_data)
            return existing

        # Create lead
        lead = await self.repository.create_lead(**lead_data)

        # Enrich if enabled
        if self.config.enable_enrichment and self.config.enrich_on_create:
            asyncio.create_task(self._enrich_lead(lead.id))

        # Score lead
        await self._score_lead(lead.id)

        # Route lead
        if self.config.auto_assign:
            await self._route_lead(lead.id)

        # Log activity
        await self.repository.create_activity(
            lead_id=lead.id,
            type=ActivityType.FORM_SUBMIT if source == LeadSource.WEB_FORM else ActivityType.NOTE,
            subject=f"Lead captured from {source.value}",
            description=f"Source: {source.value}, Raw: {raw_data}",
            occurred_at=datetime.utcnow(),
        )

        return lead

    async def _check_duplicate(self, lead_data: Dict[str, Any]) -> Optional[Lead]:
        """Check for duplicate lead."""
        # Check email
        if lead_data.get("email"):
            existing = await self.repository.get_lead_by_email(lead_data["email"])
            if existing:
                # Check if within dedup window
                if existing.created_at > datetime.utcnow() - timedelta(hours=self.config.dedup_window_hours):
                    return existing

        # Check domain
        if lead_data.get("company"):
            domain = self._extract_domain(lead_data["company"])
            if domain:
                # Would check for matching domain leads
                pass

        return None

    def _extract_domain(self, company: str) -> Optional[str]:
        """Extract domain from company name."""
        # Simplified - would use Clearbit or similar
        return None

    async def _add_touchpoint(self, lead_id: int, source: LeadSource, data: Dict[str, Any]):
        """Add touchpoint to existing lead."""
        await self.repository.create_activity(
            lead_id=lead_id,
            type=ActivityType.NOTE,
            subject=f"Touchpoint from {source.value}",
            description=f"Additional interaction: {data}",
            occurred_at=datetime.utcnow(),
        )

    async def _enrich_lead(self, lead_id: int):
        """Enrich lead with external data."""
        lead = await self.repository.get_lead(lead_id)
        if not lead or not lead.email:
            return

        cache_key = f"enrich_{lead.email}"
        if cache_key in self._enrichment_cache:
            cached = self._enrichment_cache[cache_key]
            if (datetime.utcnow() - datetime.fromisoformat(cached.data.get("_cached_at", "2000-01-01"))).hours < 24:
                await self._apply_enrichment(lead_id, cached.data)
                return

        enrichment_data = {}
        confidence = 0.0

        # Try each enrichment provider
        for provider in self.config.enrichment_providers:
            try:
                result = await self._enrich_with_provider(lead, provider)
                if result.success:
                    enrichment_data.update(result.data)
                    confidence = max(confidence, result.confidence)
            except Exception as e:
                self.logger.error(f"Enrichment provider {provider} failed: {e}")

        if enrichment_data:
            enrichment_data["_cached_at"] = datetime.utcnow().isoformat()
            self._enrichment_cache[cache_key] = EnrichmentResult(
                success=True, data=enrichment_data, confidence=confidence
            )
            await self._apply_enrichment(lead_id, enrichment_data)

    async def _enrich_with_provider(self, lead: Lead, provider: str) -> EnrichmentResult:
        """Enrich with specific provider."""
        # Placeholder for actual enrichment APIs
        if provider == "clearbit":
            # Would call Clearbit API
            return EnrichmentResult(
                success=False, data={}, confidence=0.0, provider=provider
            )
        elif provider == "apollo":
            return EnrichmentResult(
                success=False, data={}, confidence=0.0, provider=provider
            )
        elif provider == "hunter":
            return EnrichmentResult(
                success=False, data={}, confidence=0.0, provider=provider
            )

        return EnrichmentResult(
            success=False, data={}, confidence=0.0, provider=provider,
            error=f"Unknown provider: {provider}"
        )

    async def _apply_enrichment(self, lead_id: int, data: Dict[str, Any]):
        """Apply enrichment data to lead."""
        update_data = {}

        # Map enrichment fields
        field_map = {
            "company_name": "company",
            "company_domain": "company_domain",
            "company_size": "company_size",
            "company_industry": "industry",
            "company_revenue": "revenue",
            "location": "location",
            "linkedin_url": "linkedin_url",
            "twitter_url": "twitter_url",
            "phone": "phone",
            "title": "title",
        }

        for enrich_field, lead_field in field_map.items():
            if enrich_field in data:
                update_data[lead_field] = data[enrich_field]

        if update_data:
            await self.repository.update_lead(lead_id, **update_data)

    async def _score_lead(self, lead_id: int):
        """Score lead based on configured model."""
        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return

        score = 0
        factors = {}

        # Demographic scoring
        demo_score = self._score_demographic(lead)
        score += demo_score * self.config.score_weights.get("demographic", 0.3)
        factors["demographic"] = demo_score

        # Firmographic scoring
        firmo_score = self._score_firmographic(lead)
        score += firmo_score * self.config.score_weights.get("firmographic", 0.2)
        factors["firmographic"] = firmo_score

        # Behavioral scoring
        behav_score = await self._score_behavioral(lead_id)
        score += behav_score * self.config.score_weights.get("behavioral", 0.3)
        factors["behavioral"] = behav_score

        # Engagement scoring
        engage_score = await self._score_engagement(lead_id)
        score += engage_score * self.config.score_weights.get("engagement", 0.2)
        factors["engagement"] = engage_score

        final_score = min(int(score), 100)

        # Update lead
        await self.repository.update_lead(lead_id, score=final_score, scoring_factors=factors)

        # Check for MQL/SQL thresholds
        if final_score >= self.config.score_threshold_sql and lead.status != LeadStatus.QUALIFIED:
            await self.repository.update_lead(lead_id, status=LeadStatus.QUALIFIED)
        elif final_score >= self.config.score_threshold_mql and lead.status == LeadStatus.NEW:
            await self.repository.update_lead(lead_id, status=LeadStatus.QUALIFIED)

    def _score_demographic(self, lead: Lead) -> int:
        """Score based on demographic data."""
        score = 0
        if lead.first_name: score += 10
        if lead.last_name: score += 10
        if lead.title:
            score += 20
            # Seniority keywords
            senior_keywords = ["vp", "vice president", "director", "head", "chief", "cto", "ceo", "cfo", "cmo"]
            if any(k in lead.title.lower() for k in senior_keywords):
                score += 20
        if lead.phone: score += 10
        return min(score, 100)

    def _score_firmographic(self, lead: Lead) -> int:
        """Score based on company data."""
        score = 0
        if lead.company: score += 15
        if lead.company_domain: score += 10
        if lead.company_size:
            size = lead.company_size.lower()
            if "1000" in size or "enterprise" in size: score += 30
            elif "500" in size: score += 25
            elif "200" in size: score += 20
            elif "50" in size: score += 15
            else: score += 10
        if lead.industry:
            # Target industries
            target_industries = ["saas", "software", "technology", "fintech", "ai", "ml"]
            if any(t in lead.industry.lower() for t in target_industries):
                score += 20
        if lead.revenue:
            score += 10
        return min(score, 100)

    async def _score_behavioral(self, lead_id: int) -> int:
        """Score based on behavioral signals."""
        activities = await self.repository.get_activities_for_lead(lead_id, limit=50)
        score = 0

        for activity in activities:
            if activity.type == ActivityType.EMAIL_OPEN:
                score += 5
            elif activity.type == ActivityType.EMAIL_CLICK:
                score += 10
            elif activity.type == ActivityType.WEB_VISIT:
                score += 5
            elif activity.type == ActivityType.FORM_SUBMIT:
                score += 20
            elif activity.type == ActivityType.CHAT:
                score += 15
            elif activity.type == ActivityType.CALL:
                score += 25
            elif activity.type == ActivityType.MEETING:
                score += 30

        return min(score, 100)

    async def _score_engagement(self, lead_id: int) -> int:
        """Score based on recent engagement."""
        activities = await self.repository.get_activities_for_lead(lead_id, limit=20)
        if not activities:
            return 0

        # Recency factor
        now = datetime.utcnow()
        recent_count = sum(1 for a in activities if (now - a.occurred_at).days <= 7)

        # Frequency
        total = len(activities)

        score = min(recent_count * 10 + total * 2, 100)
        return score

    async def _route_lead(self, lead_id: int):
        """Route lead to owner based on rules."""
        lead = await self.repository.get_lead(lead_id)
        if not lead:
            return

        for rule in self.config.assignment_rules:
            condition = rule.get("condition", {})
            owner = rule.get("owner_id")

            match = True
            for field, value in condition.items():
                lead_value = getattr(lead, field, None)
                if lead_value != value:
                    match = False
                    break

            if match and owner:
                await self.repository.update_lead(lead_id, owner_id=owner)
                break

    async def get_leads_needing_followup(self) -> List[Lead]:
        """Get leads that need follow-up based on SLA."""
        return await self.repository.get_leads_needing_followup(datetime.utcnow())

    async def bulk_import_leads(
        self,
        leads: List[Dict[str, Any]],
        source: LeadSource,
    ) -> Dict[str, Any]:
        """Bulk import leads."""
        results = {"created": 0, "updated": 0, "duplicates": 0, "errors": []}

        for lead_data in leads:
            try:
                lead = await self.capture_lead(source, lead_data)
                # Would track created vs updated
                results["created"] += 1
            except Exception as e:
                results["errors"].append(str(e))

        return results