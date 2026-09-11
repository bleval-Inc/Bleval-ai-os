"""Wake word detection using openWakeWord."""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import numpy as np

from axiom.voice.config import (
    voice_config,
    EXECUTIVE_WAKE_WORDS,
    VALID_EXECUTIVES,
)

logger = logging.getLogger("axiom.voice.wakeword.detector")


class WakeWordDetector:
    """
    Multi-model wake word detector using openWakeWord.

    Runs one model per executive against the same live microphone stream.
    On detection, emits an event with the executive ID and confidence.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        on_wake: Optional[Callable[[str, float, str], None]] = None,
    ):
        self.config = config or voice_config.wake_word
        self.on_wake = on_wake

        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._audio_stream = None
        self._audio_queue = queue.Queue(maxsize=10)

        self._sample_rate = self.config.sample_rate
        self._chunk_size = self.config.chunk_size

        # Exposed to the debug endpoint. Updated on every inference so the
        # reported scores always reflect the SAME path used for the trigger
        # decision (no separate hidden detection path).
        self._latest_scores: Dict[str, float] = {}

        # Rolling buffer of the most recent microphone audio (float32 mono).
        # On wake detection this is handed to the VAD capture manager so the
        # beginning of the user's command is not lost during the
        # wake -> capture microphone handoff.
        self._recent_audio: list = []
        self._recent_sample_count = 0
        self._recent_max_samples = int(self.config.sample_rate * 1.2)

        # Diagnostic counters
        self._callback_count = 0
        self._last_callback_time = 0.0
        self._consumed_chunk_count = 0
        self._last_consumed_time = 0.0

    def load_models(self) -> bool:
        """Load all configured wake word models."""

        try:
            from openwakeword.model import Model
        except ImportError:
            logger.error(
                "openWakeWord not installed. "
                "Install with: pip install openwakeword"
            )
            return False

        loaded_count = 0

        # ---------------------------------------------------------
        # Load custom executive-specific models.
        # ---------------------------------------------------------
        for exec_id in VALID_EXECUTIVES:
            model_path = self.config.model_paths.get(exec_id)

            if not model_path:
                continue

            if not Path(model_path).exists():
                logger.warning(
                    f"Custom wake word model not found for "
                    f"{exec_id}: {model_path}"
                )
                continue

            try:
                model = Model(
                    wakeword_models=[model_path],
                    inference_framework="onnx",
                )

                self._models[exec_id] = model
                loaded_count += 1

                logger.info(
                    f"Loaded custom wake word model for "
                    f"{exec_id}: {model_path}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to load custom wake word model "
                    f"for {exec_id}: {e}"
                )

        logger.info(
            f"Loaded {loaded_count}/{len(VALID_EXECUTIVES)} "
            f"wake word models"
        )

        return loaded_count > 0

    def start(self, audio_stream: Any = None) -> bool:
        """Start the wake word detection loop."""
        print(f"[STARTUP_VOICE] WakeWordDetector.start ENTER: id={id(self)}, audio_stream provided={audio_stream is not None}")

        if self._running:
            print("[STARTUP_VOICE] WakeWordDetector.start: already running, returning True")
            logger.warning(
                "Wake word detector already running"
            )
            return True

        if not self._models:
            print("[STARTUP_VOICE] WakeWordDetector.start: no models loaded, attempting to load")
            if not self.load_models():
                logger.error(
                    "No wake word models loaded"
                )
                print("[STARTUP_VOICE] WakeWordDetector.start: load_models() failed, returning False")
                return False
            else:
                print("[STARTUP_VOICE] WakeWordDetector.start: load_models() succeeded")

        self._audio_stream = audio_stream
        self._audio_queue = queue.Queue(maxsize=10)
        self._running = True
        print(f"[STARTUP_VOICE] WakeWordDetector.start: set _running=True, _audio_stream={self._audio_stream}")

        self._thread = threading.Thread(
            target=self._detection_loop,
            daemon=True,
        )

        self._thread.start()
        print(f"[STARTUP_VOICE] WakeWordDetector.start: detection thread started, id={self._thread.ident}")

        logger.info(
            "Wake word detector started"
        )
        print("[STARTUP_VOICE] WakeWordDetector.start EXIT, returning True")
        return True

    def stop(self) -> None:
        """Stop the wake word detection loop."""

        self._running = False

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self._audio_stream:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
            except Exception:
                pass

            self._audio_stream = None

        logger.info(
            "Wake word detector stopped"
        )

    def _detection_loop(self) -> None:
        """
        Main detection loop.

        Reads one microphone chunk and evaluates that exact chunk
        against all executive models.

        The highest-confidence executive becomes the winner.

        A wake word is accepted only when:
          1. The winner reaches the confidence threshold.
          2. The winner beats the second-best model by the margin.
          3. The detector is outside the cooldown period.
        """

        import sounddevice as sd

        # ---------------------------------------------------------
        # Create microphone stream if the caller did not provide one.
        # ---------------------------------------------------------
        stream = self._audio_stream

        if stream is None:
            try:
                print(f"[STARTUP_VOICE] WakeWordDetector._detection_loop: creating new audio stream")
                def audio_callback(
                    indata,
                    frames,
                    time_info,
                    status,
                ):
                    # Diagnostic instrumentation for audio callback
                    current_time = time.time()
                    self._callback_count += 1

                    if status:
                        logger.debug(
                            f"Audio callback status: {status}"
                        )

                    if not self._running:
                        return

                    # Calculate audio levels
                    audio_float = indata[:, 0]
                    peak = np.max(np.abs(audio_float)) if len(audio_float) > 0 else 0.0
                    rms = np.sqrt(np.mean(audio_float**2)) if len(audio_float) > 0 else 0.0

                    # Log first callback and every 50th callback
                    if self._callback_count == 1 or self._callback_count % 50 == 0:
                        logger.info(
                            f"[AUDIO_TRACE] callback received count={self._callback_count} frames={frames} peak={peak:.6f} rms={rms:.6f} status={status}"
                        )
                    elif self._callback_count % 50 == 1:  # Every 50th after first (51, 101, etc.)
                        logger.info(
                            f"[AUDIO_TRACE] callback count={self._callback_count} peak={peak:.6f} rms={rms:.6f}"
                        )

                    try:
                        self._audio_queue.put_nowait(
                            indata[:, 0].copy()
                        )
                    except queue.Full:
                        try:
                            self._audio_queue.get_nowait()
                        except queue.Empty:
                            pass

                        try:
                            self._audio_queue.put_nowait(
                                indata[:, 0].copy()
                            )
                        except queue.Full:
                            pass

                stream = sd.InputStream(
                    samplerate=self._sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=self._chunk_size,
                    device=voice_config.audio_device,
                    callback=audio_callback,
                )

                print(f"[STARTUP_VOICE] WakeWordDetector._detection_loop: about to start audio stream, id={id(stream)}")
                stream.start()
                self._audio_stream = stream

                # Log stream startup info
                print(f"[STARTUP_VOICE] WakeWordDetector._detection_loop: audio stream started, active={stream.active}, closed={stream.closed}")
                logger.info(
                    f"[AUDIO_STREAM_START] stream_id={id(stream)} active={stream.active} closed={stream.closed} running={self._running} callback_count={self._callback_count}"
                )
                print(f"[AUDIO_STREAM_START] stream_id={id(stream)} active={stream.active} closed={stream.closed} running={self._running} callback_count={self._callback_count}")

            except Exception as e:
                logger.error(
                    f"Failed to open audio stream: {e}"
                )
                print(f"[STARTUP_VOICE] WakeWordDetector._detection_loop: Failed to open audio stream: {e}")

                self._running = False
                return

        logger.info(
            "Wake word detection loop running"
        )

        # ---------------------------------------------------------
        # Runtime decision parameters.
        # ---------------------------------------------------------
        confidence_threshold = (
            self.config.confidence_threshold
        )

        winner_margin = 0.05
        cooldown_seconds = 1.0

        last_trigger_time = 0.0

        # ---------------------------------------------------------
        # Main detection loop.
        # ---------------------------------------------------------
        while self._running:
            try:
                # Receive one microphone chunk from the
                # callback-based sounddevice stream.
                try:
                    audio_data = self._audio_queue.get(
                        timeout=0.25
                    )
                except queue.Empty:
                    continue

                # Diagnostic instrumentation for consumed chunks
                current_time = time.time()
                self._consumed_chunk_count += 1

                if len(audio_data) != self._chunk_size:
                    logger.debug(
                        f"Unexpected audio chunk size: "
                        f"{len(audio_data)} "
                        f"(expected {self._chunk_size})"
                    )
                    continue

                if not np.isfinite(audio_data).all():
                    logger.debug(
                        "Ignoring non-finite audio chunk"
                    )
                    continue

                if not np.any(audio_data):
                    logger.debug(
                        "Ignoring silent audio chunk"
                    )
                    continue

                # Log first consumed chunk and every 50th consumed chunk
                if self._consumed_chunk_count == 1 or self._consumed_chunk_count % 50 == 0:
                    # Calculate audio levels
                    peak = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 0.0
                    rms = np.sqrt(np.mean(audio_data**2)) if len(audio_data) > 0 else 0.0
                    logger.info(
                        f"[AUDIO_TRACE] consumed chunk count={self._consumed_chunk_count} peak={peak:.6f} rms={rms:.6f} _running={self._running} stream_active={getattr(self._audio_stream, 'active', 'None') if self._audio_stream else 'None'}"
                    )
                elif self._consumed_chunk_count % 50 == 1:  # Every 50th after first (51, 101, etc.)
                    # Calculate audio levels
                    peak = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 0.0
                    rms = np.sqrt(np.mean(audio_data**2)) if len(audio_data) > 0 else 0.0
                    logger.info(
                        f"[AUDIO_TRACE] consumed count={self._consumed_chunk_count} peak={peak:.6f} rms={rms:.6f}"
                    )

                # -------------------------------------------------
                # sounddevice gives float32 audio in approximately
                # [-1.0, 1.0].
                #
                # openWakeWord expects int16 PCM here.
                # -------------------------------------------------
                audio_int16 = (
                    audio_data.flatten() * 32767
                ).astype(np.int16)

                # -------------------------------------------------
                # Get one score from every executive model for the
                # SAME audio chunk.
                # -------------------------------------------------
                scores: Dict[str, float] = {}

                for exec_id, model in self._models.items():
                    try:
                        prediction = model.predict(
                            audio_int16
                        )

                        # Extract scores for all wake word phrases associated with this executive
                        executive_score = 0.0
                        if isinstance(prediction, dict) and prediction:
                            # Get the maximum score among all wake word phrases for this executive
                            wake_word_phrases = EXECUTIVE_WAKE_WORDS.get(exec_id, [exec_id])
                            phrase_scores = []
                            for phrase in wake_word_phrases:
                                if phrase in prediction:
                                    phrase_scores.append(float(prediction[phrase]))

                            # Use the maximum score among all phrases for this executive
                            if phrase_scores:
                                executive_score = max(phrase_scores)
                            # Fallback: if no specific phrases matched, use max of all predictions
                            elif prediction:
                                executive_score = max(float(value) for value in prediction.values())

                        scores[exec_id] = executive_score

                    except Exception as e:
                        logger.debug(
                            f"Model inference error for "
                            f"{exec_id}: {e}"
                        )

                        scores[exec_id] = 0.0

                if not scores:
                    continue

                # Temporary production diagnostic:
                # expose the latest model scores to the debug endpoint.
                self._latest_scores = dict(scores)

                # -------------------------------------------------
                # Rank all executives by confidence.
                # -------------------------------------------------
                ranked = sorted(
                    scores.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )

                winner, winner_score = ranked[0]

                second_score = (
                    ranked[1][1]
                    if len(ranked) > 1
                    else 0.0
                )

                margin = (
                    winner_score - second_score
                )

                now = time.monotonic()

                # -------------------------------------------------
                # Accept only a strong, clearly separated winner.
                # -------------------------------------------------
                if (
                    winner_score >= confidence_threshold
                    and margin >= winner_margin
                    and (
                        now - last_trigger_time
                    ) >= cooldown_seconds
                ):
                    wake_word = (
                        self._get_triggered_wake_word(
                            winner,
                            winner,
                        )
                    )

                    logger.info(
                        f"Wake word detected: "
                        f"{winner} "
                        f"({wake_word}) "
                        f"confidence="
                        f"{winner_score:.3f} "
                        f"margin="
                        f"{margin:.3f}"
                    )

                    if self.on_wake:
                        try:
                            self.on_wake(
                                winner,
                                winner_score,
                                wake_word,
                            )

                        except Exception as e:
                            logger.error(
                                f"Wake callback error: {e}"
                            )

                    last_trigger_time = now

            except Exception as e:
                logger.error(
                    f"Error in detection loop: {e}"
                )

                time.sleep(0.1)

        logger.info(
            "Wake word detection loop stopped"
        )

    def _get_triggered_wake_word(
        self,
        exec_id: str,
        model_name: str,
    ) -> str:
        """
        Map an executive/model to its primary wake word phrase.

        model_name is retained in the method signature for
        compatibility with the existing detector architecture.
        """

        return EXECUTIVE_WAKE_WORDS.get(
            exec_id,
            [exec_id],
        )[0]


class MockWakeWordDetector:
    """
    Mock detector for testing without hardware/models.

    Simulates wake word detection after a configurable delay.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        on_wake: Optional[Callable[[str, float, str], None]] = None,
    ):
        self.config = config or voice_config.wake_word
        self.on_wake = on_wake

        self._running = False
        self._thread: Optional[threading.Thread] = None

    def load_models(self) -> bool:
        logger.info(
            "Mock wake word detector: models 'loaded'"
        )
        return True

    def start(self, audio_stream: Any = None) -> bool:
        if self._running:
            return True

        self._running = True

        self._thread = threading.Thread(
            target=self._mock_loop,
            daemon=True,
        )

        self._thread.start()

        logger.info(
            "Mock wake word detector started"
        )

        return True

    def stop(self) -> None:
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        logger.info(
            "Mock wake word detector stopped"
        )

    def _mock_loop(self) -> None:
        """Simulate wake word detection every 30 seconds."""

        import random

        executives = list(VALID_EXECUTIVES)

        while self._running:
            time.sleep(30)

            if not self._running:
                break

            exec_id = random.choice(
                executives
            )

            wake_word = EXECUTIVE_WAKE_WORDS[
                exec_id
            ][0]

            confidence = random.uniform(
                0.6,
                0.95,
            )

            logger.info(
                f"[MOCK] Wake word: "
                f"{exec_id} "
                f"({wake_word}) "
                f"confidence="
                f"{confidence:.3f}"
            )

            if self.on_wake:
                self.on_wake(
                    exec_id,
                    confidence,
                    wake_word,
                )


def create_wake_word_detector(
    use_mock: bool = False,
    on_wake: Optional[
        Callable[[str, float, str], None]
    ] = None,
) -> WakeWordDetector | MockWakeWordDetector:
    """
    Factory function to create the appropriate detector.
    """

    if use_mock:
        return MockWakeWordDetector(
            on_wake=on_wake
        )

    return WakeWordDetector(
        on_wake=on_wake
    )