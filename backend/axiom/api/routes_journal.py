"""Journal API Routes — Trading Journal for House of Valta.
Handles voice-driven trade journal entry creation, retrieval, and analytics.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from axiom.data.models.journal import (
    JournalEntry,
    JournalEntryType,
    TradingSession,
    TradeResult,
    APlusClassification,
    JournalTemplate,
)


# Router — mounted in main.py
router = APIRouter(prefix="/api/v1/journal")


# In-memory reference to the runtime (set during app startup)
_runtime = None


def set_runtime(runtime: Any) -> None:
    """Inject runtime reference into the API layer."""
    global _runtime
    _runtime = runtime


def _get_runtime():
    if _runtime is None:
        raise HTTPException(status_code=503, detail="Runtime not initialised")
    return _runtime


# ══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ══════════════════════════════════════════════════════════════════════════════


class JournalEntryCreateRequest(BaseModel):
    """Request to create a new journal entry from voice dictation."""

    # Voice-driven content
    raw_transcription: str = Field(..., description="Original voice dictation from trader")
    title: Optional[str] = Field(None, description="Optional title for the journal entry")

    # Timing
    date: Optional[str] = Field(None, description="Date of the trade (ISO format, defaults to today)")
    session: Optional[TradingSession] = Field(None, description="Trading session")

    # Instrument details (can be extracted from voice or provided)
    instrument_name: Optional[str] = Field(None, description="Trading instrument (e.g., XAUUSD, US30)")
    instrument_type: Optional[str] = Field(None, description="Instrument type")

    # Entry type
    entry_type: JournalEntryType = Field(JournalEntryType.TRADE_JOURNAL, description="Type of journal entry")


class JournalEntryResponse(BaseModel):
    """Response model for journal entry data."""

    id: int
    uuid: str
    entry_type: JournalEntryType
    title: str
    date: str
    session: Optional[TradingSession]
    created_at: str
    updated_at: str

    # Trade identification
    symbol_id: Optional[int]
    mt5_deal_id: Optional[int]
    mt5_order_id: Optional[int]

    # Instrument details
    instrument_name: Optional[str]
    instrument_type: Optional[str]

    # Content
    raw_transcription: str
    structured_notes: Optional[str]

    # Market analysis
    market_analysis: Optional[str]
    higher_timeframe_bias: Optional[str]
    market_breakdown: Optional[str]

    # Trade setup and execution
    setup_description: Optional[str]
    entry_reasoning: Optional[str]
    entry_price: Optional[float]
    entry_time: Optional[str]

    # Risk management
    stop_loss: Optional[float]
    stop_loss_reason: Optional[str]
    target_price: Optional[float]
    target_reason: Optional[str]

    # Trade management
    lot_size: Optional[float]
    trade_direction: Optional[str]

    # Trade outcome
    exit_price: Optional[float]
    exit_time: Optional[str]
    result: Optional[TradeResult]
    pnl: Optional[float]
    pnl_percent: Optional[float]

    # Invalidation and trade management
    invalidation_criteria: Optional[str]
    trade_management_notes: Optional[str]
    actual_exit_reason: Optional[str]

    # Psychology and behavioral
    psychology_state: Optional[str]
    mistakes_made: Optional[str]
    what_went_well: Optional[str]
    lessons_learned: Optional[str]

    # Strategy classification
    a_plus_classification: Optional[APlusClassification]
    setup_score: Optional[int]

    # Metadata
    tags: List[str]
    custom_fields: Dict[str, Any]


class JournalAnalyticsResponse(BaseModel):
    """Response model for journal analytics."""

    period_start: str
    period_end: str
    period_type: str

    # Performance metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Financial metrics
    total_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    expectancy: float

    # Risk metrics
    max_drawdown: float
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Setup quality
    a_plus_setups: int
    average_setup_score: float

    # Session breakdown
    asian_session_trades: int
    london_session_trades: int
    new_york_session_trades: int

    # Instrument performance
    instrument_performance: Dict[str, Any]

    # Psychology insights
    common_mistakes: List[str]
    psychological_patterns: List[str]

    generated_at: str
    source_trade_count: int


class VoiceCommandJournalRequest(BaseModel):
    """Request for processing voice commands related to journal operations."""

    transcript: str
    executive: str = "valta_prime"
    wake_word: str
    confidence: float = 1.0


# ══════════════════════════════════════════════════════════════════════════════
# Journal Entry Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/", response_model=JournalEntryResponse)
async def create_journal_entry(request: JournalEntryCreateRequest):
    """Create a new journal entry from voice dictation.

    This is the primary endpoint for voice-driven journal entry creation.
    The system processes the raw transcription and structures the information
    for storage and later analysis.
    """
    rt = _get_runtime()

    # Parse date or use today
    from datetime import datetime
    entry_date = datetime.fromisoformat(request.date) if request.date else datetime.now()

    # Create journal entry
    journal_entry = JournalEntry(
        title=request.title or f"Trade Journal - {entry_date.strftime('%Y-%m-%d')}",
        entry_type=request.entry_type,
        date=entry_date,
        session=request.session,
        raw_transcription=request.raw_transcription,
        structured_notes=request.raw_transcription,  # Initially same as raw, will be processed later
        instrument_name=request.instrument_name,
        instrument_type=request.instrument_type,
    )

    # Save to database
    if rt.data_manager:
        await rt.data_manager.create(journal_entry)
        await rt.data_manager.commit()

    return JournalEntryResponse(
        id=journal_entry.id,
        uuid=journal_entry.uuid,
        entry_type=journal_entry.entry_type,
        title=journal_entry.title,
        date=journal_entry.date.isoformat(),
        session=journal_entry.session,
        created_at=journal_entry.created_at.isoformat(),
        updated_at=journal_entry.updated_at.isoformat(),
        symbol_id=journal_entry.symbol_id,
        mt5_deal_id=journal_entry.mt5_deal_id,
        mt5_order_id=journal_entry.mt5_order_id,
        instrument_name=journal_entry.instrument_name,
        instrument_type=journal_entry.instrument_type,
        raw_transcription=journal_entry.raw_transcription,
        structured_notes=journal_entry.structured_notes,
        market_analysis=journal_entry.market_analysis,
        higher_timeframe_bias=journal_entry.higher_timeframe_bias,
        market_breakdown=journal_entry.market_breakdown,
        setup_description=journal_entry.setup_description,
        entry_reasoning=journal_entry.entry_reasoning,
        entry_price=float(journal_entry.entry_price) if journal_entry.entry_price else None,
        entry_time=journal_entry.entry_time.isoformat() if journal_entry.entry_time else None,
        stop_loss=float(journal_entry.stop_loss) if journal_entry.stop_loss else None,
        stop_loss_reason=journal_entry.stop_loss_reason,
        target_price=float(journal_entry.target_price) if journal_entry.target_price else None,
        target_reason=journal_entry.target_reason,
        lot_size=float(journal_entry.lot_size) if journal_entry.lot_size else None,
        trade_direction=journal_entry.trade_direction,
        exit_price=float(journal_entry.exit_price) if journal_entry.exit_price else None,
        exit_time=journal_entry.exit_time.isoformat() if journal_entry.exit_time else None,
        result=journal_entry.result,
        pnl=float(journal_entry.pnl) if journal_entry.pnl else None,
        pnl_percent=float(journal_entry.pnl_percent) if journal_entry.pnl_percent else None,
        invalidation_criteria=journal_entry.invalidation_criteria,
        trade_management_notes=journal_entry.trade_management_notes,
        actual_exit_reason=journal_entry.actual_exit_reason,
        psychology_state=journal_entry.psychology_state,
        mistakes_made=journal_entry.mistakes_made,
        what_went_well=journal_entry.what_went_well,
        lessons_learned=journal_entry.lessons_learned,
        a_plus_classification=journal_entry.a_plus_classification,
        setup_score=journal_entry.setup_score,
        tags=journal_entry.tags,
        custom_fields=journal_entry.custom_fields,
    )


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(entry_id: int):
    """Retrieve a specific journal entry by ID."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    journal_entry = await rt.data_manager.get_by_id(JournalEntry, entry_id)
    if not journal_entry:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    return JournalEntryResponse(
        id=journal_entry.id,
        uuid=journal_entry.uuid,
        entry_type=journal_entry.entry_type,
        title=journal_entry.title,
        date=journal_entry.date.isoformat(),
        session=journal_entry.session,
        created_at=journal_entry.created_at.isoformat(),
        updated_at=journal_entry.updated_at.isoformat(),
        symbol_id=journal_entry.symbol_id,
        mt5_deal_id=journal_entry.mt5_deal_id,
        mt5_order_id=journal_entry.mt5_order_id,
        instrument_name=journal_entry.instrument_name,
        instrument_type=journal_entry.instrument_type,
        raw_transcription=journal_entry.raw_transcription,
        structured_notes=journal_entry.structured_notes,
        market_analysis=journal_entry.market_analysis,
        higher_timeframe_bias=journal_entry.higher_timeframe_bias,
        market_breakdown=journal_entry.market_breakdown,
        setup_description=journal_entry.setup_description,
        entry_reasoning=journal_entry.entry_reasoning,
        entry_price=float(journal_entry.entry_price) if journal_entry.entry_price else None,
        entry_time=journal_entry.entry_time.isoformat() if journal_entry.entry_time else None,
        stop_loss=float(journal_entry.stop_loss) if journal_entry.stop_loss else None,
        stop_loss_reason=journal_entry.stop_loss_reason,
        target_price=float(journal_entry.target_price) if journal_entry.target_price else None,
        target_reason=journal_entry.target_reason,
        lot_size=float(journal_entry.lot_size) if journal_entry.lot_size else None,
        trade_direction=journal_entry.trade_direction,
        exit_price=float(journal_entry.exit_price) if journal_entry.exit_price else None,
        exit_time=journal_entry.exit_time.isoformat() if journal_entry.exit_time else None,
        result=journal_entry.result,
        pnl=float(journal_entry.pnl) if journal_entry.pnl else None,
        pnl_percent=float(journal_entry.pnl_percent) if journal_entry.pnl_percent else None,
        invalidation_criteria=journal_entry.invalidation_criteria,
        trade_management_notes=journal_entry.trade_management_notes,
        actual_exit_reason=journal_entry.actual_exit_reason,
        psychology_state=journal_entry.psychology_state,
        mistakes_made=journal_entry.mistakes_made,
        what_went_well=journal_entry.what_went_well,
        lessons_learned=journal_entry.lessons_learned,
        a_plus_classification=journal_entry.a_plus_classification,
        setup_score=journal_entry.setup_score,
        tags=journal_entry.tags,
        custom_fields=journal_entry.custom_fields,
    )


@router.get("/", response_model=List[JournalEntryResponse])
async def list_journal_entries(
    limit: int = Query(50, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    entry_type: Optional[JournalEntryType] = Query(None, description="Filter by entry type"),
    session: Optional[TradingSession] = Query(None, description="Filter by trading session"),
    instrument: Optional[str] = Query(None, description="Filter by instrument name"),
    result: Optional[TradeResult] = Query(None, description="Filter by trade result"),
    a_plus_only: bool = Query(False, description="Show only A+ classified setups"),
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
):
    """List journal entries with optional filtering."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    # Build filters
    filters = {}
    if entry_type:
        filters["entry_type"] = entry_type
    if session:
        filters["session"] = session
    if instrument:
        filters["instrument_name"] = instrument
    if result:
        filters["result"] = result
    if a_plus_only:
        filters["a_plus_classification__isnot"] = None  # Not null
    if start_date:
        filters["date__gte"] = start_date
    if end_date:
        filters["date__lte"] = end_date

    # Get entries
    journal_entries = await rt.data_manager.list(
        JournalEntry,
        limit=limit,
        offset=offset,
        order_by="date DESC",
        **filters
    )

    return [
        JournalEntryResponse(
            id=entry.id,
            uuid=entry.uuid,
            entry_type=entry.entry_type,
            title=entry.title,
            date=entry.date.isoformat(),
            session=entry.session,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
            symbol_id=entry.symbol_id,
            mt5_deal_id=entry.mt5_deal_id,
            mt5_order_id=entry.mt5_order_id,
            instrument_name=entry.instrument_name,
            instrument_type=entry.instrument_type,
            raw_transcription=entry.raw_transcription,
            structured_notes=entry.structured_notes,
            market_analysis=entry.market_analysis,
            higher_timeframe_bias=entry.higher_timeframe_bias,
            market_breakdown=entry.market_breakdown,
            setup_description=entry.setup_description,
            entry_reasoning=entry.entry_reasoning,
            entry_price=float(entry.entry_price) if entry.entry_price else None,
            entry_time=entry.entry_time.isoformat() if entry.entry_time else None,
            stop_loss=float(entry.stop_loss) if entry.stop_loss else None,
            stop_loss_reason=entry.stop_loss_reason,
            target_price=float(entry.target_price) if entry.target_price else None,
            target_reason=entry.target_reason,
            lot_size=float(entry.lot_size) if entry.lot_size else None,
            trade_direction=entry.trade_direction,
            exit_price=float(entry.exit_price) if entry.exit_price else None,
            exit_time=entry.exit_time.isoformat() if entry.exit_time else None,
            result=entry.result,
            pnl=float(entry.pnl) if entry.pnl else None,
            pnl_percent=float(entry.pnl_percent) if entry.pnl_percent else None,
            invalidation_criteria=entry.invalidation_criteria,
            trade_management_notes=entry.trade_management_notes,
            actual_exit_reason=entry.actual_exit_reason,
            psychology_state=entry.psychology_state,
            mistakes_made=entry.mistakes_made,
            what_went_well=entry.what_went_well,
            lessons_learned=entry.lessons_learned,
            a_plus_classification=entry.a_plus_classification,
            setup_score=entry.setup_score,
            tags=entry.tags,
            custom_fields=entry.custom_fields,
        )
        for entry in journal_entries
    ]


@router.put("/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(entry_id: int, request: JournalEntryCreateRequest):
    """Update an existing journal entry.

    Allows traders to review and edit their journal entries after initial creation.
    """
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    journal_entry = await rt.data_manager.get_by_id(JournalEntry, entry_id)
    if not journal_entry:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    # Update fields
    journal_entry.title = request.title or journal_entry.title
    journal_entry.entry_type = request.entry_type
    journal_entry.raw_transcription = request.raw_transcription
    journal_entry.structured_notes = request.raw_transcription  # Reset structured notes for reprocessing
    journal_entry.date = datetime.fromisoformat(request.date) if request.date else journal_entry.date
    journal_entry.session = request.session or journal_entry.session
    journal_entry.instrument_name = request.instrument_name or journal_entry.instrument_name
    journal_entry.instrument_type = request.instrument_type or journal_entry.instrument_type

    # Update timestamp
    journal_entry.updated_at = datetime.now()

    # Save changes
    await rt.data_manager.update(journal_entry)
    await rt.data_manager.commit()

    # Return updated entry (same structure as get)
    return await get_journal_entry(entry_id)


@router.delete("/{entry_id}")
async def delete_journal_entry(entry_id: int):
    """Delete a journal entry."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    journal_entry = await rt.data_manager.get_by_id(JournalEntry, entry_id)
    if not journal_entry:
        raise HTTPException(status_code=404, detail=f"Journal entry {entry_id} not found")

    await rt.data_manager.delete(journal_entry)
    await rt.data_manager.commit()

    return {"message": f"Journal entry {entry_id} deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Analytics Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/analytics/summary", response_model=JournalAnalyticsResponse)
async def get_journal_analytics(
    period_type: str = Query("monthly", description="Period type: daily, weekly, monthly"),
    period_start: Optional[str] = Query(None, description="Start date (ISO format)"),
    period_end: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """Get journal analytics and performance metrics for a specified period."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    # For now, return mock analytics - in a full implementation, this would
    # calculate real statistics from the journal entries
    from datetime import datetime, timedelta

    # Default to last 30 days if no period specified
    end_date = datetime.fromisoformat(period_end) if period_end else datetime.now()
    start_date = datetime.fromisoformat(period_start) if period_start else end_date - timedelta(days=30)

    # Mock analytics response
    return JournalAnalyticsResponse(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        period_type=period_type,
        total_trades=15,
        winning_trades=9,
        losing_trades=6,
        win_rate=60.0,
        total_pnl=2450.50,
        average_win=450.25,
        average_loss=-180.50,
        profit_factor=2.45,
        expectancy=125.33,
        max_drawdown=320.00,
        max_consecutive_wins=4,
        max_consecutive_losses=2,
        a_plus_setups=5,
        average_setup_score=82.5,
        asian_session_trades=3,
        london_session_trades=7,
        new_york_session_trades=5,
        instrument_performance={
            "XAUUSD": {"trades": 5, "win_rate": 80.0, "pnl": 1200.00},
            "US30": {"trades": 4, "win_rate": 50.0, "pnl": 800.50},
            "EURUSD": {"trades": 3, "win_rate": 66.7, "pnl": 300.00},
            "GBPUSD": {"trades": 3, "win_rate": 33.3, "pnl": 150.00}
        },
        common_mistakes=[
            "Moving stop loss to break even too early",
            "Not waiting for confirmation on higher timeframe",
            "Overtrading during low volatility periods"
        ],
        psychological_patterns=[
            "Tends to exit winners early during losing streaks",
            "Shows strong discipline when following predefined plans",
            "Emotional impact increases after consecutive losses"
        ],
        generated_at=datetime.now().isoformat(),
        source_trade_count=15
    )


@router.get("/analytics/a-plus-setups")
async def get_a_plus_setups(
    limit: int = Query(20, ge=1, le=50, description="Number of A+ setups to return"),
):
    """Get A+ classified trading setups for pattern analysis."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    # Get A+ classified entries
    a_plus_entries = await rt.data_manager.list(
        JournalEntry,
        limit=limit,
        order_by="date DESC",
        a_plus_classification__isnot=None  # Not null
    )

    return [
        {
            "id": entry.id,
            "uuid": entry.uuid,
            "date": entry.date.isoformat(),
            "instrument": entry.instrument_name,
            "setup_score": entry.setup_score,
            "pnl": float(entry.pnl) if entry.pnl else None,
            "raw_transcription_preview": entry.raw_transcription[:200] + "..." if len(entry.raw_transcription) > 200 else entry.raw_transcription,
            "lessons_learned": entry.lessons_learned,
        }
        for entry in a_plus_entries
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Voice Command Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/voice/process", response_model=JournalEntryResponse)
async def process_voice_journal_command(request: VoiceCommandJournalRequest):
    """Process voice commands specifically for journal operations.

    This endpoint handles Valta Prime voice commands for journal operations
    like starting a session journal, logging trades, etc.
    """
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    # Process the voice command to determine intent
    transcript_lower = request.transcript.lower()

    # Default response
    response_text = "Valta Prime ready for journal operations."
    action_taken = "voice_command_received"

    # Check for specific journal commands
    if "start" in transcript_lower and ("session" in transcript_lower or "journal" in transcript_lower):
        if "london" in transcript_lower:
            response_text = "Valta Prime: London session journal started. Ready to record trades."
            action_taken = "london_session_started"
        elif "new york" in transcript_lower or "ny" in transcript_lower:
            response_text = "Valta Prime: New York session journal started. Ready to record trades."
            action_taken = "new_york_session_started"
        elif "asian" in transcript_lower:
            response_text = "Valta Prime: Asian session journal started. Ready to record trades."
            action_taken = "asian_session_started"
        else:
            response_text = "Valta Prime: Trading journal started. Ready to record your session."
            action_taken = "journal_session_started"

    elif "log" in transcript_lower or "record" in transcript_lower:
        response_text = "Valta Prime: Trade logged. Please provide entry details."
        action_taken = "trade_log_prompted"

    elif "show" in transcript_lower or "display" in transcript_lower:
        if "performance" in transcript_lower or "stats" in transcript_lower:
            response_text = "Valta Prime: Retrieving your session performance metrics."
            action_taken = "performance_requested"
        else:
            response_text = "Valta Prime: Displaying recent journal entries."
            action_taken = "entries_displayed"

    elif "compare" in transcript_lower:
        response_text = "Valta Prime: Comparing this trade with your A+ setups."
        action_taken = "comparison_requested"

    # Create a basic journal entry for the voice command interaction
    journal_entry = JournalEntry(
        title=f"Voice Command - {request.executive.title()}",
        entry_type=JournalEntryType.TRADE_JOURNAL,
        date=datetime.now(),
        raw_transcription=request.transcript,
        structured_notes=f"Voice command processed: {request.transcript}",
        psychology_state="Voice command interaction",
        lessons_learned="Voice command processed for journal operations",
    )

    # Save to database
    await rt.data_manager.create(journal_entry)
    await rt.data_manager.commit()

    return JournalEntryResponse(
        id=journal_entry.id,
        uuid=journal_entry.uuid,
        entry_type=journal_entry.entry_type,
        title=journal_entry.title,
        date=journal_entry.date.isoformat(),
        session=journal_entry.session,
        created_at=journal_entry.created_at.isoformat(),
        updated_at=journal_entry.updated_at.isoformat(),
        symbol_id=journal_entry.symbol_id,
        mt5_deal_id=journal_entry.mt5_deal_id,
        mt5_order_id=journal_entry.mt5_order_id,
        instrument_name=journal_entry.instrument_name,
        instrument_type=journal_entry.instrument_type,
        raw_transcription=journal_entry.raw_transcription,
        structured_notes=journal_entry.structured_notes,
        market_analysis=journal_entry.market_analysis,
        higher_timeframe_bias=journal_entry.higher_timeframe_bias,
        market_breakdown=journal_entry.market_breakdown,
        setup_description=journal_entry.setup_description,
        entry_reasoning=journal_entry.entry_reasoning,
        entry_price=float(journal_entry.entry_price) if journal_entry.entry_price else None,
        entry_time=journal_entry.entry_time.isoformat() if journal_entry.entry_time else None,
        stop_loss=float(journal_entry.stop_loss) if journal_entry.stop_loss else None,
        stop_loss_reason=journal_entry.stop_loss_reason,
        target_price=float(journal_entry.target_price) if journal_entry.target_price else None,
        target_reason=journal_entry.target_reason,
        lot_size=float(journal_entry.lot_size) if journal_entry.lot_size else None,
        trade_direction=journal_entry.trade_direction,
        exit_price=float(journal_entry.exit_price) if journal_entry.exit_price else None,
        exit_time=journal_entry.exit_time.isoformat() if journal_entry.exit_time else None,
        result=journal_entry.result,
        pnl=float(journal_entry.pnl) if journal_entry.pnl else None,
        pnl_percent=float(journal_entry.pnl_percent) if journal_entry.pnl_percent else None,
        invalidation_criteria=journal_entry.invalidation_criteria,
        trade_management_notes=journal_entry.trade_management_notes,
        actual_exit_reason=journal_entry.actual_exit_reason,
        psychology_state=journal_entry.psychology_state,
        mistakes_made=journal_entry.mistakes_made,
        what_went_well=journal_entry.what_went_well,
        lessons_learned=journal_entry.lessons_learned,
        a_plus_classification=journal_entry.a_plus_classification,
        setup_score=journal_entry.setup_score,
        tags=journal_entry.tags,
        custom_fields=journal_entry.custom_fields,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Template Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/templates")
async def list_journal_templates():
    """List available journal templates."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    templates = await rt.data_manager.list(JournalTemplate, is_active=True)
    return [
        {
            "id": template.id,
            "uuid": template.uuid,
            "name": template.name,
            "description": template.description,
            "entry_type": template.entry_type.value,
            "voice_triggers": template.voice_triggers,
            "is_active": template.is_active,
        }
        for template in templates
    ]


@router.post("/templates/{template_id}/use")
async def use_journal_template(template_id: int):
    """Create a new journal entry using a specific template."""
    rt = _get_runtime()

    if not rt.data_manager:
        raise HTTPException(status_code=503, detail="Data manager not available")

    template = await rt.data_manager.get_by_id(JournalTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Journal template {template_id} not found")

    # Create journal entry from template
    journal_entry = JournalEntry(
        title=f"New {template.name}",
        entry_type=template.entry_type,
        date=datetime.now(),
        structured_notes=f"Created from template: {template.name}",
        tags=template.tags.copy() if template.tags else [],
    )

    await rt.data_manager.create(journal_entry)
    await rt.data_manager.commit()

    return {"message": f"Journal entry created from template '{template.name}'", "entry_id": journal_entry.id}


# ══════════════════════════════════════════════════════════════════════════════
# Health Check
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/health")
async def journal_health():
    """Health check for journal service."""
    rt = _get_runtime()

    if not rt.data_manager:
        return {"status": "unhealthy", "service": "journal", "error": "Data manager not available"}

    try:
        # Simple query to test connectivity
        count = await rt.data_manager.count(JournalEntry)
        return {
            "status": "healthy",
            "service": "journal",
            "total_entries": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "journal",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }