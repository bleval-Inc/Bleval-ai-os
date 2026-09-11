"""Voice intelligence callback - connects voice pipeline to Axiom runtime."""

import logging
from typing import Any, Optional

from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator

logger = logging.getLogger(__name__)


class VoiceIntelligenceCallback:
    """Callback interface for voice pipeline to interact with Axiom runtime."""

    def __init__(self, runtime: Optional[Any] = None):
        self.runtime = runtime

    async def on_wake_word_detected(self, entity: str, confidence: float) -> None:
        """Called when wake word is detected."""
        logger.info(f"Wake word detected for entity '{entity}' with confidence {confidence}")
        # The pipeline handles capture and STT internally

    async def on_command_received(self, entity: str, command: str) -> None:
        """Called when a command is received after wake word + STT."""
        logger.info(f"Command received from {entity}: '{command}'")
        
        if self.runtime is not None:
            # Route to the appropriate executive or AXIOM AI
            from axiom.runtime.executive_loop import ExecutiveTask
            
            # Create task for the executive runtime
            task = ExecutiveTask(
                task_type="voice_command",
                payload={
                    "entity": entity,
                    "command": command,
                    "source": "voice_pipeline"
                },
                priority="high"
            )
            
            # Send to runtime for processing
            await self.runtime.submit_task(task)
        else:
            logger.warning("No runtime available - command will not be processed")

    async def on_response_ready(self, entity: str, response: str, audio_data: Optional[bytes] = None) -> None:
        """Called when a response is ready to be spoken."""
        logger.info(f"Response ready for {entity}: '{response[:50]}...'")
        # The pipeline handles TTS and relay internally

    async def on_error(self, error: str) -> None:
        """Called when an error occurs in the pipeline."""
        logger.error(f"Voice pipeline error: {error}")


def create_voice_callback(runtime: Optional[Any] = None) -> VoiceIntelligenceCallback:
    """Factory function to create a voice intelligence callback."""
    return VoiceIntelligenceCallback(runtime)