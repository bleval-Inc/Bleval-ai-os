"""Fundamental Reporting API Routes — Valta Prime Session Intelligence.
Provides access to Valta Prime's automated fundamental analysis briefings
for Asian, London, and New York sessions.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from axiom.runtime.lifecycle import AxiomRuntime

router = APIRouter()


class SessionBriefingResponse(BaseModel):
    """Response model for session briefing."""
    session: str
    session_name: str
    date: str
    generated_at: str
    report_type: str
    executive_summary: str
    gold: Dict[str, Any]
    us30: Dict[str, Any]
    market_events_to_watch: List[Dict[str, Any]]
    valta_prime_assessment: str
    data_sources: Dict[str, int]


class LatestReportResponse(BaseModel):
    """Response model for latest report."""
    session: Optional[str] = None
    session_name: Optional[str] = None
    date: Optional[str] = None
    generated_at: Optional[str] = None
    report_type: Optional[str] = None
    executive_summary: Optional[str] = None
    gold: Optional[Dict[str, Any]] = None
    us30: Optional[Dict[str, Any]] = None
    market_events_to_watch: Optional[List[Dict[str, Any]]] = None
    valta_prime_assessment: Optional[str] = None
    data_sources: Optional[Dict[str, int]] = None


class ReportStatusResponse(BaseModel):
    """Response model for report status."""
    engine: str
    cached_reports: int
    last_report_times: Dict[str, str]


@router.get(
    "/fundamental-reporting/session/{session}",
    response_model=SessionBriefingResponse,
    summary="Get fundamental analysis briefing for a specific trading session",
    description="Generate or retrieve a fundamental analysis briefing for Asian, London, or New York session",
)
async def get_session_briefing(
    session: str,
    target_time: Optional[str] = Query(None, description="ISO format timestamp for report generation (defaults to now)"),
) -> SessionBriefingResponse:
    """Get fundamental analysis briefing for a specific trading session."""
    from axiom.api.routes import get_runtime
    runtime = get_runtime()
    try:
        # Validate session
        try:
            session_enum = session.lower()
            if session_enum not in ["asian", "london", "new_york"]:
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session. Must be 'asian', 'london', or 'new_york'"
            )

        # Parse target_time if provided
        parsed_target_time = None
        if target_time:
            try:
                parsed_target_time = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid target_time format. Use ISO format (e.g., 2024-01-15T14:30:00Z)"
                )

        # Generate the session briefing
        report = await runtime.fundamental_reporting.generate_session_briefing(
            session=session_enum,
            target_time=parsed_target_time
        )

        return SessionBriefingResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate session briefing: {str(e)}"
        )


@router.get(
    "/fundamental-reporting/latest",
    response_model=LatestReportResponse,
    summary="Get the latest fundamental analysis briefing",
    description="Retrieve the most recently generated fundamental analysis briefing",
)
async def get_latest_report(
    session: Optional[str] = Query(None, description="Filter by session: 'asian', 'london', or 'new_york'"),
) -> LatestReportResponse:
    """Get the latest fundamental analysis briefing."""
    from axiom.api.routes import get_runtime
    runtime = get_runtime()
    try:
        # Validate session if provided
        if session:
            try:
                session_enum = session.lower()
                if session_enum not in ["asian", "london", "new_york"]:
                    raise ValueError()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session. Must be 'asian', 'london', or 'new_york'"
                )
            session_enum = session.lower()
        else:
            session_enum = None

        # Get the latest report
        report = await runtime.fundamental_reporting.get_latest_report(
            session=session_enum
        )

        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reports available"
            )

        return LatestReportResponse(**report)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve latest report: {str(e)}"
        )


@router.get(
    "/fundamental-reporting/status",
    response_model=ReportStatusResponse,
    summary="Get fundamental reporting engine status",
    description="Get status information about the fundamental reporting engine",
)
async def get_reporting_status(
) -> ReportStatusResponse:
    """Get fundamental reporting engine status."""
    from axiom.api.routes import get_runtime
    runtime = get_runtime()
    try:
        if not runtime.fundamental_reporting:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Fundamental reporting engine not available"
            )

        status_info = {
            "engine": "operational",
            "cached_reports": len(runtime.fundamental_reporting._reports_cache),
            "last_report_times": {
                session.value: time.isoformat()
                for session, time in runtime.fundamental_reporting._last_report_times.items()
            }
        }

        return ReportStatusResponse(**status_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reporting status: {str(e)}"
        )


@router.post(
    "/fundamental-reporting/clear-cache",
    summary="Clear old reports from cache",
    description="Clear cached reports older than specified hours",
)
async def clear_report_cache(
    older_than_hours: int = Query(24, ge=1, le=168, description="Hours (1-168, default 24)"),
) -> Dict[str, Any]:
    """Clear old reports from cache."""
    from axiom.api.routes import get_runtime
    runtime = get_runtime()
    try:
        if not runtime.fundamental_reporting:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Fundamental reporting engine not available"
            )

        runtime.fundamental_reporting.clear_cache(older_than_hours=older_than_hours)

        return {
            "message": f"Cleared reports older than {older_than_hours} hours",
            "remaining_cached_reports": len(runtime.fundamental_reporting._reports_cache)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear report cache: {str(e)}"
        )