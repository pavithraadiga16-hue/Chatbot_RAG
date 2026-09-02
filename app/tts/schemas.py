"""
PhinsIQ - Text-to-Speech (TTS) Pydantic Schemas
================================================

PURPOSE:
    Data transfer objects (DTOs) for TTS requests, responses, batch synthesis jobs,
    and voice catalog endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    """Direct audio synthesis request."""
    text: str = Field(..., min_length=1, description="Text string to synthesize into speech")
    speaker: Optional[str] = Field(default="EN_INDIA", description="Speaker identifier (default EN_INDIA adult voice)")
    speed: float = Field(default=1.0, ge=0.2, le=3.0, description="Speech playback rate (1.0 = standard rate)")
    pitch: Optional[float] = Field(default=0.0, ge=-12.0, le=12.0, description="Pitch shift in semitones (0.0 = original adult voice)")


class BatchSynthesizeRequest(BaseModel):
    """Batch synthesis request matching legacy Gonzaga / Flutter mobile app schema."""
    text: str = Field(..., min_length=1, description="Text to synthesize")
    lang: Optional[str] = Field(default="en-IN", description="Language code (e.g. en-IN, en-US)")
    style: Optional[str] = Field(default="default", description="Voice speaking style")
    speed: float = Field(default=1.0, ge=0.2, le=3.0, description="Speech speed (default 1.0 standard rate)")
    pitch: Optional[float] = Field(default=0.0, ge=-12.0, le=12.0, description="Pitch shift in semitones (0.0 = adult voice)")
    speaker: Optional[str] = Field(default="EN_INDIA", description="Explicit MeloTTS speaker override (default EN_INDIA)")


class BatchSynthesizeResponse(BaseModel):
    """Immediate response returned after queueing or completing batch synthesis."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: 'completed', 'processing', or 'failed'")
    language: Optional[str] = Field(default="en-IN", description="Language code")
    style: Optional[str] = Field(default="default", description="Voice style")
    text_length: int = Field(..., description="Number of characters in the input text")


class BatchResultResponse(BaseModel):
    """Result payload when querying the status and audio data of a batch synthesis job."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status ('completed', 'processing', 'failed')")
    audio_b64: Optional[str] = Field(default=None, description="Base64-encoded WAV audio data")
    sample_rate: Optional[int] = Field(default=None, description="Audio sample rate (e.g. 44100)")
    latency_ms: Optional[int] = Field(default=None, description="Synthesis latency in milliseconds")
    language: Optional[str] = Field(default="en-IN", description="Language code")
    style: Optional[str] = Field(default="default", description="Voice style")
    error: Optional[str] = Field(default=None, description="Failure reason if status is 'failed'")


class SpeakerInfo(BaseModel):
    """Metadata describing an available speaker voice."""
    id: str = Field(..., description="Speaker identifier used in synthesis requests")
    name: str = Field(..., description="Display name of the voice character")
    accent: str = Field(..., description="Language accent description")
    flag: str = Field(..., description="Flag emoji for UI display")


class TTSHealthResponse(BaseModel):
    """TTS subsystem health check response."""
    status: str = Field(..., description="'ok' or 'unavailable'")
    available: bool = Field(..., description="True if MeloTTS and required ML libraries are installed and ready")
    model: str = Field(default="melotts-english", description="Model architecture name")
    speaker: str = Field(..., description="Active default speaker")
    device: str = Field(default="cpu", description="Inference compute device")
    sample_rate: int = Field(default=44100, description="WAV sample rate in Hz")
    cache_size: int = Field(default=0, description="Count of synthesized phrases currently cached in memory")
    uptime_seconds: float = Field(..., description="Seconds since the TTS service was initialized")
    error: Optional[str] = Field(default=None, description="Dependency or initialization error details, if any")
