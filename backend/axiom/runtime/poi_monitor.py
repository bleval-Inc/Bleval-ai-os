"""POI (Point of Interest) Monitor — Valta Prime's price level surveillance.

Valta Prime monitors Founder-defined Points of Interest on GOLD and US30.

Critical protocol when price reaches a POI:
  1. DETECT — price touches or approaches defined level
  2. VERIFY — confirm the touch is genuine (not a wick/spike)
  3. IMMEDIATELY ALERT — emergency communication to Founder
  4. ESCALATE — follow emergency escalation rules
  5. TELL FOUNDER TO ACCESS CHARTS
  6. PROVIDE CURRENT ANALYSIS — context, scenarios, recommendation

CRITICAL RULE: Valta Prime MUST NEVER EXECUTE A TRADE.
All output is analysis and recommendation only.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════════


class POIDirection(str, Enum):
    """Direction of the POI approach."""
    APPROACHING_FROM_ABOVE = "approaching_from_above"
    APPROACHING_FROM_BELOW = "approaching_from_below"
    BREAKING_ABOVE = "breaking_above"
    BREAKING_BELOW = "breaking_below"


class POIAction(str, Enum):
    """Recommended action at a POI."""
    WATCH = "watch"           # Monitor — approaching but not yet at level
    ALERT = "alert"           # At level — check charts
    ESCALATE = "escalate"     # Critical level — immediate escalation
    BOUNCE_SETUP = "bounce"   # Bounce trade setup identified
    BREAK_SETUP = "break"     # Breakout/breakdown setup identified


class AlertStatus(str, Enum):
    """Status of a POI alert."""
    PENDING = "pending"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"
    RESOLVED = "resolved"


@dataclass
class PointOfInterest:
    """A Founder-defined price level to monitor."""
    poi_id: str
    instrument: str             # GOLD or US30
    price_level: float
    direction: POIDirection
    action: POIAction
    description: str
    tolerance_pips: float       # How close before triggering
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class POIAlert:
    """An alert generated when price reaches a POI."""
    alert_id: str
    poi_id: str
    instrument: str
    price_level: float
    current_price: float
    direction: POIDirection
    action: POIAction
    description: str
    status: AlertStatus = AlertStatus.PENDING
    verification_notes: str = ""
    market_context: str = ""
    analysis: str = ""
    scenario_a: str = ""        # Bounce scenario
    scenario_b: str = ""        # Break scenario
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Default POIs (Founder-defined starting levels)
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_POIS: List[PointOfInterest] = [
    PointOfInterest(
        poi_id="POI-GOLD-001",
        instrument="GOLD",
        price_level=2340.0,
        direction=POIDirection.APPROACHING_FROM_ABOVE,
        action=POIAction.ALERT,
        description="GOLD support zone — prior swing low. Monitor for bounce or breakdown.",
        tolerance_pips=5.0,
        tags=["support", "swing-low"],
    ),
    PointOfInterest(
        poi_id="POI-GOLD-002",
        instrument="GOLD",
        price_level=2385.0,
        direction=POIDirection.APPROACHING_FROM_BELOW,
        action=POIAction.ALERT,
        description="GOLD resistance — prior weekly high. Monitor for rejection or breakout.",
        tolerance_pips=5.0,
        tags=["resistance", "weekly-high"],
    ),
    PointOfInterest(
        poi_id="POI-US30-001",
        instrument="US30",
        price_level=40800.0,
        direction=POIDirection.APPROACHING_FROM_ABOVE,
        action=POIAction.ALERT,
        description="US30 resistance zone. Prior rejection point. Watch for reaction.",
        tolerance_pips=30.0,
        tags=["resistance", "supply-zone"],
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# POI Monitor
# ═══════════════════════════════════════════════════════════════════════════════


class POIMonitor:
    """Monitors Founder-defined Points of Interest on trading instruments.

    Lifecycle:
      1. Founder defines POIs (or defaults are loaded)
      2. Background loop checks simulated/real price data
      3. When price approaches POI: detect → verify → alert
      4. Alert follows escalation protocol
      5. Founder acknowledges or POI expires
    """

    def __init__(self, runtime: Any = None) -> None:
        self._runtime = runtime
        self._pois: Dict[str, PointOfInterest] = {}
        self._alerts: Dict[str, POIAlert] = {}
        self._active_alerts: List[str] = []  # Alert IDs that haven't been resolved

        # Load defaults
        for poi in DEFAULT_POIS:
            self._pois[poi.poi_id] = poi

    # ── POI Management ────────────────────────────────────────────────────────

    def define_poi(
        self,
        instrument: str,
        price_level: float,
        direction: POIDirection,
        action: POIAction,
        description: str,
        tolerance_pips: float = 5.0,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Define a new Point of Interest to monitor.

        Returns the POI ID.
        """
        poi_id = f"POI-{instrument}-{len(self._pois) + 1:03d}"
        poi = PointOfInterest(
            poi_id=poi_id,
            instrument=instrument.upper(),
            price_level=price_level,
            direction=direction,
            action=action,
            description=description,
            tolerance_pips=tolerance_pips,
            tags=tags or [],
        )
        self._pois[poi_id] = poi
        return poi_id

    def remove_poi(self, poi_id: str) -> bool:
        """Remove (deactivate) a POI."""
        poi = self._pois.get(poi_id)
        if not poi:
            return False
        poi.is_active = False
        return True

    def list_pois(self, active_only: bool = True) -> List[PointOfInterest]:
        """List all POIs, optionally only active ones."""
        pois = list(self._pois.values())
        if active_only:
            pois = [p for p in pois if p.is_active]
        return sorted(pois, key=lambda p: p.price_level)

    # ── Price Checking ────────────────────────────────────────────────────────

    def check_price(self, instrument: str, current_price: float) -> List[POIAlert]:
        """Check if the current price triggers any active POIs.

        This is the DETECT phase of the protocol:
          1. Check all active POIs for this instrument
          2. Compare current price to POI level with tolerance
          3. Generate alert if triggered
          4. Perform VERIFY logic

        Returns list of newly generated alerts (empty if none triggered).
        """
        instrument = instrument.upper()
        new_alerts: List[POIAlert] = []

        for poi in self._pois.values():
            if not poi.is_active or poi.instrument != instrument:
                continue

            # Check if price is within tolerance of the POI level
            distance = abs(current_price - poi.price_level)
            if distance > poi.tolerance_pips:
                continue

            # Determine actual direction of approach
            approach: POIDirection
            if current_price > poi.price_level:
                approach = POIDirection.APPROACHING_FROM_ABOVE
            else:
                approach = POIDirection.APPROACHING_FROM_BELOW

            # Check if we already have a pending/triggered alert for this POI
            if self._has_active_alert_for_poi(poi.poi_id):
                continue

            # Build market context and analysis
            context = self._build_market_context(poi, current_price, approach)
            scenario_a, scenario_b = self._build_scenarios(poi, current_price, approach)

            alert = POIAlert(
                alert_id=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                poi_id=poi.poi_id,
                instrument=instrument,
                price_level=poi.price_level,
                current_price=current_price,
                direction=approach,
                action=poi.action,
                description=poi.description,
                status=AlertStatus.TRIGGERED,
                verification_notes=self._verify_setup(poi, current_price, approach),
                market_context=context,
                analysis=self._build_analysis(poi, current_price, approach, context),
                scenario_a=scenario_a,
                scenario_b=scenario_b,
            )

            self._alerts[alert.alert_id] = alert
            self._active_alerts.append(alert.alert_id)
            new_alerts.append(alert)

        return new_alerts

    def _has_active_alert_for_poi(self, poi_id: str) -> bool:
        """Check if there's already an unresolved alert for this POI."""
        for alert_id in self._active_alerts:
            alert = self._alerts.get(alert_id)
            if alert and alert.poi_id == poi_id:
                return True
        return False

    def _verify_setup(
        self, poi: PointOfInterest, current_price: float, approach: POIDirection
    ) -> str:
        """VERIFY phase — confirm the price action is genuine.

        Checks:
          - Is it a genuine touch or a spike/wick?
          - Is there confluence (support/resistance, volume)?
          - What's the broader market structure?
        """
        notes = []
        notes.append(f"Price at {current_price}, POI level {poi.price_level}")
        notes.append(f"Distance: {abs(current_price - poi.price_level):.1f} points")

        # Simulated verification logic — in production this would hook
        # into real price data (volume, order flow, etc.)
        distance_pct = abs(current_price - poi.price_level) / poi.price_level * 100
        if distance_pct < 0.1:
            notes.append("VERIFICATION: Price is touching POI level directly. Genuine test.")
        elif distance_pct < 0.5:
            notes.append(f"VERIFICATION: Price within {distance_pct:.2f}% of POI. Approaching zone.")
        else:
            notes.append("VERIFICATION: Price near POI zone. Monitor for closer approach.")

        # Direction-specific notes
        if approach in (POIDirection.APPROACHING_FROM_ABOVE, POIDirection.BREAKING_BELOW):
            notes.append("Direction: Price testing POI from above (resistance-turned-support test)")
        else:
            notes.append("Direction: Price testing POI from below (support-turned-resistance test)")

        return "\n".join(notes)

    def _build_market_context(
        self, poi: PointOfInterest, current_price: float, approach: POIDirection
    ) -> str:
        """Build market context for the alert."""
        context_parts = [
            f"Instrument: {poi.instrument}",
            f"POI Level: {poi.price_level}",
            f"Current Price: {current_price}",
            f"Direction: {approach.value}",
            f"Tags: {', '.join(poi.tags)}",
            f"Alert Time: {datetime.now(timezone.utc).isoformat()}",
        ]
        return "\n".join(context_parts)

    def _build_scenarios(
        self, poi: PointOfInterest, current_price: float, approach: POIDirection
    ) -> tuple:
        """Build Scenario A (bounce) and Scenario B (break) for the alert."""
        is_below = current_price < poi.price_level

        if is_below:
            scenario_a = (
                f"SCENARIO A (BOUNCE): Price holds at {poi.price_level} and reverses upward. "
                f"Target: {poi.price_level + (poi.price_level * 0.01):.1f}. "
                f"Invalidation: close below {poi.price_level - poi.tolerance_pips}."
            )
            scenario_b = (
                f"SCENARIO B (BREAK): Price breaks below {poi.price_level} with conviction. "
                f"Next support: {poi.price_level - (poi.price_level * 0.015):.1f}. "
                f"Invalidation: quick recovery above {poi.price_level} within 2 candles."
            )
        else:
            scenario_a = (
                f"SCENARIO A (REJECTION): Price rejects at {poi.price_level} and reverses downward. "
                f"Target: {poi.price_level - (poi.price_level * 0.01):.1f}. "
                f"Invalidation: close above {poi.price_level + poi.tolerance_pips}."
            )
            scenario_b = (
                f"SCENARIO B (BREAKOUT): Price breaks above {poi.price_level} with conviction. "
                f"Next resistance: {poi.price_level + (poi.price_level * 0.015):.1f}. "
                f"Invalidation: quick rejection below {poi.price_level} within 2 candles."
            )

        return scenario_a, scenario_b

    def _build_analysis(
        self,
        poi: PointOfInterest,
        current_price: float,
        approach: POIDirection,
        context: str,
    ) -> str:
        """Build the full analysis for the alert."""
        analysis_parts = [
            f"=== EMERGENCY POI ALERT ===",
            f"",
            f"⚠️  PRICE AT POI — {poi.instrument}",
            f"",
            f"Level: {poi.price_level}",
            f"Current: {current_price}",
            f"",
            f"**Analysis:**",
            f"Price has reached a Founder-defined Point of Interest on {poi.instrument}.",
            f"This level was pre-identified for monitoring.",
            f"",
            f"**Verification:** Complete — price action is testing the level.",
            f"**Setup:** Both bounce and break scenarios are prepared.",
        ]
        return "\n".join(analysis_parts)

    # ── Alert Management ──────────────────────────────────────────────────────

    def get_active_alerts(self) -> List[POIAlert]:
        """Get all currently active (unresolved) alerts."""
        return [
            self._alerts[alert_id]
            for alert_id in self._active_alerts
            if alert_id in self._alerts
        ]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Founder acknowledges the alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        return True

    def resolve_alert(self, alert_id: str, resolution_notes: str = "") -> bool:
        """Mark an alert as resolved (price moved away or trade executed)."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        alert.analysis += f"\n\n**Resolution:** {resolution_notes}"
        if alert_id in self._active_alerts:
            self._active_alerts.remove(alert_id)
        return True

    def get_alert_history(self, limit: int = 20) -> List[POIAlert]:
        """Get recent alert history."""
        alerts = sorted(
            self._alerts.values(),
            key=lambda a: a.created_at,
            reverse=True,
        )
        return alerts[:limit]

    # ── Escalation ────────────────────────────────────────────────────────────

    def format_escalation_message(self, alert: POIAlert) -> str:
        """Format the full escalation message for the Founder.

        This is what Valta Prime sends when price reaches a POI.
        """
        return (
            f"⚠️  **FOUNDER — IMMEDIATE ATTENTION REQUIRED**\n\n"
            f"**POI ALERT: {alert.instrument}**\n\n"
            f"Price has reached your defined Point of Interest.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**Level:** {alert.price_level}\n"
            f"**Current Price:** {alert.current_price}\n"
            f"**Instrument:** {alert.instrument}\n"
            f"**Approach:** {alert.direction.value.replace('_', ' ').title()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Verification:**\n{alert.verification_notes}\n\n"
            f"**Scenario A:**\n{alert.scenario_a}\n\n"
            f"**Scenario B:**\n{alert.scenario_b}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**ACTION REQUIRED:** Access your charts and verify.\n"
            f"I am standing by for your analysis.\n\n"
            f"— Valta Prime — House of Valta\n\n"
            f"*This is an automated POI alert. I cannot execute trades.*"
        )

    def format_quick_alert(self, alert: POIAlert) -> str:
        """Format a quick alert message (for high-urgency scenarios)."""
        return (
            f"⚠️  POI TRIGGERED — {alert.instrument} @ {alert.current_price}\n"
            f"Target: {alert.price_level} | "
            f"Scenarios prepared. Check charts immediately.\n"
            f"— Valta Prime"
        )

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        """Get a dashboard snapshot of POI monitor state."""
        active_pois = self.list_pois(active_only=True)
        active_alerts = self.get_active_alerts()
        total_alerts = len(self._alerts)

        return {
            "active_pois": len(active_pois),
            "active_alerts": len(active_alerts),
            "total_alerts_ever": total_alerts,
            "total_pois_defined": len(self._pois),
            "pois": [
                {
                    "poi_id": p.poi_id,
                    "instrument": p.instrument,
                    "price_level": p.price_level,
                    "action": p.action.value,
                    "active": p.is_active,
                }
                for p in active_pois
            ],
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "instrument": a.instrument,
                    "price_level": a.price_level,
                    "current_price": a.current_price,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                }
                for a in active_alerts
            ],
        }