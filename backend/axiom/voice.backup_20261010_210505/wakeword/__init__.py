"""Axiom OS Wake Word Detection package."""

from axiom.voice.wakeword.detector import (
    WakeWordDetector,
    MockWakeWordDetector,
    create_wake_word_detector,
)
from axiom.voice.wakeword.vad import (
    SileroVAD,
    WebRTCVAD,
    VADCaptureManager,
    MockVADCaptureManager,
    create_vad_capture_manager,
)

__all__ = [
    "WakeWordDetector",
    "MockWakeWordDetector",
    "create_wake_word_detector",
    "SileroVAD",
    "WebRTCVAD",
    "VADCaptureManager",
    "MockVADCaptureManager",
    "create_vad_capture_manager",
]