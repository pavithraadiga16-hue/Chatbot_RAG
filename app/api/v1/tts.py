"""
PhinsIQ - Text-to-Speech (TTS) API Endpoints
=============================================

PURPOSE:
    Dedicated endpoints for Voice & Speech Synthesis powered by MeloTTS.
    Keeps the TTS concept completely isolated from PhinsIQ chat and ERP pipelines.

ROUTES:
    GET  /api/v1/tts/health            - Health check & runtime status
    GET  /api/v1/tts/speakers          - Supported voices, accents & flags
    POST /api/v1/tts/synthesize        - Direct text-to-speech (raw WAV or base64)
    POST /api/v1/tts/batch/synthesize  - Batch synthesis (Gonzaga mobile app compat)
    GET  /api/v1/tts/batch/result/{id} - Batch synthesis result retrieval
"""

import hashlib
import time
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.tts.schemas import (
    BatchResultResponse,
    BatchSynthesizeRequest,
    BatchSynthesizeResponse,
    SpeakerInfo,
    SynthesizeRequest,
    TTSHealthResponse,
)
from app.tts.service import tts_service

logger = get_logger(__name__)

router = APIRouter(tags=["Text-to-Speech"])


def _verify_api_key(x_api_key: Optional[str] = None) -> None:
    """Validate X-API-Key if TTS API key is configured."""
    if settings.tts_api_key and x_api_key != settings.tts_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized: Invalid or missing X-API-Key header"},
        )


@router.get(
    "/health",
    response_model=TTSHealthResponse,
    summary="Check TTS engine health",
)
async def tts_health() -> TTSHealthResponse:
    """
    Returns TTS engine availability, active model, device, in-memory cache size, and uptime.
    """
    is_avail = tts_service.is_available
    return TTSHealthResponse(
        status="ok" if is_avail else "unavailable",
        available=is_avail,
        model="melotts-english",
        speaker=settings.tts_speaker,
        device="cpu",
        sample_rate=tts_service.sample_rate,
        cache_size=tts_service.cache_size,
        uptime_seconds=tts_service.uptime_seconds,
        error=tts_service.init_error if not is_avail else None,
    )


@router.get(
    "/speakers",
    response_model=List[SpeakerInfo],
    summary="List available speaker voices",
)
async def list_speakers() -> List[SpeakerInfo]:
    """
    Returns the catalog of available speaker voices and accents.
    """
    return [SpeakerInfo(**s) for s in tts_service.get_available_speakers()]


@router.post(
    "/synthesize",
    summary="Synthesize text to WAV audio directly",
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "Returns raw 16-bit PCM WAV audio.",
        }
    },
)
async def synthesize_direct(
    request: SynthesizeRequest,
    format: str = Query(default="wav", description="'wav' for raw audio stream, 'json' for base64 JSON payload"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Converts input text directly to speech.
    Returns either raw `audio/wav` binary data or base64 JSON based on `format`.
    """
    _verify_api_key(x_api_key)

    if not tts_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=tts_service.init_error or "TTS engine is currently unavailable",
        )

    try:
        wav_bytes, latency_ms = await tts_service.synthesize_wav(
            text=request.text,
            speaker=request.speaker,
            speed=request.speed,
            pitch=request.pitch,
        )

        if format.lower() == "json":
            import base64
            b64_data = base64.b64encode(wav_bytes).decode("ascii")
            return {
                "status": "completed",
                "audio_b64": b64_data,
                "sample_rate": tts_service.sample_rate,
                "latency_ms": latency_ms,
            }

        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=\"speech.wav\"",
                "X-Latency-Ms": str(latency_ms),
                "X-Sample-Rate": str(tts_service.sample_rate),
            },
        )
    except Exception as exc:
        logger.error("tts_direct_synthesis_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio synthesis failed: {exc}",
        )


@router.post(
    "/batch/synthesize",
    response_model=BatchSynthesizeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch synthesis job creation",
)
async def batch_synthesize(
    request: BatchSynthesizeRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> BatchSynthesizeResponse:
    """
    Creates an audio synthesis job matching Gonzaga School Flutter mobile integration.
    """
    _verify_api_key(x_api_key)

    text = request.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text parameter cannot be empty",
        )

    if not tts_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=tts_service.init_error or "TTS engine is currently unavailable",
        )

    # Generate unique job_id
    job_hash = hashlib.sha1(f"{time.time()}|{text}".encode("utf-8")).hexdigest()[:16]
    job_id = f"melo_{job_hash}"

    tts_service.register_job(job_id, {"status": "processing"})

    try:
        audio_b64, sample_rate, latency_ms = await tts_service.synthesize_base64(
            text=text,
            speaker=request.speaker,
            speed=request.speed,
            pitch=request.pitch,
        )

        tts_service.register_job(
            job_id,
            {
                "status": "completed",
                "audio_b64": audio_b64,
                "sample_rate": sample_rate,
                "latency_ms": latency_ms,
                "language": request.lang or "en-IN",
                "style": request.style or "default",
            },
        )

        logger.info(
            "melo_tts_batch_completed",
            job_id=job_id,
            latency_ms=latency_ms,
            text_length=len(text),
        )

        return BatchSynthesizeResponse(
            job_id=job_id,
            status="completed",
            language=request.lang or "en-IN",
            style=request.style or "default",
            text_length=len(text),
        )
    except Exception as exc:
        logger.error("melo_tts_batch_failed", job_id=job_id, error=str(exc))
        tts_service.register_job(
            job_id,
            {
                "status": "failed",
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {exc}",
        )


@router.get(
    "/batch/result/{job_id}",
    response_model=BatchResultResponse,
    summary="Retrieve batch synthesis result",
)
async def get_batch_result(
    job_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Retrieves the audio payload and status for a previously submitted batch synthesis job.
    """
    _verify_api_key(x_api_key)

    job = tts_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Job not found", "job_id": job_id},
        )

    job_status = job.get("status")

    if job_status == "completed":
        return BatchResultResponse(
            job_id=job_id,
            status="completed",
            audio_b64=job.get("audio_b64"),
            sample_rate=job.get("sample_rate"),
            latency_ms=job.get("latency_ms"),
            language=job.get("language", "en-IN"),
            style=job.get("style", "default"),
        )
    elif job_status == "failed":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "job_id": job_id,
                "status": "failed",
                "error": job.get("error", "Speech synthesis failed"),
            },
        )
    else:
        # Processing status (202 Accepted)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"job_id": job_id, "status": job_status or "processing"},
        )
