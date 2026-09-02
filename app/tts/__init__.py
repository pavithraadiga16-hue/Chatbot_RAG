"""
PhinsIQ Text-to-Speech (TTS) Subsystem
======================================
"""

from app.tts.service import tts_service, TTSService
from app.tts.schemas import (
    SynthesizeRequest,
    BatchSynthesizeRequest,
    BatchSynthesizeResponse,
    BatchResultResponse,
    SpeakerInfo,
    TTSHealthResponse,
)

__all__ = [
    "tts_service",
    "TTSService",
    "SynthesizeRequest",
    "BatchSynthesizeRequest",
    "BatchSynthesizeResponse",
    "BatchResultResponse",
    "SpeakerInfo",
    "TTSHealthResponse",
]
