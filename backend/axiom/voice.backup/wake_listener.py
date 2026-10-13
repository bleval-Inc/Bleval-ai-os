import sounddevice as sd
import numpy as np
import threading
import logging
from typing import Callable, Optional, Tuple
from queue import Queue

logger = logging.getLogger(__name__)

class VoiceListener:
    def __init__(
        self,
        wake_detector,
        on_wake: Callable[[str, str, float], None],
        audio_queue: Optional[Queue] = None,
        device: int = 1,
        samplerate: int = 16000,
        channels: int = 1,
        dtype: str = 'float32',
        blocksize: int = 1280
    ):
        self.wake_detector = wake_detector
        self.on_wake = on_wake
        self.audio_queue = audio_queue
        self.device = device
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize

        self._stream: Optional[sd.InputStream] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        # State: 'listening' for wake word detection, 'capturing' for sending audio to queue
        self._state = 'listening'
        self._state_lock = threading.Lock()

    def start(self) -> bool:
        with self._lock:
            if self._running:
                logger.warning("[VOICE_LISTENER] Already running")
                return False

            logger.info("[VOICE_LISTENER] Starting")

            try:
                # Initialize the wake detector if it has an initialize method
                if hasattr(self.wake_detector, 'initialize'):
                    self.wake_detector.initialize()

                # Open the microphone stream
                self._stream = sd.InputStream(
                    device=self.device,
                    samplerate=self.samplerate,
                    channels=self.channels,
                    dtype=self.dtype,
                    blocksize=self.blocksize
                )
                self._stream.start()

                logger.info("[VOICE_LISTENER] Microphone opened")
                logger.info("[VOICE_LISTENER] Wake engine active")

                # Reset state to listening (in case we were left in capturing state)
                with self._state_lock:
                    self._state = 'listening'

                # Start the listener thread
                self._running = True
                self._thread = threading.Thread(target=self._audio_loop, daemon=True)
                self._thread.start()

                logger.info("[VOICE_LISTENER] Listening")
                return True

            except Exception as e:
                logger.error(f"[VOICE_LISTENER] Failed to start: {e}", exc_info=True)
                self.stop()
                return False

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                logger.warning("[VOICE_LISTENER] Already stopped")
                return

            logger.info("[VOICE_LISTENER] Stopping")
            self._running = False

            # Stop the stream first
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.error(f"[VOICE_LISTENER] Error closing stream: {e}", exc_info=True)
                finally:
                    self._stream = None

            # Wait for the thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
                if self._thread.is_alive():
                    logger.warning("[VOICE_LISTENER] Thread did not stop gracefully")

            self._thread = None

            # Stop the wake detector if it has a stop method
            if hasattr(self.wake_detector, 'stop'):
                try:
                    self.wake_detector.stop()
                except Exception as e:
                    logger.error(f"[VOICE_LISTENER] Error stopping wake detector: {e}", exc_info=True)

            logger.info("[VOICE_LISTENER] Stopped")

    def set_capturing(self, capturing: bool) -> None:
        """Set whether we are in capturing state (sending audio to queue) or listening state."""
        with self._state_lock:
            self._state = 'capturing' if capturing else 'listening'
        logger.debug(f"[VOICE_LISTENER] State set to: {self._state}")

    def _audio_loop(self) -> None:
        logger.debug("[VOICE_LISTENER] Audio loop started")
        while self._running:
            try:
                # Read audio block
                if self._stream is None:
                    break
                audio_block, overflowed = self._stream.read(self.blocksize)
                if overflowed:
                    logger.warning("[VOICE_LISTENER] Audio input overflowed")

                # Ensure we have the right shape and type
                audio_block = audio_block.flatten().astype(np.float32)

                # Process audio with wake detector only if we are in listening state
                with self._state_lock:
                    state = self._state

                if state == 'listening':
                    result = self.wake_detector.process_audio(audio_block)
                    if result:
                        entity, confidence, wake_word = result
                        logger.info(f"[VOICE_LISTENER] Wake detected: entity={entity}, word={wake_word}, confidence={confidence}")
                        # Invoke the callback immediately
                        try:
                            self.on_wake(entity, wake_word, confidence)
                        except Exception as e:
                            logger.error(f"[VOICE_LISTENER] Error in wake callback: {e}", exc_info=True)
                        # After wake detection, switch to capturing state to send audio to queue
                        self.set_capturing(True)
                    # In listening state, we do not send audio to the queue
                elif state == 'capturing':
                    # In capturing state, we send the audio block to the queue if we have one
                    if self.audio_queue is not None:
                        try:
                            self.audio_queue.put_nowait(audio_block.copy())
                        except Exception as e:
                            # Queue full: we can drop the frame or handle as needed
                            logger.debug(f"[VOICE_LISTENER] Audio queue full, dropping frame: {e}")
                    # Note: we do not do wake detection in capturing state

                # Periodic log (every 100 frames)
                if hasattr(self, '_frame_count'):
                    self._frame_count += 1
                else:
                    self._frame_count = 0

                if self._frame_count % 100 == 0:
                    logger.debug("[VOICE_LISTENER] AUDIO FRAME")

            except Exception as e:
                logger.error(f"[VOICE_LISTENER] Error in audio loop: {e}", exc_info=True)
                # Continue running unless it's a critical error? We'll break on any error to avoid infinite error loop.
                break

        logger.debug("[VOICE_LISTENER] Audio loop ended")