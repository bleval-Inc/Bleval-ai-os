"""Intent router for voice commands."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from axiom.voice.config import EXECUTIVE_WORKSTATIONS, VALID_EXECUTIVES

logger = logging.getLogger("axiom.voice.router.intent_router")


@dataclass
class RouterOutput:
    """Output from the intent router."""
    target_entity: str
    raw_text: str
    delegated_by: Optional[str]  # "axiom" if Axiom delegated, None if direct wake
    timestamp: str
    confidence: float = 1.0
    wake_word: str = ""
    target_workstation: str = ""


class IntentRouter:
    """
    Routes transcribed voice commands to the appropriate executive.
    
    Routing is primarily deterministic based on wake word, with one exception:
    If Axiom is woken, Axiom's intelligence engine does secondary classification
    to decide if it should handle directly or delegate to an executive.
    """
    
    def __init__(self):
        # Keywords that suggest delegation from Axiom to specific executives
        self.delegation_keywords: Dict[str, List[str]] = {
            "jenson": [
                "operations", "project", "team", "meeting", "schedule", "agency",
                "bleval", "inc", "company", "business", "workflow", "task",
                "department", "employee", "hire", "onboard", "process",
            ],
            "valta_prime": [
                "trade", "trading", "market", "portfolio", "position", "risk",
                "gold", "forex", "crypto", "stock", "analysis", "chart",
                "technical", "fundamental", "entry", "exit", "stop loss",
                "take profit", "leverage", "margin", "drawdown", "pnl",
                "profit", "loss", "strategy", "backtest", "signal",
            ],
            "yamako": [
                "personal", "habit", "remind", "reminder", "calendar", "schedule",
                "health", "fitness", "exercise", "meditation", "sleep", "water",
                "daily", "routine", "goal", "journal", "note", "todo", "task",
                "appointment", "birthday", "anniversary", "contact", "call",
            ],
        }
        
        # Axiom's own domain keywords (when it should handle directly)
        self.axiom_keywords = [
            "system", "status", "health", "memory", "knowledge", "research",
            "search", "find", "lookup", "what is", "who is", "define",
            "explain", "how to", "help", "settings", "config", "restart",
            "shutdown", "backup", "sync", "update", "version", "log",
        ]
    
    def route(
        self,
        transcript: str,
        wake_entity: str,
        confidence: float = 1.0,
        wake_word: str = "",
    ) -> RouterOutput:
        """
        Route a transcribed command to the target executive.
        
        Args:
            transcript: The transcribed command text
            wake_entity: The executive that was woken (from wake word detection)
            confidence: Wake word detection confidence
            wake_word: The specific wake word that triggered
            
        Returns:
            RouterOutput with target_entity and routing info
        """
        timestamp = self._get_timestamp()
        lower_text = transcript.lower().strip()
        
        # Direct wake word routing (most common case)
        if wake_entity != "axiom":
            return RouterOutput(
                target_entity=wake_entity,
                raw_text=transcript,
                delegated_by=None,
                timestamp=timestamp,
                confidence=confidence,
                wake_word=wake_word,
                target_workstation=EXECUTIVE_WORKSTATIONS.get(wake_entity, "os"),
            )
        
        # Axiom was woken - check if it should delegate
        delegated_to = self._check_delegation(lower_text)
        
        if delegated_to:
            logger.info(f"Axiom delegating to {delegated_to}: '{transcript}'")
            return RouterOutput(
                target_entity=delegated_to,
                raw_text=transcript,
                delegated_by="axiom",
                timestamp=timestamp,
                confidence=confidence,
                wake_word=wake_word,
                target_workstation=EXECUTIVE_WORKSTATIONS.get(delegated_to, "os"),
            )
        
        # Axiom handles directly
        return RouterOutput(
            target_entity="axiom",
            raw_text=transcript,
            delegated_by=None,
            timestamp=timestamp,
            confidence=confidence,
            wake_word=wake_word,
            target_workstation="os",
        )
    
    def _check_delegation(self, text: str) -> Optional[str]:
        """Check if Axiom should delegate to an executive based on command content."""
        scores: Dict[str, int] = {exec_id: 0 for exec_id in VALID_EXECUTIVES if exec_id != "axiom"}
        
        for exec_id, keywords in self.delegation_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    scores[exec_id] += 1
        
        # Also check Axiom keywords - if strong match, don't delegate
        axiom_score = sum(1 for kw in self.axiom_keywords if kw in text)
        
        # Find highest scoring executive
        if scores:
            best_exec = max(scores, key=scores.get)
            best_score = scores[best_exec]
            
            # Delegate if executive score > axiom score and executive score > 0
            if best_score > axiom_score and best_score > 0:
                return best_exec
        
        return None
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def get_workstation_for_entity(self, entity: str) -> str:
        """Get the target workstation for an entity."""
        return EXECUTIVE_WORKSTATIONS.get(entity, "os")


# Backward compatibility function
def route_command(transcript: str, wake_entity: str, **kwargs) -> RouterOutput:
    """Convenience function for simple routing."""
    router = IntentRouter()
    return router.route(transcript, wake_entity, **kwargs)