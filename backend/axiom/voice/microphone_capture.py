"""
Real-time audio input from microphone via sounddevice.
"""

import logging
from typing import AsyncGenerator, Optional

import numpy as np
import sounddevice as sd

from .config import voice_config

logger = logging.getLogger(__name__)


class MicrophoneCapture:
    """Manages real-time audio input from the microphone."""

    def __init__(self, config: Optional[object] = None):
        """
        Initialize microphone capture.

        Args:
            config: Configuration object. If None, uses global voice_config.
        """
        self.config = config or voice_config
        self.stream: Optional[sd.InputStream] = None
        self._audio_queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        """Start the microphone stream."""
        if self.stream is not None:
            logger.warning("Microphone stream already started")
            return

        # Create audio queue for thread-safe communication
        self._audio_queue = asyncio.Queue()

        # Get the current event loop
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new one
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        # Start the sounddevice stream
        self.stream = sd.InputStream(
            samplerate=self.config.wake_word.sample_rate,
            channels=self.config.wake_word.channels,
            dtype='float32',
            callback=self._audio_callback,
        )
        self.stream.start()
        logger.info(f"Microphone stream started: {self.config.wake_word.sample_rate}Hz, {self.config.wake_word.channels} channel")

    def _audio_callback(self, indata, frames, time, status):
        """Audio callback from sounddevice (runs in separate thread)."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        # Convert to mono if needed and put in queue
        if self.config.wake_word.channels == 1:
            audio_data = indata[:, 0]  # Take first channel
        else:
            # Convert to mono by averaging channels
            audio_data = np.mean(indata, axis=1)

        # Put audio data in queue (thread-safe)
        if self._loop and self._audio_queue:
            asyncio.run_coroutine_threadsafe(
                self._audio_queue.put(audio_data.copy()),
                self._loop
            )

    async def stop(self) -> None:
        """Stop the microphone stream."""
        if self.stream is None:
            logger.warning("Microphone stream not started")
            return

        self.stream.stop()
        self.stream.close()
        self.stream = None
        logger.info("Microphone stream stopped")

    async def audio_stream_generator(self) -> AsyncGenerator[np.ndarray, None]:
        """
        Generate audio chunks from the microphone stream.

        Yields:
            Audio chunks as numpy arrays (float32, mono, 16kHz)
        """
        if self._audio_queue is None:
            raise RuntimeError("Microphone stream not started. Call start() first.")

        try:
            while True:
                # Get audio chunk from queue with timeout
                try:
                    audio_chunk = await asyncio.wait_for(
                        self._audio_queue.get(),
                        timeout=1.0
                    )
                    yield audio_chunk
                except asyncio.TimeoutError:
                    # Continue listening if timeout (no audio data)
                    continue
                except Exception as e:
                    logger.error(f"Error in audio stream generator: {e}")
                    break
        except Exception as e:
            logger.error(f"Fatal error in audio stream generator: {e}")
            raise

    def health_check(self) -> bool:
        """Check if microphone stream is active."""
        return self.stream is not None and self.stream.active