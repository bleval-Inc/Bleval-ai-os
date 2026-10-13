"""Wake word detection using openWakeWord."""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np

from axiom.voice.config import voice_config

logger = logging.getLogger("axiom.voice.wakeword.detector")
logger.info("WakeWordDetector module initializing")


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

        # Exposed to the debug endpoint. Updated on every inference so the
        # reported scores always reflect the SAME path used for the trigger
        # decision (no separate hidden detection path).
        self._latest_scores: Dict[str, float] = {}

        # Diagnostic counters
        self._wake_predictions = 0
        self._wake_detections = 0
        self._last_trigger_time = 0.0

        # Cooldown seconds
        self._cooldown_seconds = 1.0

    def load_models(self) -> bool:
        """Load all configured wake word models."""
        print("Loading wake word models...")

        # Set the feature model path for openwakeword
        # The feature model (melspectrogram.onnx) is required for processing
        feature_model_path = Path(__file__).resolve().parent.parent.parent.parent / "runtime" / "state" / "models" / "wakeword" / "melspectrogram.onnx"
        print(f"Feature model path: {feature_model_path}")
        print(f"Feature model exists: {feature_model_path.exists()}")
        if feature_model_path.exists():
            os.environ["OPENWAKEWORD_FEATURE_MODEL"] = str(feature_model_path)
            print(f"Set OPENWAKEWORD_FEATURE_MODEL to: {feature_model_path}")
        else:
            print(f"Feature model not found at: {feature_model_path}")

        # Log the current value of the environment variable for debugging
        print(f"OPENWAKEWORD_FEATURE_MODEL is set to: {os.environ.get('OPENWAKEWORD_FEATURE_MODEL', 'NOT SET')}")

        try:
            from openwakeword.model import Model
        except ImportError:
                print(
                    "openWakeWord not installed. "
                    "Install with: pip install openwakeword"
                )
                logger.error(
                    "openWakeWord not installed. "
                    "Install with: pip install openwakeword"
                )
                return False

        loaded_count = 0

        # ---------------------------------------------------------
        # Load custom executive-specific models.
        # ---------------------------------------------------------
        for exec_id in voice_config.valid_executives:
            model_path = self.config.model_paths.get(exec_id)

            if not model_path:
                continue

            print(f"Checking model path for {exec_id}: {model_path}")
            if not Path(model_path).exists():
                print(
                    f"Custom wake word model not found for "
                    f"{exec_id}: {model_path}"
                )
                continue

            try:
                print(f"Loading wake word model from: {model_path}")
                # Get the feature model paths for openwakeword
                feature_model_path = Path(__file__).resolve().parent.parent.parent.parent / "runtime" / "state" / "models" / "wakeword" / "melspectrogram.onnx"
                embedding_model_path = Path(__file__).resolve().parent.parent.parent.parent / "runtime" / "state" / "models" / "wakeword" / "embedding_model.onnx"
                model = Model(
                    wakeword_models=[model_path],
                    inference_framework="onnx",
                    melspec_model_path=str(feature_model_path),
                    embedding_model_path=str(embedding_model_path),
                )

                self._models[exec_id] = model
                loaded_count += 1

                print(
                    f"Loaded custom wake word model for "
                    f"{exec_id}: {model_path}"
                )

            except Exception as e:
                print(
                    f"Failed to load custom wake word model "
                    f"for {exec_id}: {e}"
                )
                logger.error(
                    f"Failed to load custom wake word model "
                    f"for {exec_id}: {e}"
                )

        print(
            f"Loaded {loaded_count}/{len(VALID_EXECUTIVES)} "
            f"wake word models"
        )

        return loaded_count > 0

    def start(self, audio_stream: Any = None) -> bool:
        """Start the wake word detector."""
        if self._running:
            return True

        if not self._models:
            if not self.load_models():
                return False

        self._running = True
        logger.info("Wake word detector started")
        return True

    def stop(self) -> None:
        """Stop the wake word detector."""
        self._running = False
        logger.info("Wake word detector stopped")

    def process_audio(self, audio_chunk: np.ndarray) -> Optional[Tuple[str, float, str]]:
        """Process an audio chunk for wake word detection.

        Returns a tuple (entity, confidence, wake_word) if a wake word is detected,
        otherwise None.
        """
        with self._lock:
            if not self._running:
                return None

            self._wake_predictions += 1

            if not self._models:
                return None

            try:
                # Convert to int16 for openWakeWord
                audio_int16 = (audio_chunk.flatten() * 32767).astype(np.int16)

                # Get scores from all models
                scores: Dict[str, float] = {}
                for exec_id, model in self._models.items():
                    try:
                        prediction = model.predict(audio_int16)

                        # Extract scores for all wake word phrases associated with this executive
                        executive_score = 0.0
                        if isinstance(prediction, dict) and prediction:
                            # Get the maximum score among all wake word phrases for this executive
                            wake_word_phrases = EXECUTIVE_WAKE_WORDS.get(exec_id, [exec_id])
                            phrase_scores = []
                            for phrase in wake_word_phrases:
                                if phrase in prediction:
                                    phrase_scores.append(float(prediction[phrase]))

                            if phrase_scores:
                                executive_score = max(phrase_scores)
                            elif prediction:
                                executive_score = max(float(v) for v in prediction.values())

                        scores[exec_id] = executive_score
                    except Exception as e:
                        logger.debug(f"Wake word model error for {exec_id}: {e}")
                        scores[exec_id] = 0.0

                if not scores:
                    return None

                # Temporary production diagnostic:
                # expose the latest model scores to the debug endpoint.
                self._latest_scores = dict(scores)

                # Rank executives by confidence
                ranked = sorted(
                    scores.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )

                winner, winner_score = ranked[0]
                second_score = ranked[1][1] if len(ranked) > 1 else 0.0
                margin = winner_score - second_score

                now = time.time()

                # Check detection criteria
                confidence_threshold = self.config.confidence_threshold
                winner_margin = 0.05

                if (winner_score >= confidence_threshold and
                    margin >= winner_margin and
                    (now - self._last_trigger_time) >= self._cooldown_seconds):

                    self._wake_detections += 1
                    self._last_trigger_time = now
                    wake_word = self._get_triggered_wake_word(winner, winner)
                    return (winner, winner_score, wake_word)

                return None

            except Exception as e:
                logger.debug(f"Wake word processing error: {e}")
                return None

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

        return voice_config.executive_wake_words.get(
            exec_id,
            [exec_id],
        )[0]

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        with self._lock:
            return {
                "wake_predictions": self._wake_predictions,
                "wake_detections": self._wake_detections,
                "running": self._running,
                "latest_scores": dict(self._latest_scores),
            }


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