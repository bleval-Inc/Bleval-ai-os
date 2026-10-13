"""
Intelligence Engine Integration for Voice Pipeline

Connects the voice pipeline to the existing Axiom AI intelligence engine,
enabling voice commands to be processed through the full AI stack.
"""

import asyncio
import logging
from typing import Optional

from axiom_voice_pipeline.models import (
    IntelligenceEngineOutput,
    ResultContent,
)
from axiom_voice_pipeline.config import WORKSTATION_ROUTING

logger = logging.getLogger(__name__)


class VoiceIntelligenceCallback:
    """
    Callback handler that integrates voice commands with the Axiom intelligence engine.
    
    This is the bridge between:
    - Voice pipeline (wake word → transcription → routing)
    - Axiom intelligence engine (AI model, learning, memory)
    - Workstations (result display + audio playback)
    """
    
    def __init__(self, axiom_runtime):
        """
        Initialize callback.
        
        Args:
            axiom_runtime: AxiomRuntime instance from main backend
        """
        self.runtime = axiom_runtime
        self.intelligence_engine = None
        self.executive_agents = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize connections to backend components."""
        if not self.runtime:
            logger.warning("No runtime provided. Intelligence callback will be limited.")
            return
        
        try:
            # Get references to backend systems
            self.intelligence_engine = getattr(self.runtime, 'intelligence', None)
            
            # Cache executive agents
            if hasattr(self.runtime, 'executives'):
                self.executive_agents = self.runtime.executives
            
            logger.info("Voice intelligence callback initialized")
        except Exception as e:
            logger.warning(f"Error initializing intelligence callback: {e}")
    
    async def process_command(
        self,
        entity: str,
        command_text: str,
    ) -> Optional[IntelligenceEngineOutput]:
        """
        Process a voice command through the intelligence engine.
        
        This is the main callback that the voice pipeline calls.
        
        Args:
            entity: Target entity (axiom, jenson, yamako, valtaprime)
            command_text: User's transcribed command
            
        Returns:
            IntelligenceEngineOutput with full_result and spoken_summary
        """
        logger.info(f"Processing voice command for {entity}: '{command_text}'")
        
        try:
            # Get the executive agent or use mock if not available
            agent = self.executive_agents.get(entity)
            
            if agent:
                # Use actual executive agent
                result = await self._process_with_agent(agent, command_text)
            else:
                # Fallback to mock or basic processing
                result = await self._process_with_mock(entity, command_text)
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return self._mock_result(entity, command_text)
    
    async def _process_with_agent(self, agent, command_text: str) -> Optional[IntelligenceEngineOutput]:
        """
        Process command using an actual executive agent.
        
        Args:
            agent: Executive agent instance
            command_text: Command to process
            
        Returns:
            IntelligenceEngineOutput
        """
        try:
            # Call agent's execute or process method
            # This depends on the actual agent interface
            if hasattr(agent, 'execute'):
                result = await agent.execute(command_text)
            elif hasattr(agent, 'process'):
                result = await agent.process(command_text)
            else:
                logger.warning(f"Agent {agent} has no execute/process method")
                return None
            
            # Transform agent result to voice pipeline format
            return self._transform_agent_result(agent, result, command_text)
        
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            return None
    
    async def _process_with_mock(
        self,
        entity: str,
        command_text: str,
    ) -> IntelligenceEngineOutput:
        """
        Process command using mock/fallback responses.
        
        Args:
            entity: Entity name
            command_text: Command text
            
        Returns:
            Mock IntelligenceEngineOutput
        """
        logger.debug(f"Using mock processing for {entity}: {command_text}")
        
        # Simulate some processing delay
        await asyncio.sleep(0.5)
        
        return self._mock_result(entity, command_text)
    
    def _transform_agent_result(
        self,
        agent,
        result: any,
        original_command: str,
    ) -> Optional[IntelligenceEngineOutput]:
        """
        Transform agent result to IntelligenceEngineOutput format.
        
        Args:
            agent: The agent that produced the result
            result: Raw agent result
            original_command: Original command text
            
        Returns:
            IntelligenceEngineOutput or None
        """
        try:
            # Extract entity name from agent
            entity_name = getattr(agent, 'name', 'axiom').lower()
            
            # Build full result content
            if isinstance(result, dict):
                result_content = result
                spoken_text = result.get('summary', f"Processed: {original_command}")
            elif isinstance(result, str):
                result_content = {"message": result}
                spoken_text = result
            else:
                result_content = {"response": str(result)}
                spoken_text = str(result)
            
            # Ensure spoken text is concise (1-3 sentences for TTS)
            if len(spoken_text) > 500:
                spoken_text = spoken_text[:500] + "..."
            
            return IntelligenceEngineOutput(
                full_result=ResultContent(
                    type="agent_result",
                    content=result_content,
                ),
                spoken_summary=spoken_text,
                target_workstation=WORKSTATION_ROUTING.get(entity_name, "os"),
            )
        
        except Exception as e:
            logger.error(f"Error transforming agent result: {e}")
            return None
    
    def _mock_result(
        self,
        entity: str,
        command: str,
    ) -> IntelligenceEngineOutput:
        """
        Generate a mock result for testing/fallback.
        
        Args:
            entity: Entity name
            command: Command text
            
        Returns:
            Mock IntelligenceEngineOutput
        """
        # Personality-specific responses
        responses = {
            "axiom": f"Processing OS-level command: {command}. Standing by for confirmation.",
            "jenson": f"Noted, chief. Working on: {command}. I'll have the details in a moment.",
            "yamako": f"Oh, you want me to {command}? Let me get that sorted for you!",
            "valtaprime": f"Command received. Executing: {command}. Awaiting market conditions.",
        }
        
        spoken_summary = responses.get(entity, f"Received your command: {command}")
        
        # Mock full result data
        full_result = {
            "command": command,
            "entity": entity,
            "status": "processed",
            "data": {
                "message": f"Mock result for command: {command}",
                "confidence": 0.95,
            },
        }
        
        return IntelligenceEngineOutput(
            full_result=ResultContent(
                type="mock_response",
                content=full_result,
            ),
            spoken_summary=spoken_summary,
            target_workstation=WORKSTATION_ROUTING.get(entity, "os"),
        )


def create_voice_callback(runtime=None) -> VoiceIntelligenceCallback:
    """
    Factory function to create a voice intelligence callback.
    
    Args:
        runtime: Optional AxiomRuntime instance
        
    Returns:
        VoiceIntelligenceCallback instance
    """
    return VoiceIntelligenceCallback(runtime)
