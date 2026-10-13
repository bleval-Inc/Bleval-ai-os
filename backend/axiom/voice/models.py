"""
Data models for the Axiom Voice Pipeline.

Defines Pydantic models for type safety and validation across the pipeline.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================


class EventType(str, Enum):
    """Types of events emitted through the pipeline."""

    WAKE_DETECTED = "wake_detected"
    LISTENING_STARTED = "listening_started"
    ACKNOWLEDGING = "acknowledging"
    CAPTURING = "capturing"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    PROCESSING = "processing"
    EXECUTIVE_SPEAKING = "executive_speaking"
    DISPLAY_RESULT = "display_result"
    IDLE = "idle"
    ERROR = "error"


class IntentType(str, Enum):
    """Types of intents that can be routed."""
    
    SEARCH = "search"
    DATA_QUERY = "data_query"
    ACTION = "action"
    GENERAL = "general"
    DELEGATION = "delegation"


# ============================================================================
# WAKE WORD EVENTS
# ============================================================================


class WakeWordDetection(BaseModel):
    """Result from wake word detection."""
    
    wake_entity: str = Field(..., description="Entity name triggered: axiom, jenson, yamako, valtaprime")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    

class WakeWordEvent(BaseModel):
    """Event emitted when a wake word is detected."""
    
    event: str = Field(default=EventType.WAKE_DETECTED)
    detection: WakeWordDetection
    
    class Config:
        use_enum_values = True


# ============================================================================
# SPEECH-TO-TEXT EVENTS
# ============================================================================


class TranscriptionComplete(BaseModel):
    """Result from speech-to-text transcription."""
    
    raw_text: str = Field(..., description="Transcribed user command")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Transcription confidence")
    duration_seconds: float = Field(..., ge=0.0, description="Duration of captured audio")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TranscriptionCompleteEvent(BaseModel):
    """Event emitted after STT completes."""
    
    event: str = Field(default=EventType.TRANSCRIPTION_COMPLETE)
    wake_entity: str
    transcription: TranscriptionComplete
    
    class Config:
        use_enum_values = True


# ============================================================================
# INTENT ROUTING
# ============================================================================


class IntentRouterOutput(BaseModel):
    """Output from the intent router."""
    
    target_entity: str = Field(
        ..., 
        description="Target entity: axiom, jenson, yamako, valtaprime"
    )
    raw_text: str = Field(..., description="Transcribed user command")
    intent_type: IntentType = Field(default=IntentType.GENERAL)
    delegated_by: Optional[str] = Field(None, description="If delegated, which entity delegated it")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============================================================================
# INTELLIGENCE ENGINE OUTPUT
# ============================================================================


class ResultContent(BaseModel):
    """Generic result content container."""
    
    type: str = Field(..., description="search_results | data | text | table")
    content: Any = Field(..., description="The actual result data")
    metadata: Optional[dict[str, Any]] = None


class IntelligenceEngineOutput(BaseModel):
    """Output from the intelligence engine (Axiom's AI model)."""
    
    full_result: ResultContent = Field(
        ..., 
        description="Complete result for display on workstation UI"
    )
    spoken_summary: str = Field(
        ..., 
        description="Short, natural-language summary (1-3 sentences) for TTS"
    )
    target_workstation: str = Field(
        ..., 
        description="Workstation to display result: os | agency | personal | trading"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# TEXT-TO-SPEECH EVENTS
# ============================================================================


class SynthesizedAudio(BaseModel):
    """Result from text-to-speech synthesis."""
    
    audio_bytes: Optional[bytes] = Field(None, description="Raw audio bytes (if streamed)")
    audio_url: Optional[str] = Field(None, description="URL to audio file (if written to disk)")
    duration_seconds: float = Field(..., ge=0.0)
    sample_rate: int = Field(default=22050)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutiveSpeakingEvent(BaseModel):
    """Event emitted when an executive is speaking (audio being synthesized)."""
    
    event: str = Field(default=EventType.EXECUTIVE_SPEAKING)
    entity: str
    spoken_text: str
    audio: SynthesizedAudio
    
    class Config:
        use_enum_values = True


# ============================================================================
# DISPLAY RESULTS
# ============================================================================


class DisplayResultEvent(BaseModel):
    """Event to display results on a workstation."""
    
    event: str = Field(default=EventType.DISPLAY_RESULT)
    workstation: str = Field(..., description="os | agency | personal | trading")
    data: ResultContent
    requested_by_entity: str = Field(..., description="Which entity requested this display")
    
    class Config:
        use_enum_values = True


# ============================================================================
# STATE TRANSITION EVENTS
# ============================================================================


class ListeningStartedEvent(BaseModel):
    """Event when listening starts after wake word."""

    event: str = Field(default=EventType.LISTENING_STARTED)
    wake_entity: str

    class Config:
        use_enum_values = True


class AcknowledgingEvent(BaseModel):
    """Event when acknowledging wake word and preparing to capture command."""

    event: str = Field(default=EventType.ACKNOWLEDGING)
    wake_entity: str

    class Config:
        use_enum_values = True


class CapturingEvent(BaseModel):
    """Event when capturing audio command after wake word acknowledgment."""

    event: str = Field(default=EventType.CAPTURING)
    wake_entity: str

    class Config:
        use_enum_values = True


class ProcessingEvent(BaseModel):
    """Event when processing input (routing, intelligence engine)."""

    event: str = Field(default=EventType.PROCESSING)
    entity: str

    class Config:
        use_enum_values = True


class IdleEvent(BaseModel):
    """Event when returning to idle state."""
    
    event: str = Field(default=EventType.IDLE)
    
    class Config:
        use_enum_values = True


class ErrorEvent(BaseModel):
    """Event when an error occurs."""
    
    event: str = Field(default=EventType.ERROR)
    error_message: str
    error_code: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


# ============================================================================
# PIPELINE STATE
# ============================================================================


@dataclass
class PipelineState:
    """Current state of the voice pipeline."""
    
    is_listening: bool = False
    active_entity: Optional[str] = None
    current_phase: str = "idle"  # idle | listening | transcribing | processing | speaking
    last_event: Optional[dict[str, Any]] = None
    error: Optional[str] = None
