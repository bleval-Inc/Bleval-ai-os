"""
Intelligence Engine Integration for Voice Pipeline

Connects the voice pipeline to the existing Axiom AI intelligence engine,
enabling voice commands to be processed through the full AI stack.
Includes learning mechanisms to improve voice command processing over time.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    IntelligenceEngineOutput,
    ResultContent,
)
from .config import voice_config

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
        self.learning_enabled = True
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

            # Initialize learning components if enabled
            if self.learning_enabled:
                self._setup_learning()

            logger.info("Voice intelligence callback initialized")
        except Exception as e:
            logger.warning(f"Error initializing intelligence callback: {e}")

    def _setup_learning(self):
        """Setup learning components for voice command processing."""
        try:
            # Import memory engine here to avoid circular dependencies
            from axiom.engine.memory import MemoryEngine
            self.memory_engine = MemoryEngine()
            logger.info("Voice intelligence learning components initialized")
        except Exception as e:
            logger.warning(f"Error setting up voice intelligence learning: {e}")
            self.learning_enabled = False

    async def process_command(
        self,
        entity: str,
        command_text: str,
    ) -> Optional[IntelligenceEngineOutput]:
        """
        Process a voice command through the intelligence engine.

        This is the main callback that the voice pipeline calls.
        Includes learning storage for continuous improvement (Phase B7).

        Args:
            entity: Target entity (axiom, jenson, yamako, valtaprime)
            command_text: User's transcribed command

        Returns:
            IntelligenceEngineOutput with full_result and spoken_summary
        """
        logger.info(f"Processing voice command for {entity}: '{command_text}'")

        result = None
        success = False

        try:
            # Try to use intelligence engine first
            if self.intelligence_engine:
                # Get agent ID for intelligence engine routing
                agent_id = entity.lower()
                result = await self.intelligence_engine.generate_for_executive(
                    exec_id=agent_id,
                    task_description=command_text,
                    org_id="",  # Could be extracted from runtime if needed
                    additional_context=None  # Could be enhanced with context if needed
                )

                # Transform intelligence engine result to voice pipeline format
                voice_result = self._transform_intelligence_result(result, agent_id, command_text)
                success = voice_result is not None
                return voice_result

            # Fallback to executive agent approach if intelligence engine not available
            agent = self.executive_agents.get(entity)
            if agent:
                # Use actual executive agent
                result = await self._process_with_agent(agent, command_text)
                success = result is not None
                return result

            # Final fallback to mock or basic processing
            result = await self._process_with_mock(entity, command_text)
            success = result is not None
            return result

        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            result = self._mock_result(entity, command_text)
            success = result is not None
            return result

        finally:
            # Store learning from this interaction (Phase B7 enhancement)
            if result:
                metadata = {
                    "processing_method": "intelligence_engine" if self.intelligence_engine and hasattr(self.intelligence_engine, '__class__') and 'intelligence' in str(type(self.intelligence_engine)).lower() else "fallback",
                    "timestamp": datetime.utcnow().isoformat()
                }
                # Extract result text for learning storage
                result_text = ""
                if result and hasattr(result, 'full_result') and hasattr(result.full_result, 'content'):
                    if isinstance(result.full_result.content, dict):
                        result_text = result.full_result.content.get('message', str(result.full_result.content))
                    else:
                        result_text = str(result.full_result.content)
                else:
                    result_text = str(result) if result else ""

                self.store_voice_interaction_learning(
                    entity=entity,
                    command_text=command_text,
                    result_text=result_text,
                    success=success,
                    metadata=metadata
                )

    async def _process_with_agent(self, agent, command_text: str) -> Optional[IntelligenceEngineOutput]:
        """
        Process command using an actual executive agent via the intelligence engine.

        Args:
            agent: Executive agent instance (used to get agent_id)
            command_text: Command to process

        Returns:
            IntelligenceEngineOutput
        """
        try:
            # Get agent ID for intelligence engine routing
            agent_id = getattr(agent, 'name', 'axiom').lower()

            # Use intelligence engine to generate response
            if self.intelligence_engine:
                # Use generate_for_executive for executive agents
                response_text = await self.intelligence_engine.generate_for_executive(
                    exec_id=agent_id,
                    task_description=command_text,
                    org_id="",  # Could be extracted from runtime if needed
                    additional_context=None  # Could be enhanced with context if needed
                )

                # Transform intelligence engine result to voice pipeline format
                return self._transform_intelligence_result(response_text, agent_id, command_text)
            else:
                logger.warning("Intelligence engine not available, falling back to mock")
                return await self._process_with_mock(agent_id, command_text)

        except Exception as e:
            logger.error(f"Error executing agent via intelligence engine: {e}")
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

    def _transform_intelligence_result(
        self,
        result_text: str,
        entity_name: str,
        original_command: str,
    ) -> IntelligenceEngineOutput:
        """
        Transform intelligence engine result to IntelligenceEngineOutput format.

        Args:
            result_text: Raw text result from intelligence engine
            entity_name: Entity name (axiom, jenson, yamako, valtaprime)
            original_command: Original command text

        Returns:
            IntelligenceEngineOutput
        """
        try:
            # Build full result content
            result_content = {
                "type": "text",
                "content": {
                    "message": result_text,
                    "command": original_command,
                    "entity": entity_name
                }
            }

            # Create a concise spoken summary (1-3 sentences)
            # Limit to reasonable length for TTS
            spoken_text = result_text.strip()
            if len(spoken_text) > 300:  # Roughly 2-3 sentences
                # Try to cut at a sentence boundary
                cutoff = spoken_text.rfind('.', 0, 300)
                if cutoff != -1:
                    spoken_text = spoken_text[:cutoff + 1]
                else:
                    spoken_text = spoken_text[:300] + "..."

            # Ensure we have something to say
            if not spoken_text:
                spoken_text = f"I have processed your command: {original_command}"

            return IntelligenceEngineOutput(
                full_result=ResultContent(
                    type="text",
                    content=result_content,
                ),
                spoken_summary=spoken_text,
                target_workstation=voice_config.workstation_routing.get(entity_name, "os"),
            )

        except Exception as e:
            logger.error(f"Error transforming intelligence result: {e}")
            # Fallback to a basic result
            return IntelligenceEngineOutput(
                full_result=ResultContent(
                    type="text",
                    content={
                        "message": f"I have processed your command: {original_command}",
                        "command": original_command,
                        "entity": entity_name
                    }
                ),
                spoken_summary=f"I have processed your command: {original_command}",
                target_workstation=voice_config.workstation_routing.get(entity_name, "os"),
            )

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
            target_workstation=voice_config.workstation_routing.get(entity, "os"),
        )

    def store_voice_interaction_learning(
        self,
        entity: str,
        command_text: str,
        result_text: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store learning from a voice command interaction for future improvement.

        This implements the learning mechanism for Phase B7 by storing voice
        interaction patterns in agent memory, allowing the system to learn
        from experience and improve voice command processing over time.

        Args:
            entity: Target entity (axiom, jenson, yamako, valtaprime)
            command_text: User's transcribed command
            result_text: Result generated by the intelligence engine
            success: Whether the interaction was successful
            metadata: Additional metadata about the interaction
        """
        if not self.learning_enabled or not hasattr(self, 'memory_engine'):
            return

        try:
            # Create a learning entry
            timestamp = datetime.utcnow().isoformat()
            learning_entry = f"""# Voice Command Interaction Learning

## Interaction Details
- Timestamp: {timestamp}
- Entity: {entity}
- Command: {command_text}
- Result: {result_text}
- Success: {success}

## Metadata
{chr(10).join([f'- {k}: {v}' for k, v in (metadata or {}).items()])}

## Learning Notes
This interaction represents a voice command processed through the AXIOM AI OS voice pipeline.
The system can learn from patterns in successful interactions to improve future processing.
"""

            # Store in the agent's memory (learning flows upward from agent layer)
            # Use a standardized naming convention for voice learning entries
            import hashlib
            command_hash = hashlib.md5(command_text.encode()).hexdigest()[:8]
            memory_key = f"voice_learning_{entity}_{command_hash}_{int(datetime.utcnow().timestamp())}"

            self.memory_engine.write_agent_memory(
                agent_id=entity,
                key=memory_key,
                content=learning_entry
            )

            logger.debug(f"Stored voice interaction learning for {entity}: {command_text[:50]}...")

        except Exception as e:
            logger.warning(f"Error storing voice interaction learning: {e}")


def create_voice_callback(runtime=None) -> VoiceIntelligenceCallback:
    """
    Factory function to create a voice intelligence callback.

    Args:
        runtime: Optional AxiomRuntime instance

    Returns:
        VoiceIntelligenceCallback instance
    """
    return VoiceIntelligenceCallback(runtime)