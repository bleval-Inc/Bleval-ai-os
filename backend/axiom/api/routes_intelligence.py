"""Market Intelligence API Routes — House of Valta Market Intelligence.
Provides access to market news, economic indicators, geopolitical events, and institutional information.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, desc, asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.data.models.intelligence import (
    MarketNews,
    EconomicIndicator,
    GeopoliticalEvent,
    InstitutionalInfo,
    IntelligenceCache,
    NewsCategory,
    NewsSourceType,
    RelevanceLevel,
)
from axiom.data.models.market import Symbol
from axiom.data.database import Domain


# Router — mounted in main.py
router = APIRouter(prefix="/intelligence", tags=["intelligence"])


_runtime = None


def set_runtime(runtime: Any) -> None:
    """Inject the application runtime into the API layer."""
    global _runtime
    _runtime = runtime


def _get_runtime():
    if _runtime is None:
        raise HTTPException(status_code=503, detail="Runtime not initialised")
    return _runtime


async def get_db():
    """Yield a read-only market database session for dependency-injected routes."""
    runtime = _get_runtime()
    async with runtime.data_manager.get_read_session(Domain.MARKET) as db:
        yield db


# Pydantic models for request/response validation
class MarketNewsBase(BaseModel):
    headline: str = Field(..., max_length=500)
    summary: Optional[str] = Field(None)
    content: Optional[str] = Field(None)
    url: Optional[str] = Field(None, max_length=1000)
    category: NewsCategory
    source_type: NewsSourceType
    source_name: str = Field(..., max_length=200)
    relevance_level: RelevanceLevel
    relevance_score: Optional[int] = Field(None, ge=0, le=100)
    affected_instruments: List[str] = Field(default_factory=list)
    affected_currencies: List[str] = Field(default_factory=list)
    affected_commodities: List[str] = Field(default_factory=list)
    affected_indices: List[str] = Field(default_factory=list)
    published_at: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)
    content_hash: Optional[str] = Field(None, max_length=64)
    source_id: Optional[str] = Field(None, max_length=100)
    related_symbol_ids: List[int] = Field(default_factory=list)


class MarketNewsCreate(MarketNewsBase):
    pass


class MarketNewsResponse(MarketNewsBase):
    id: int
    uuid: str
    received_at: datetime

    class Config:
        from_attributes = True


class EconomicIndicatorBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None)
    indicator_type: str = Field(..., max_length=50)
    release_date: datetime
    actual_value: Optional[float] = Field(None)
    forecast_value: Optional[float] = Field(None)
    previous_value: Optional[float] = Field(None)
    unit: Optional[str] = Field(None, max_length=20)
    impact_level: RelevanceLevel
    affected_instruments: List[str] = Field(default_factory=list)
    affected_currencies: List[str] = Field(default_factory=list)
    source_name: str = Field(..., max_length=200)
    source_type: NewsSourceType
    release_time: Optional[datetime] = None
    next_release: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)
    survey_median: Optional[float] = Field(None)


class EconomicIndicatorCreate(EconomicIndicatorBase):
    pass


class EconomicIndicatorResponse(EconomicIndicatorBase):
    id: int
    uuid: str

    class Config:
        from_attributes = True


class GeopoliticalEventBase(BaseModel):
    title: str = Field(..., max_length=300)
    description: Optional[str] = Field(None)
    event_type: str = Field(..., max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    countries_affected: List[str] = Field(default_factory=list)
    event_scope: str = Field(..., max_length=50)
    start_date: datetime
    end_date: Optional[datetime] = None
    is_ongoing: bool = Field(default=False)
    impact_level: RelevanceLevel
    impact_score: Optional[int] = Field(None, ge=0, le=100)
    affected_instruments: List[str] = Field(default_factory=list)
    affected_currencies: List[str] = Field(default_factory=list)
    affected_commodities: List[str] = Field(default_factory=list)
    source_name: str = Field(..., max_length=200)
    source_type: NewsSourceType
    source_reliability: int = Field(default=50, ge=0, le=100)
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class GeopoliticalEventCreate(GeopoliticalEventBase):
    pass


class GeopoliticalEventResponse(GeopoliticalEventBase):
    id: int
    uuid: str

    class Config:
        from_attributes = True


class InstitutionalInfoBase(BaseModel):
    title: str = Field(..., max_length=300)
    summary: Optional[str] = Field(None)
    content: Optional[str] = Field(None)
    author: Optional[str] = Field(None, max_length=200)
    institution: str = Field(..., max_length=200)
    info_type: str = Field(..., max_length=100)
    published_at: datetime
    relevance_level: RelevanceLevel
    relevance_score: Optional[int] = Field(None, ge=0, le=100)
    affected_instruments: List[str] = Field(default_factory=list)
    affected_currencies: List[str] = Field(default_factory=list)
    source_name: str = Field(..., max_length=200)
    source_type: NewsSourceType
    source_url: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    extra_data: dict = Field(default_factory=dict)


class InstitutionalInfoCreate(InstitutionalInfoBase):
    pass


class InstitutionalInfoResponse(InstitutionalInfoBase):
    id: int
    uuid: str
    received_at: datetime

    class Config:
        from_attributes = True


# Market News Endpoints
@router.get("/news", response_model=List[MarketNewsResponse])
async def get_market_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[NewsCategory] = Query(None),
    source_type: Optional[NewsSourceType] = Query(None),
    source_name: Optional[str] = Query(None),
    relevance_level: Optional[RelevanceLevel] = Query(None),
    min_relevance_score: Optional[int] = Query(None, ge=0, le=100),
    affected_instrument: Optional[str] = Query(None),
    affected_currency: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_expired: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Get market news with filtering options."""
    query = select(MarketNews)

    # Filter by category
    if category:
        query = query.where(MarketNews.category == category)

    # Filter by source
    if source_type:
        query = query.where(MarketNews.source_type == source_type)
    if source_name:
        query = query.where(MarketNews.source_name.ilike(f"%{source_name}%"))

    # Filter by relevance
    if relevance_level:
        query = query.where(MarketNews.relevance_level == relevance_level)
    if min_relevance_score is not None:
        query = query.where(MarketNews.relevance_score >= min_relevance_score)

    # Filter by affected instruments/currencies
    if affected_instrument:
        query = query.where(MarketNews.affected_instruments.contains([affected_instrument]))
    if affected_currency:
        query = query.where(MarketNews.affected_currencies.contains([affected_currency]))

    # Filter by date range
    if start_date:
        query = query.where(MarketNews.published_at >= start_date)
    if end_date:
        query = query.where(MarketNews.published_at <= end_date)

    # Filter by expiration (unless explicitly including expired)
    if not include_expired:
        now = datetime.utcnow()
        query = query.where(
            or_(MarketNews.expires_at.is_(None), MarketNews.expires_at > now)
        )

    # Order by most recent first
    query = query.order_by(desc(MarketNews.published_at))

    # Apply pagination
    news_items = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return news_items


@router.get("/news/{news_id}", response_model=MarketNewsResponse)
async def get_market_news_item(news_id: int):
    """Get a specific market news item by ID."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        news_item = db.query(MarketNews).filter(MarketNews.id == news_id).first()
        if not news_item:
            raise HTTPException(status_code=404, detail="Market news item not found")
        return news_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@router.post("/news", response_model=MarketNewsResponse, status_code=status.HTTP_201_CREATED)
async def create_market_news(news: MarketNewsCreate):
    """Create a new market news item."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        # Check for duplicates based on content hash and source
        if news.content_hash:
            existing = (
                db.query(MarketNews)
                .filter(
                    and_(
                        MarketNews.content_hash == news.content_hash,
                        MarketNews.source_name == news.source_name,
                    )
                )
                .first()
            )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Duplicate news item detected",
            )

        db_news = MarketNews(**news.dict())
        db.add(db_news)
        db.commit()
        db.refresh(db_news)
        return db_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

# Economic Indicators Endpoints
@router.get("/indicators", response_model=List[EconomicIndicatorResponse])
async def get_economic_indicators(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = Query(None),
    indicator_type: Optional[str] = Query(None),
    impact_level: Optional[RelevanceLevel] = Query(None),
    min_impact_score: Optional[int] = Query(None, ge=0, le=100),
    affected_instrument: Optional[str] = Query(None),
    affected_currency: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_future: bool = Query(False),
):
    """Get economic indicators with filtering options."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        query = db.query(EconomicIndicator)

        # Filter by name
        if name:
            query = query.filter(EconomicIndicator.name.ilike(f"%{name}%"))

        # Filter by type
        if indicator_type:
            query = query.filter(EconomicIndicator.indicator_type == indicator_type)

        # Filter by impact
        if impact_level:
            query = query.filter(EconomicIndicator.impact_level == impact_level)
        if min_impact_score is not None:
            query = query.filter(EconomicIndicator.impact_score >= min_impact_score)

        # Filter by affected instruments/currencies
        if affected_instrument:
            query = query.filter(EconomicIndicator.affected_instruments.contains([affected_instrument]))
        if affected_currency:
            query = query.filter(EconomicIndicator.affected_currencies.contains([affected_currency]))

        # Filter by date range
        if start_date:
            query = query.filter(EconomicIndicator.release_date >= start_date)
        if end_date:
            query = query.filter(EconomicIndicator.release_date <= end_date)

        # Filter by future releases (unless explicitly including)
        if not include_future:
            now = datetime.utcnow()
            query = query.filter(EconomicIndicator.release_date <= now)

        # Order by most recent first
        query = query.order_by(desc(EconomicIndicator.release_date))

        # Apply pagination
        indicators = query.offset(skip).limit(limit).all()
        return indicators
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@router.get("/indicators/{indicator_id}", response_model=EconomicIndicatorResponse)
async def get_economic_indicator(indicator_id: int):
    """Get a specific economic indicator by ID."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        indicator = db.query(EconomicIndicator).filter(EconomicIndicator.id == indicator_id).first()
        if not indicator:
            raise HTTPException(status_code=404, detail="Economic indicator not found")
        return indicator
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

@router.post("/indicators", response_model=EconomicIndicatorResponse, status_code=status.HTTP_201_CREATED)
async def create_economic_indicator(indicator: EconomicIndicatorCreate):
    """Create a new economic indicator."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        # Check for duplicates
        existing = (
            db.query(EconomicIndicator)
            .filter(
                and_(
                    EconomicIndicator.name == indicator.name,
                    EconomicIndicator.release_date == indicator.release_date,
                    EconomicIndicator.source_name == indicator.source_name,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Duplicate economic indicator detected",
            )

        db_indicator = EconomicIndicator(**indicator.dict())
        db.add(db_indicator)
        db.commit()
        db.refresh(db_indicator)
        return db_indicator
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    

# Geopolitical Events Endpoints
@router.get("/events", response_model=List[GeopoliticalEventResponse])
async def get_geopolitical_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    impact_level: Optional[RelevanceLevel] = Query(None),
    min_impact_score: Optional[int] = Query(None, ge=0, le=100),
    affected_instrument: Optional[str] = Query(None),
    affected_currency: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    is_ongoing: Optional[bool] = Query(None),
):
    """Get geopolitical events with filtering options."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)

    # Filter by type
    if event_type:
        query = query.filter(GeopoliticalEvent.event_type == event_type)

    # Filter by region
    if region:
        query = query.filter(GeopoliticalEvent.region.ilike(f"%{region}%"))

    # Filter by impact
    if impact_level:
        query = query.filter(GeopoliticalEvent.impact_level == impact_level)
    if min_impact_score is not None:
        query = query.filter(GeopoliticalEvent.impact_score >= min_impact_score)

    # Filter by affected instruments/currencies
    if affected_instrument:
        query = query.filter(GeopoliticalEvent.affected_instruments.contains([affected_instrument]))
    if affected_currency:
        query = query.filter(GeopoliticalEvent.affected_currencies.contains([affected_currency]))

    # Filter by date range
    if start_date:
        query = query.filter(GeopoliticalEvent.start_date >= start_date)
    if end_date:
        query = query.filter(GeopoliticalEvent.start_date <= end_date)

    # Filter by ongoing status
    if is_ongoing is not None:
        query = query.filter(GeopoliticalEvent.is_ongoing == is_ongoing)

    # Order by start date (most recent first)
    query = query.order_by(desc(GeopoliticalEvent.start_date))

    # Apply pagination
    events = query.offset(skip).limit(limit).all()
    return events



@router.get("/events/{event_id}", response_model=GeopoliticalEventResponse)
async def get_geopolitical_event(event_id: int):
    """Get a specific geopolitical event by ID."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        event = db.query(GeopoliticalEvent).filter(GeopoliticalEvent.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Geopolitical event not found")
        return event
    finally:
        db.close()
    

@router.post("/events", response_model=GeopoliticalEventResponse, status_code=status.HTTP_201_CREATED)
async def create_geopolitical_event(event: GeopoliticalEventCreate):
    """Create a new geopolitical event."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        db_event = GeopoliticalEvent(**event.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    finally:
        db.close()
    

# Institutional Information Endpoints
@router.get("/institutional", response_model=List[InstitutionalInfoResponse])
async def get_institutional_info(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    institution: Optional[str] = Query(None),
    info_type: Optional[str] = Query(None),
    relevance_level: Optional[RelevanceLevel] = Query(None),
    min_relevance_score: Optional[int] = Query(None, ge=0, le=100),
    affected_instrument: Optional[str] = Query(None),
    affected_currency: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Get institutional information with filtering options."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    query = db.query(InstitutionalInfo)

    # Filter by institution
    if institution:
        query = query.filter(InstitutionalInfo.institution.ilike(f"%{institution}%"))

    # Filter by info type
    if info_type:
        query = query.filter(InstitutionalInfo.info_type == info_type)

    # Filter by relevance
    if relevance_level:
        query = query.filter(InstitutionalInfo.relevance_level == relevance_level)
    if min_relevance_score is not None:
        query = query.filter(InstitutionalInfo.relevance_score >= min_relevance_score)

    # Filter by affected instruments/currencies
    if affected_instrument:
        query = query.filter(InstitutionalInfo.affected_instruments.contains([affected_instrument]))
    if affected_currency:
        query = query.filter(InstitutionalInfo.affected_currencies.contains([affected_currency]))

    # Filter by date range
    if start_date:
        query = query.filter(InstitutionalInfo.published_at >= start_date)
    if end_date:
        query = query.filter(InstitutionalInfo.published_at <= end_date)

    # Order by most recent first
    query = query.order_by(desc(InstitutionalInfo.published_at))

    # Apply pagination
    info_items = query.offset(skip).limit(limit).all()
    return info_items
    

@router.get("/institutional/{info_id}", response_model=InstitutionalInfoResponse)
async def get_institutional_item(info_id: int):
    """Get a specific institutional information item by ID."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        info_item = db.query(InstitutionalInfo).filter(InstitutionalInfo.id == info_id).first()
        if not info_item:
            raise HTTPException(status_code=404, detail="Institutional information not found")
        return info_item
    finally:
        db.close()
    

@router.post("/institutional", response_model=InstitutionalInfoResponse, status_code=status.HTTP_201_CREATED)
async def create_institutional_info(info: InstitutionalInfoCreate):
    """Create a new institutional information item."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        db_info = InstitutionalInfo(**info.dict())
        db.add(db_info)
        db.commit()
        db.refresh(db_info)
        return db_info
    finally:
        db.close()
    

# Intelligence Cache Endpoints
@router.get("/cache/{cache_key}")
async def get_intelligence_cache(cache_key: str):
    """Get cached intelligence data."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        cache_item = (
            db.query(IntelligenceCache)
            .filter(
                and_(
                    IntelligenceCache.cache_key == cache_key,
                    IntelligenceCache.is_valid == True,
                    IntelligenceCache.expires_at > datetime.utcnow(),
                )
            )
            .first()
        )
        if not cache_item:
            raise HTTPException(status_code=404, detail="Cache entry not found or expired")
        return {"data": cache_item.cached_data, "expires_at": cache_item.expires_at}
    finally:
        db.close()
    

@router.post("/cache", status_code=status.HTTP_201_CREATED)
async def set_intelligence_cache(
    cache_key: str = Query(...),
    cache_type: str = Query(...),
    data: dict = {},
    ttl_hours: int = Query(24, ge=1, le=8760),  # 1 hour to 1 year
):
    """Set intelligence cache data."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        # Check if cache entry already exists
        existing = db.query(IntelligenceCache).filter(IntelligenceCache.cache_key == cache_key).first()
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        if existing:
            # Update existing entry
            existing.cache_type = cache_type
            existing.cached_data = data
            existing.expires_at = expires_at
            existing.is_valid = True
            existing.created_at = datetime.utcnow()
        else:
            # Create new entry
            cache_entry = IntelligenceCache(
                cache_key=cache_key,
                cache_type=cache_type,
                cached_data=data,
                expires_at=expires_at,
            )
            db.add(cache_entry)

        db.commit()
        return {"message": "Cache entry saved successfully"}
    finally:
        db.close()
    

# Summary and Analytics Endpoints
@router.get("/summary")
async def get_intelligence_summary(
    hours: int = Query(24, ge=1, le=168),  # Last 1 hour to 1 week
):
    """Get a summary of recent intelligence activity."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Count news items
        news_count = (
            db.query(MarketNews)
            .filter(MarketNews.received_at >= since)
            .count()
        )

        # Count indicators
        indicators_count = (
            db.query(EconomicIndicator)
            .filter(EconomicIndicator.received_at >= since)
            .count()
        )

        # Count events
        events_count = (
            db.query(GeopoliticalEvent)
            .filter(GeopoliticalEvent.received_at >= since)
            .count()
        )

        # Count institutional info
        institutional_count = (
            db.query(InstitutionalInfo)
            .filter(InstitutionalInfo.received_at >= since)
            .count()
        )

        # Get high relevance items
        high_relevance_news = (
            db.query(MarketNews)
            .filter(
                and_(
                    MarketNews.received_at >= since,
                    or_(
                        MarketNews.relevance_level == RelevanceLevel.CRITICAL,
                        MarketNews.relevance_level == RelevanceLevel.HIGH,
                    )
                )
            )
            .count()
        )

        # Get by category
        news_by_category = {}
        for category in NewsCategory:
            count = (
                db.query(MarketNews)
                .filter(
                    and_(
                        MarketNews.received_at >= since,
                        MarketNews.category == category,
                    )
                )
                .count()
            )
            news_by_category[category.value] = count

        # Get by source type
        news_by_source_type = {}
        for source_type in NewsSourceType:
            count = (
                db.query(MarketNews)
                .filter(
                    and_(
                        MarketNews.received_at >= since,
                        MarketNews.source_type == source_type,
                    )
                )
                .count()
            )
            news_by_source_type[source_type.value] = count

        return {
            "period_hours": hours,
            "period_start": since.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "totals": {
                "news_items": news_count,
                "economic_indicators": indicators_count,
                "geopolitical_events": events_count,
                "institutional_info": institutional_count,
                "total_items": news_count + indicators_count + events_count + institutional_count,
            },
            "high_relevance_items": high_relevance_news,
            "news_by_category": news_by_category,
            "news_by_source_type": news_by_source_type,
        }
    finally:
        db.close()
    

# Health check endpoint
@router.get("/health")
async def intelligence_health_check():
    """Health check for intelligence service."""
    rt = _get_runtime()
    # Get database session from runtime data manager
    db = rt.data_manager.get_session(Domain.MARKET)
    try:
        # Simple query to check database connectivity
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "service": "market_intelligence",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Intelligence service unhealthy: {str(e)}",
        )
    finally:
        db.close()