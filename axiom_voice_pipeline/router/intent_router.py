"""
Intent Router - determines which entity should handle a command.

Wake word largely determines routing, with Axiom capable of delegating to subordinates.
"""

import logging
from typing import Optional

from ..config import ENTITIES, IntentRouterConfig, intent_router_config
from ..models import IntentRouterOutput, IntentType

logger = logging.getLogger(__name__)


class IntentRouter:
    """
    Routes transcribed commands to the appropriate entity.
    
    Routing logic:
    - If wake_entity is Jenson, Yamako, or Valta Prime: route directly to that entity
    - If wake_entity is Axiom: 
        - If delegation_enabled, perform secondary classification to route to a subordinate
        - Otherwise, handle at Axiom level
    """
    
    def __init__(self, config: IntentRouterConfig = None):
        """
        Initialize the intent router.
        
        Args:
            config: IntentRouterConfig instance. If None, uses global intent_router_config.
        """
        self.config = config or intent_router_config
    
    def route(
        self,
        wake_entity: str,
        raw_text: str,
    ) -> Optional[IntentRouterOutput]:
        """
        Route a command to the appropriate entity.
        
        Args:
            wake_entity: The entity that was woken (axiom, jenson, yamako, valtaprime)
            raw_text: The transcribed user command
            
        Returns:
            IntentRouterOutput with target entity and metadata, or None if routing fails
        """
        if wake_entity not in ENTITIES:
            logger.error(f"Unknown wake entity: {wake_entity}")
            return None
        
        target_entity = wake_entity
        delegated_by = None
        intent_type = self._classify_intent(raw_text)
        
        # If Axiom is the wake entity and delegation is enabled, perform secondary routing
        if wake_entity == "axiom" and self.config.axiom_delegation_enabled:
            target_entity, delegated_by = self._axiom_delegate(raw_text)
        
        logger.info(
            f"Routing: '{raw_text}' -> {target_entity}"
            f" (wake_entity={wake_entity}, intent={intent_type})"
        )
        
        return IntentRouterOutput(
            target_entity=target_entity,
            raw_text=raw_text,
            intent_type=intent_type,
            delegated_by=delegated_by,
            confidence=1.0,  # Routing is deterministic
        )
    
    def _axiom_delegate(self, raw_text: str) -> tuple[str, Optional[str]]:
        """
        When Axiom is woken, determine if the command should be delegated.
        
        Performs lightweight keyword matching to determine if the command is about
        a specific domain (trading, agency, personal) or OS-level.
        
        Args:
            raw_text: The transcribed command
            
        Returns:
            Tuple of (target_entity, delegated_by)
            - If delegation occurs: (delegated_entity, "axiom")
            - If no delegation: ("axiom", None)
        """
        raw_text_lower = raw_text.lower()
        
        # Check delegation keywords for each entity
        for entity_name, keywords in self.config.delegation_keywords.items():
            if any(keyword in raw_text_lower for keyword in keywords):
                logger.debug(
                    f"Axiom delegating to {entity_name} based on keywords in: {raw_text}"
                )
                return entity_name, "axiom"
        
        # No delegation keywords matched - handle at Axiom level
        logger.debug(f"Axiom handling command at OS level: {raw_text}")
        return "axiom", None
    
    def _classify_intent(self, raw_text: str) -> IntentType:
        """
        Classify the intent type of a command.
        
        This is a lightweight classification. A full implementation might use
        the intelligence engine's NLU capabilities.
        
        Args:
            raw_text: The transcribed command
            
        Returns:
            IntentType classification
        """
        raw_text_lower = raw_text.lower()
        
        # Heuristic classification based on keywords
        if any(word in raw_text_lower for word in ["search", "find", "look up", "show"]):
            return IntentType.SEARCH
        elif any(word in raw_text_lower for word in ["get", "fetch", "retrieve", "check", "status"]):
            return IntentType.DATA_QUERY
        elif any(word in raw_text_lower for word in ["do", "execute", "run", "perform", "cancel", "stop"]):
            return IntentType.ACTION
        else:
            return IntentType.GENERAL
