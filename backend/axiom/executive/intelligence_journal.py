"""Valta Prime Journal Intelligence Extension.
Provides specialized intelligence capabilities for analyzing trading journal data
to identify patterns, recurring errors, and strategy insights.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from axiom.executive.intelligence import ExecutiveIntelligence
from axiom.models.journal import (
    JournalEntry,
    JournalEntryType,
    TradingSession,
    TradeResult,
    APlusClassification,
)
from axiom.data.manager import DataManager


class ValtaPrimeJournalIntelligence:
    """Specialized intelligence for Valta Prime's trading journal analysis."""

    def __init__(self, data_manager: DataManager, base_intelligence: ExecutiveIntelligence):
        self.data_manager = data_manager
        self.base_intelligence = base_intelligence

    async def analyze_journal_patterns(
        self,
        days_back: int = 30,
        session: Optional[TradingSession] = None,
        instrument: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze journal entries to identify trading patterns and insights."""

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Build filters
        filters = {
            "date__gte": start_date,
            "date__lte": end_date,
        }
        if session:
            filters["session"] = session
        if instrument:
            filters["instrument_name"] = instrument

        # Get journal entries
        entries = await self.data_manager.list(
            JournalEntry,
            limit=1000,  # Reasonable limit for analysis
            order_by="date DESC",
            **filters
        )

        if not entries:
            return {
                "analysis_period": f"{start_date.date()} to {end_date.date()}",
                "total_entries": 0,
                "message": "No journal entries found for the specified period",
            }

        # Analyze patterns
        analysis = {
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "total_entries": len(entries),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "filters_applied": {
                "session": session.value if session else None,
                "instrument": instrument,
                "days_back": days_back,
            },
            "performance_metrics": self._calculate_performance_metrics(entries),
            "setup_quality_analysis": self._analyze_setup_quality(entries),
            "psychological_patterns": self._analyze_psychological_patterns(entries),
            "session_analysis": self._analyze_session_performance(entries),
            "instrument_analysis": self._analyze_instrument_performance(entries),
            "common_mistakes": self._identify_common_mistakes(entries),
            "strengths_identified": self._identify_strengths(entries),
            "a_plus_analysis": self._analyze_a_plus_setups(entries),
            "recommendations": self._generate_recommendations(entries),
        }

        return analysis

    async def get_a_plus_patterns(
        self,
        days_back: int = 90,
        min_setup_score: int = 80,
    ) -> Dict[str, Any]:
        """Analyze A+ setups to identify winning patterns."""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        filters = {
            "date__gte": start_date,
            "date__lte": end_date,
            "a_plus_classification__isnot": None,
            "setup_score__gte": min_setup_score,
        }

        a_plus_entries = await self.data_manager.list(
            JournalEntry,
            limit=500,
            order_by="setup_score DESC, date DESC",
            **filters
        )

        if not a_plus_entries:
            return {
                "analysis_period": f"{start_date.date()} to {end_date.date()}",
                "total_a_plus_setups": 0,
                "message": "No A+ setups found meeting criteria",
            }

        # Analyze what makes these setups successful
        patterns = {
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "total_a_plus_setups": len(a_plus_entries),
            "min_setup_score": min_setup_score,
            "average_setup_score": sum(e.setup_score or 0 for e in a_plus_entries) / len(a_plus_entries),
            "average_pnl": sum(float(e.pnl or 0) for e in a_plus_entries) / len(a_plus_entries),
            "win_rate": len([e for e in a_plus_entries if e.result == TradeResult.WIN]) / len(a_plus_entries) * 100,
            "common_elements": self._extract_common_elements(a_plus_entries),
            "instrument_distribution": self._analyze_instrument_distribution(a_plus_entries),
            "session_distribution": self._analyze_session_distribution(a_plus_entries),
            "setup_characteristics": self._analyze_setup_characteristics(a_plus_entries),
            "risk_management_patterns": self._analyze_risk_management(a_plus_entries),
            "psychological_factors": self._analyze_psychological_factors(a_plus_entries),
            "entry_timing_patterns": self._analyze_entry_timing(a_plus_entries),
        }

        return patterns

    async def compare_trade_with_history(
        self,
        current_trade_data: Dict[str, Any],
        comparison_type: str = "setup_similarity",
    ) -> Dict[str, Any]:
        """Compare a current trade with historical journal entries."""

        # Extract key characteristics from current trade
        current_instrument = current_trade_data.get("instrument_name")
        current_setup = current_trade_data.get("setup_description", "")
        current_session = current_trade_data.get("session")
        current_timeframe_bias = current_trade_data.get("higher_timeframe_bias")

        # Find similar historical trades
        filters = {}
        if current_instrument:
            filters["instrument_name"] = current_instrument
        if current_session:
            filters["session"] = current_session

        # Get recent similar trades for comparison
        similar_trades = await self.data_manager.list(
            JournalEntry,
            limit=50,
            order_by="date DESC",
            **filters
        )

        comparison_results = {
            "current_trade_summary": {
                "instrument": current_instrument,
                "setup": current_setup[:100] + "..." if len(current_setup) > 100 else current_setup,
                "session": current_session.value if current_session else None,
                "timeframe_bias": current_timeframe_bias,
            },
            "similar_historical_trades": len(similar_trades),
            "comparison_type": comparison_type,
            "matches": [],
            "insights": [],
            "warnings": [],
        }

        if comparison_type == "setup_similarity":
            # Compare based on setup description similarity
            for trade in similar_trades:
                similarity_score = self._calculate_setup_similarity(
                    current_setup, trade.setup_description or ""
                )
                if similarity_score > 0.6:  # 60% similarity threshold
                    comparison_results["matches"].append({
                        "journal_entry_id": trade.id,
                        "date": trade.date.isoformat(),
                        "similarity_score": similarity_score,
                        "setup_preview": (trade.setup_description or "")[:150] + "...",
                        "result": trade.result.value if trade.result else None,
                        "pnl": float(trade.pnl) if trade.pnl else None,
                        "setup_score": trade.setup_score,
                        "lessons_learned": trade.lessons_learned,
                    })

            # Sort by similarity score
            comparison_results["matches"].sort(key=lambda x: x["similarity_score"], reverse=True)
            comparison_results["matches"] = comparison_results["matches"][:10]  # Top 10 matches

            # Generate insights from matches
            if comparison_results["matches"]:
                winning_matches = [m for m in comparison_results["matches"] if m["result"] == "win"]
                losing_matches = [m for m in comparison_results["matches"] if m["result"] == "loss"]

                if winning_matches:
                    avg_win_pnl = sum(m["pnl"] or 0 for m in winning_matches) / len(winning_matches)
                    comparison_results["insights"].append(
                        f"Similar setups have yielded an average profit of ${avg_win_pnl:.2f} "
                        f"based on {len(winning_matches)} historical winning trades"
                    )

                if losing_matches:
                    avg_loss_pnl = sum(m["pnl"] or 0 for m in losing_matches) / len(losing_matches)
                    comparison_results["insights"].append(
                        f"Similar setups have resulted in an average loss of ${abs(avg_loss_pnl):.2f} "
                        f"based on {len(losing_matches)} historical losing trades"
                    )

                # Check for contradictory outcomes
                if winning_matches and losing_matches:
                    comparison_results["warnings"].append(
                        "Historical data shows mixed results for similar setups - "
                        "exercise caution and consider additional confirmation"
                    )

        elif comparison_type == "performance_comparison":
            # Compare performance metrics
            if similar_trades:
                historical_win_rate = len([t for t in similar_trades if t.result == TradeResult.WIN]) / len(similar_trades) * 100
                historical_avg_pnl = sum(float(t.pnl or 0) for t in similar_trades) / len(similar_trades)

                comparison_results["historical_baseline"] = {
                    "win_rate": historical_win_rate,
                    "average_pnl": historical_avg_pnl,
                    "total_trades": len(similar_trades),
                }

                # Add current trade performance if available
                if "pnl" in current_trade_data and "result" in current_trade_data:
                    comparison_results["current_performance"] = {
                        "pnl": current_trade_data["pnl"],
                        "result": current_trade_data["result"],
                    }

                    pnl_diff = current_trade_data["pnl"] - historical_avg_pnl
                    comparison_results["insights"].append(
                        f"Current trade P&L is ${pnl_diff:+.2f} vs historical average of ${historical_avg_pnl:.2f}"
                    )

        return comparison_results

    async def get_behavioral_insights(
        self,
        days_back: int = 60,
    ) -> Dict[str, Any]:
        """Extract behavioral and psychological insights from journal data."""

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        filters = {
            "date__gte": start_date,
            "date__lte": end_date,
        }

        entries = await self.data_manager.list(
            JournalEntry,
            limit=1000,
            order_by="date DESC",
            **filters
        )

        insights = {
            "analysis_period": f"{start_date.date()} to {end_date.date()}",
            "total_entries_analyzed": len(entries),
            "emotional_state_patterns": self._analyze_emotional_states(entries),
            "decision_timing_patterns": self._analyze_decision_timing(entries),
            "risk_tolerance_patterns": self._analyze_risk_tolerance(entries),
            "learning_progression": self._analyze_learning_progression(entries),
            "consistency_metrics": self._analyze_consistency(entries),
            "behavioral_recommendations": self._generate_behavioral_recommendations(entries),
        }

        return insights

    # Private helper methods for analysis

    def _calculate_performance_metrics(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Calculate basic performance metrics from journal entries."""
        if not entries:
            return {}

        total_trades = len([e for e in entries if e.entry_type == JournalEntryType.TRADE_JOURNAL and e.result])
        if total_trades == 0:
            return {"message": "No completed trades found"}

        winning_trades = len([e for e in entries if e.result == TradeResult.WIN])
        losing_trades = len([e for e in entries if e.result == TradeResult.LOSS])
        break_even_trades = len([e for e in entries if e.result == TradeResult.BREAK_EVEN])

        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        pnl_values = [float(e.pnl) for e in entries if e.pnl is not None]
        total_pnl = sum(pnl_values) if pnl_values else 0
        avg_pnl = total_pnl / len(pnl_values) if pnl_values else 0

        winning_pnls = [float(e.pnl) for e in entries if e.pnl is not None and e.result == TradeResult.WIN]
        losing_pnls = [float(e.pnl) for e in entries if e.pnl is not None and e.result == TradeResult.LOSS]

        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0

        profit_factor = abs(sum(winning_pnls) / sum(losing_pnls)) if losing_pnls and sum(losing_pnls) != 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "break_even_trades": break_even_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "average_pnl": round(avg_pnl, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round((win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss), 2),
        }

    def _analyze_setup_quality(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze the quality of trade setups."""
        setup_entries = [e for e in entries if e.setup_score is not None]

        if not setup_entries:
            return {"message": "No setup scores available for analysis"}

        scores = [e.setup_score for e in setup_entries]
        high_quality_setups = [e for e in setup_entries if e.setup_score >= 80]
        low_quality_setups = [e for e in setup_entries if e.setup_score < 60]

        # Analyze correlation between setup quality and results
        high_quality_wins = len([e for e in high_quality_setups if e.result == TradeResult.WIN])
        low_quality_wins = len([e for e in low_quality_setups if e.result == TradeResult.WIN])

        high_quality_win_rate = (high_quality_wins / len(high_quality_setups)) * 100 if high_quality_setups else 0
        low_quality_win_rate = (low_quality_wins / len(low_quality_setups)) * 100 if low_quality_setups else 0

        return {
            "total_setups_scored": len(setup_entries),
            "average_setup_score": round(sum(scores) / len(scores), 2),
            "high_quality_setups_count": len(high_quality_setups),
            "low_quality_setups_count": len(low_quality_setups),
            "high_quality_win_rate": round(high_quality_win_rate, 2),
            "low_quality_win_rate": round(low_quality_win_rate, 2),
            "setup_score_distribution": {
                "90-100": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "70-79": len([s for s in scores if 70 <= s < 80]),
                "60-69": len([s for s in scores if 60 <= s < 70]),
                "below_60": len([s for s in scores if s < 60]),
            },
            "quality_insight": (
                f"High-quality setups (score ≥80) have a {high_quality_win_rate:.1f}% win rate "
                f"vs {low_quality_win_rate:.1f}% for low-quality setups (score <60)"
            ) if high_quality_setups and low_quality_setups else "Insufficient data for quality comparison"
        }

    def _analyze_psychological_patterns(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze psychological and emotional patterns in trading."""
        psych_entries = [e for e in entries if e.psychology_state or e.mistakes_made or e.what_went_well or e.lessons_learned]

        if not psych_entries:
            return {"message": "Insufficient psychological data for analysis"}

        # Extract common emotional states
        emotional_states = []
        for entry in entries:
            if entry.psychology_state:
                emotional_states.append(entry.psychology_state.lower())

        # Extract common mistakes
        mistake_keywords = []
        for entry in entries:
            if entry.mistakes_made:
                # Simple keyword extraction - in production would use NLP
                words = entry.mistakes_made.lower().split()
                mistake_keywords.extend([w for w in words if len(w) > 3][:5])  # Top 5 words per entry

        # Extract common lessons
        lesson_keywords = []
        for entry in entries:
            if entry.lessons_learned:
                words = entry.lessons_learned.lower().split()
                lesson_keywords.extend([w for w in words if len(w) > 3][:5])

        # Count frequencies
        from collections import Counter
        emotion_counter = Counter(emotional_states)
        mistake_counter = Counter(mistake_keywords)
        lesson_counter = Counter(lesson_keywords)

        return {
            "entries_with_psych_data": len(psych_entries),
            "top_emotional_states": emotion_counter.most_common(5),
            "common_mistake_keywords": mistake_counter.most_common(10),
            "common_lesson_keywords": lesson_counter.most_common(10),
            "psychological_insight": (
                f"Most frequently mentioned emotional state: '{emotion_counter.most_common(1)[0][0]}' "
                f"({emotion_counter.most_common(1)[0][1]} occurrences)"
            ) if emotional_states else "No emotional state data recorded"
        }

    def _analyze_session_performance(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze performance by trading session."""
        session_data = defaultdict(lambda: {"trades": 0, "wins": 0, "total_pnl": 0.0})

        for entry in entries:
            if entry.entry_type == JournalEntryType.TRADE_JOURNAL and entry.result and entry.session:
                session_key = entry.session.value
                session_data[session_key]["trades"] += 1
                if entry.result == TradeResult.WIN:
                    session_data[session_key]["wins"] += 1
                if entry.pnl:
                    session_data[session_key]["total_pnl"] += float(entry.pnl)

        # Calculate metrics for each session
        session_metrics = {}
        for session, data in session_data.items():
            if data["trades"] > 0:
                win_rate = (data["wins"] / data["trades"]) * 100
                avg_pnl = data["total_pnl"] / data["trades"]
                session_metrics[session] = {
                    "trades": data["trades"],
                    "wins": data["wins"],
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(data["total_pnl"], 2),
                    "average_pnl": round(avg_pnl, 2),
                }

        return {
            "session_breakdown": session_metrics,
            "best_performing_session": max(session_metrics.items(), key=lambda x: x[1]["win_rate"])[0] if session_metrics else None,
            "most_active_session": max(session_metrics.items(), key=lambda x: x[1]["trades"])[0] if session_metrics else None,
        }

    def _analyze_instrument_performance(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze performance by trading instrument."""
        instrument_data = defaultdict(lambda: {"trades": 0, "wins": 0, "total_pnl": 0.0, "setup_scores": []})

        for entry in entries:
            if entry.entry_type == JournalEntryType.TRADE_JOURNAL and entry.result and entry.instrument_name:
                instrument_key = entry.instrument_name
                instrument_data[instrument_key]["trades"] += 1
                if entry.result == TradeResult.WIN:
                    instrument_data[instrument_key]["wins"] += 1
                if entry.pnl:
                    instrument_data[instrument_key]["total_pnl"] += float(entry.pnl)
                if entry.setup_score:
                    instrument_data[instrument_key]["setup_scores"].append(entry.setup_score)

        # Calculate metrics for each instrument
        instrument_metrics = {}
        for instrument, data in instrument_data.items():
            if data["trades"] > 0:
                win_rate = (data["wins"] / data["trades"]) * 100
                avg_pnl = data["total_pnl"] / data["trades"]
                avg_setup = sum(data["setup_scores"]) / len(data["setup_scores"]) if data["setup_scores"] else 0
                instrument_metrics[instrument] = {
                    "trades": data["trades"],
                    "wins": data["wins"],
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(data["total_pnl"], 2),
                    "average_pnl": round(avg_pnl, 2),
                    "average_setup_score": round(avg_setup, 2) if data["setup_scores"] else None,
                }

        return {
            "instrument_breakdown": instrument_metrics,
            "most_profitable_instrument": max(instrument_metrics.items(), key=lambda x: x[1]["total_pnl"])[0] if instrument_metrics else None,
            "highest_win_rate_instrument": max(instrument_metrics.items(), key=lambda x: x[1]["win_rate"])[0] if instrument_metrics else None,
        }

    def _analyze_session_distribution(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze distribution of entries across trading sessions."""
        session_counts = defaultdict(int)
        for entry in entries:
            if entry.session:
                session_counts[entry.session.value] += 1

        total = sum(session_counts.values())
        return {
            "session_distribution": {
                session: {"count": count, "percentage": round((count / total) * 100, 2)}
                for session, count in session_counts.items()
            } if total > 0 else {},
            "most_active_session": max(session_counts.items(), key=lambda x: x[1])[0] if session_counts else None,
        }

    def _analyze_instrument_distribution(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze distribution of entries across instruments."""
        instrument_counts = defaultdict(int)
        for entry in entries:
            if entry.instrument_name:
                instrument_counts[entry.instrument_name] += 1

        total = sum(instrument_counts.values())
        return {
            "instrument_distribution": {
                instrument: {"count": count, "percentage": round((count / total) * 100, 2)}
                for instrument, count in instrument_counts.items()
            } if total > 0 else {},
            "most_traded_instrument": max(instrument_counts.items(), key=lambda x: x[1])[0] if instrument_counts else None,
        }

    def _extract_common_elements(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Extract common elements from successful setups."""
        # This would use NLP in production - simplified for now
        common_factors = {
            "timeframe_mentions": defaultdict(int),
            "indicator_mentions": defaultdict(int),
            "pattern_mentions": defaultdict(int),
        }

        timeframes = ["daily", "h4", "h1", "m15", "m5", "m1"]
        indicators = ["rsi", "macd", "bollinger", "moving average", "fibonacci", "volume"]
        patterns = ["breakout", "pullback", "reversal", "continuation", "support", "resistance"]

        for entry in entries:
            if entry.setup_description:
                text = entry.setup_description.lower()
                for tf in timeframes:
                    if tf in text:
                        common_factors["timeframe_mentions"][tf] += 1
                for ind in indicators:
                    if ind in text:
                        common_factors["indicator_mentions"][ind] += 1
                for pat in patterns:
                    if pat in text:
                        common_factors["pattern_mentions"][pat] += 1

        return {
            "timeframe_mentions": dict(common_factors["timeframe_mentions"]),
            "indicator_mentions": dict(common_factors["indicator_mentions"]),
            "pattern_mentions": dict(common_factors["pattern_mentions"]),
        }

    def _analyze_setup_characteristics(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze characteristics of trade setups."""
        setup_chars = {
            "entry_reasons": defaultdict(int),
            "target_reasons": defaultdict(int),
            "stop_loss_reasons": defaultdict(int),
        }

        for entry in entries:
            if entry.entry_reasoning:
                # Simplified keyword extraction
                words = entry.entry_reasoning.lower().split()
                for word in words:
                    if len(word) > 4:  # Meaningful words
                        setup_chars["entry_reasons"][word] += 1
            if entry.target_reason:
                words = entry.target_reason.lower().split()
                for word in words:
                    if len(word) > 4:
                        setup_chars["target_reasons"][word] += 1
            if entry.stop_loss_reason:
                words = entry.stop_loss_reason.lower().split()
                for word in words:
                    if len(word) > 4:
                        setup_chars["stop_loss_reasons"][word] += 1

        return {
            "top_entry_reasons": dict(sorted(setup_chars["entry_reasons"].items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_target_reasons": dict(sorted(setup_chars["target_reasons"].items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_stop_loss_reasons": dict(sorted(setup_chars["stop_loss_reasons"].items(), key=lambda x: x[1], reverse=True)[:5]),
        }

    def _analyze_risk_management(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze risk management patterns."""
        risk_data = {
            "risk_reward_ratios": [],
            "stop_loss_distances": [],
            "target_distances": [],
        }

        for entry in entries:
            if entry.entry_price and entry.stop_loss and entry.target_price:
                entry_price = float(entry.entry_price)
                stop_loss = float(entry.stop_loss)
                target_price = float(entry.target_price)

                # Calculate distances (absolute for simplicity)
                sl_distance = abs(entry_price - stop_loss)
                tp_distance = abs(target_price - entry_price)

                if sl_distance > 0:
                    risk_reward = tp_distance / sl_distance
                    risk_data["risk_reward_ratios"].append(risk_reward)
                    risk_data["stop_loss_distances"].append(sl_distance)
                    risk_data["target_distances"].append(tp_distance)

        if not risk_data["risk_reward_ratios"]:
            return {"message": "Insufficient risk management data"}

        return {
            "average_risk_reward_ratio": round(sum(risk_data["risk_reward_ratios"]) / len(risk_data["risk_reward_ratios"]), 2),
            "median_risk_reward_ratio": round(sorted(risk_data["risk_reward_ratios"])[len(risk_data["risk_reward_ratios"])//2], 2),
            "average_stop_loss_distance": round(sum(risk_data["stop_loss_distances"]) / len(risk_data["stop_loss_distances"]), 4),
            "average_target_distance": round(sum(risk_data["target_distances"]) / len(risk_data["target_distances"]), 4),
            "risk_reward_distribution": {
                "poor (<1:1)": len([r for r in risk_data["risk_reward_ratios"] if r < 1.0]),
                "moderate (1:1 to 2:1)": len([r for r in risk_data["risk_reward_ratios"] if 1.0 <= r < 2.0]),
                "good (2:1 to 3:1)": len([r for r in risk_data["risk_reward_ratios"] if 2.0 <= r < 3.0]),
                "excellent (>3:1)": len([r for r in risk_data["risk_reward_ratios"] if r >= 3.0]),
            },
        }

    def _analyze_psychological_factors(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze psychological factors in trading decisions."""
        psych_factors = {
            "emotional_states_before_entries": [],
            "emotional_states_after_exits": [],
            "decision_confidence_indicators": [],
        }

        for entry in entries:
            if entry.psychology_state:
                psych_factors["emotional_states_before_entries"].append(entry.psychology_state.lower())
            # In a full implementation, we'd have pre/post state tracking

        # Analyze language that indicates confidence/hesitation
        confidence_indicators = ["confident", "sure", "definite", "clear", "convincing"]
        hesitation_indicators = ["unsure", "hesitant", "doubt", "uncertain", "maybe", "perhaps"]

        for entry in entries:
            if entry.setup_description:
                text = entry.setup_description.lower()
                for indicator in confidence_indicators:
                    if indicator in text:
                        psych_factors["decision_confidence_indicators"].append(("confidence", indicator))
                for indicator in hesitation_indicators:
                    if indicator in text:
                        psych_factors["decision_confidence_indicators"].append(("hesitation", indicator))

        return {
            "emotional_state_samples": list(set(psych_factors["emotional_states_before_entries"][:10])) if psych_factors["emotional_states_before_entries"] else [],
            "confidence_vs_hesitation": {
                "confidence_indicators": len([x for x in psych_factors["decision_confidence_indicators"] if x[0] == "confidence"]),
                "hesitation_indicators": len([x for x in psych_factors["decision_confidence_indicators"] if x[0] == "hesitation"]),
            },
        }

    def _analyze_entry_timing(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze timing patterns of trade entries."""
        # This would analyze time of day, session timing, etc.
        hour_distribution = defaultdict(int)

        for entry in entries:
            if entry.entry_time:
                hour = entry.entry_time.hour
                hour_distribution[hour] += 1

        return {
            "hourly_distribution": dict(hour_distribution),
            "most_active_hour": max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None,
            "least_active_hour": min(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else None,
        }

    def _identify_common_mistakes(self, entries: List[JournalEntry]) -> List[Dict[str, Any]]:
        """Identify recurring mistakes from journal entries."""
        mistake_keywords = defaultdict(int)
        mistake_contexts = []

        for entry in entries:
            if entry.mistakes_made:
                text = entry.mistakes_made.lower()
                # Simple keyword spotting - would use NLP in production
                mistake_indicators = [
                    "moved stop", "stop loss", "early exit", "took profit", "should have waited",
                    "impulsive", "emotional", "revenge trade", "overtraded", "didn't follow plan",
                    "ignored signals", "missed signal", "entered early", "entered late"
                ]

                for indicator in mistake_indicators:
                    if indicator in text:
                        mistake_keywords[indicator] += 1
                        mistake_contexts.append({
                            "mistake": indicator,
                            "context": text[:100] + "..." if len(text) > 100 else text,
                            "date": entry.date.isoformat() if entry.date else None,
                            "instrument": entry.instrument_name,
                            "pnl_impact": float(entry.pnl) if entry.pnl else None,
                        })

        # Sort by frequency
        sorted_mistakes = sorted(mistake_keywords.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "mistake_type": mistake,
                "frequency": count,
                "percentage": round((count / len([e for e in entries if e.mistakes_made])) * 100, 2) if any(e.mistakes_made for e in entries) else 0,
                "recent_contexts": [ctx for ctx in mistake_contexts if ctx["mistake"] == mistake][:3],  # Show 3 recent examples
            }
            for mistake, count in sorted_mistakes[:10]  # Top 10 mistakes
        ]

    def _identify_strengths(self, entries: List[JournalEntry]) -> List[Dict[str, Any]]:
        """Identify recurring strengths from journal entries."""
        strength_keywords = defaultdict(int)

        for entry in entries:
            if entry.what_went_well:
                text = entry.what_went_well.lower()
                # Simple keyword spotting - would use NLP in production
                strength_indicators = [
                    "followed plan", "disciplined", "patient", "waited for confirmation",
                    "good risk management", "proper stop loss", "took profit at target",
                    "stayed calm", "emotional control", "stick to strategy", "didn't chase",
                    "waited for setup", "confirmed on higher timeframe"
                ]

                for indicator in strength_indicators:
                    if indicator in text:
                        strength_keywords[indicator] += 1

        # Sort by frequency
        sorted_strengths = sorted(strength_keywords.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "strength_type": strength,
                "frequency": count,
                "percentage": round((count / len([e for e in entries if e.what_went_well])) * 100, 2) if any(e.what_went_well for e in entries) else 0,
            }
            for strength, count in sorted_strengths[:10]  # Top 10 strengths
        ]

    def _analyze_a_plus_setups(self, entries: List[JournalEntry]) -> Dict[str, Any]:
        """Analyze A+ classified setups specifically."""
        a_plus_entries = [e for e in entries if e.a_plus_classification is not None]

        if not a_plus_entries:
            return {"message": "No A+ classified setups found"}

        winning_a_plus = [e for e in a_plus_entries if e.result == TradeResult.WIN]
        losing_a_plus = [e for e in a_plus_entries if e.result == TradeResult.LOSS]

        return {
            "total_a_plus_setups": len(a_plus_entries),
            "winning_a_plus": len(winning_a_plus),
            "losing_a_plus": len(losing_a_plus),
            "a_plus_win_rate": round((len(winning_a_plus) / len(a_plus_entries)) * 100, 2) if a_plus_entries else 0,
            "average_setup_score": round(sum(e.setup_score or 0 for e in a_plus_entries) / len(a_plus_entries), 2),
            "average_pnl": round(sum(float(e.pnl or 0) for e in a_plus_entries) / len(a_plus_entries), 2),
            "average_win_pnl": round(sum(float(e.pnl or 0) for e in winning_a_plus) / len(winning_a_plus), 2) if winning_a_plus else 0,
            "average_loss_pnl": round(sum(float(e.pnl or 0) for e in losing_a_plus) / len(losing_a_plus), 2) if losing_a_plus else 0,
            "instrument_breakdown": self._analyze_instrument_distribution(a_plus_entries),
            "session_breakdown": self._analyze_session_distribution(a_plus_entries),
        }

    def _generate_recommendations(self, entries: List[JournalEntry]) -> List[str]:
        """Generate actionable recommendations based on journal analysis."""
        recommendations = []

        # Get performance metrics
        perf_metrics = self._calculate_performance_metrics(entries)
        if perf_metrics.get("win_rate", 0) < 50:
            recommendations.append(
                f"Win rate is {perf_metrics.get('win_rate', 0):.1f}% - focus on improving trade selection "
                f"and setup quality rather than increasing trade frequency"
            )

        # Get setup quality analysis
        setup_analysis = self._analyze_setup_quality(entries)
        if "high_quality_win_rate" in setup_analysis and "low_quality_win_rate" in setup_analysis:
            hq_wr = setup_analysis["high_quality_win_rate"]
            lq_wr = setup_analysis["low_quality_win_rate"]
            if hq_wr > lq_wr + 20:  # Significant difference
                recommendations.append(
                    f"High-quality setups (score ≥80) win {hq_wr:.1f}% vs {lq_wr:.1f}% for low-quality setups. "
                    f"Focus only on setups scoring 80+ to improve overall performance"
                )

        # Get common mistakes
        common_mistakes = self._identify_common_mistakes(entries)
        if common_mistakes:
            top_mistake = common_mistakes[0]
            recommendations.append(
                f"Most frequent mistake: '{top_mistake['mistake']}' ({top_mistake['frequency']} occurrences). "
                f"Create specific rules to prevent this error in your trading plan"
            )

        # Get psychological insights
        psych_analysis = self._analyze_psychological_patterns(entries)
        if psych_analysis.get("top_emotional_states"):
            top_emotion = psych_analysis["top_emotional_states"][0]
            recommendations.append(
                f"Most common emotional state: '{top_emotion[0]}' ({top_emotion[1]} times). "
                f"Develop pre-trade routines to manage this emotional state effectively"
            )

        # Session-based recommendations
        session_analysis = self._analyze_session_performance(entries)
        if session_analysis.get("best_performing_session"):
            best_session = session_analysis["best_performing_session"]
            worst_session = min(
                [(k, v) for k, v in session_analysis.get("session_breakdown", {}).items()],
                key=lambda x: x[1]["win_rate"],
                default=None
            )
            if worst_session:
                recommendations.append(
                    f"You perform best in {best_session} sessions ({session_analysis['session_breakdown'][best_session]['win_rate']:.1f}% win rate) "
                    f"and worst in {worst_session[0]} sessions ({worst_session[1]['win_rate']:.1f}% win rate). "
                    f"Consider focusing your trading on {best_session} sessions"
                )

        # Risk management recommendations
        risk_analysis = self._analyze_risk_management(entries)
        if risk_analysis.get("average_risk_reward_ratio", 0) < 1.5:
            recommendations.append(
                f"Average risk-reward ratio is {risk_analysis['average_risk_reward_ratio']:.2f}. "
                f"Aim for minimum 2:1 risk-reward to improve profitability even with lower win rate"
            )

        # Default recommendations if no specific issues found
        if not recommendations:
            recommendations.extend([
                "Continue maintaining your current disciplined approach",
                "Review journal entries weekly to reinforce positive patterns",
                "Consider sharing A+ setup insights with other traders in your network",
                "Focus on consistency rather than seeking dramatic improvements"
            ])

        return recommendations[:5]  # Limit to top 5 recommendations

    def _generate_behavioral_recommendations(self, entries: List[JournalEntry]) -> List[str]:
        """Generate behavioral-specific recommendations."""
        recommendations = []

        psych_patterns = self._analyze_psychological_patterns(entries)
        if psych_patterns.get("top_emotional_states"):
            top_emotion = psych_patterns["top_emotional_states"][0]
            if "frustrat" in top_emotion[0] or "angry" in top_emotion[0] or "upset" in top_emotion[0]:
                recommendations.append(
                    f"Frequent emotional state of '{top_emotion[0]}' detected. "
                    f"Implement mandatory break rules after consecutive losses"
                )
            elif "confident" in top_emotion[0] or "certain" in top_emotion[0]:
                recommendations.append(
                    f"High confidence state of '{top_emotion[0]}' noted. "
                    f"Ensure this confidence is based on analysis, not overconfidence bias"
                )

        common_mistakes = self._identify_common_mistakes(entries)
        if any("emotional" in m["mistake_type"] or "impulsive" in m["mistake_type"] for m in common_mistakes):
            recommendations.append(
                "Emotional/impulsive errors identified. Consider implementing a pre-trade checklist "
                "that must be completed before entering any position"
            )

        if not recommendations:
            recommendations.append(
                "No significant behavioral patterns detected requiring intervention. "
                "Continue self-awareness practices through regular journaling"
            )

        return recommendations

    def _calculate_setup_similarity(self, setup1: str, setup2: str) -> float:
        """Calculate similarity between two setup descriptions."""
        if not setup1 or not setup2:
            return 0.0

        # Simple Jaccard similarity for demonstration
        # In production would use cosine similarity with TF-IDF or embeddings
        words1 = set(setup1.lower().split())
        words2 = set(setup2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0