"""
FastAPI Router for MeloTTS voice synthesis.
Supports both direct /tts endpoint and batch REST API used by the Gonzaga app.
"""

import time
import hashlib
import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field

from fastapi import APIRouter, Header, HTTPException, Query, Response, status, Request
from fastapi.responses import JSONResponse

import tts_engine

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["TTS"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize")
    speed: Optional[float] = Field(1.0, ge=0.2, le=3.0, description="Speech speed factor")
    speaker: Optional[str] = Field(None, description="Speaker name (e.g. EN_INDIA, EN_US, etc.)")
    lang: Optional[str] = Field("en-IN", description="Language code")
    style: Optional[str] = Field("default", description="Voice style")


class BatchSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    lang: Optional[str] = "en-IN"
    style: Optional[str] = "default"
    speed: Optional[float] = 1.0
    speaker: Optional[str] = None


def _verify_api_key(x_api_key: Optional[str] = None):
    """Check API key if MELO_API_KEY environment variable is configured."""
    if tts_engine.API_KEY and x_api_key != tts_engine.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )


@router.get("/health", summary="TTS & System Health Check")
@router.get("/tts/health", summary="TTS Health Check")
async def tts_health():
    """Health check returning MeloTTS model and engine status."""
    return tts_engine.get_status()


@router.post(
    "/tts",
    summary="Direct TTS synthesis",
    description="Synthesize text to speech immediately. Returns JSON with base64 audio or raw audio/wav."
)
async def synthesize_direct(
    payload: Optional[TTSRequest] = None,
    text: Optional[str] = Query(None, description="Text if passed via query params"),
    speed: float = Query(1.0, ge=0.2, le=3.0),
    speaker: Optional[str] = Query(None),
    lang: Optional[str] = Query("en-IN"),
    format: Optional[Literal["json", "wav"]] = Query("json"),
    request: Request = None,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    _verify_api_key(x_api_key)

    input_text = (payload.text if payload else None) or text
    input_speed = (payload.speed if payload else None) or speed
    input_speaker = (payload.speaker if payload else None) or speaker
    input_lang = (payload.lang if payload else None) or lang

    if not input_text or not input_text.strip():
        raise HTTPException(status_code=400, detail="Field 'text' is required.")

    try:
        b64, wav_bytes, sr, latency = tts_engine.synthesize(
            text=input_text,
            speed=input_speed,
            speaker_name=input_speaker
        )

        accept_header = request.headers.get("accept", "") if request else ""
        if format == "wav" or "audio/wav" in accept_header or "audio/*" in accept_header:
            return Response(
                content=wav_bytes,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": 'inline; filename="speech.wav"',
                    "X-Latency-Ms": str(latency),
                    "X-Sample-Rate": str(sr),
                }
            )

        return {
            "status": "completed",
            "audio_b64": b64,
            "sample_rate": sr,
            "latency_ms": latency,
            "speaker": input_speaker or tts_engine.SPEAKER,
            "language": input_lang,
            "text_length": len(input_text),
        }

    except Exception as e:
        logger.exception("TTS direct synthesis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {e}") from e


@router.post(
    "/batch/synthesize",
    status_code=status.HTTP_201_CREATED,
    summary="Batch synthesis job creation (Gonzaga App compatible)"
)
@router.post(
    "/tts/synthesize",
    status_code=status.HTTP_201_CREATED,
    summary="Batch synthesis job creation (/tts/synthesize)"
)
@router.post(
    "/tts/batch/synthesize",
    status_code=status.HTTP_201_CREATED,
    summary="Batch synthesis job creation (/tts/batch/synthesize)"
)
async def batch_synthesize(
    req: BatchSynthesizeRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    _verify_api_key(x_api_key)

    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    job_id = "melo_" + hashlib.sha1(f"{time.time()}|{text}".encode("utf-8")).hexdigest()[:16]
    tts_engine.register_job(job_id, {"status": "processing"})

    try:
        b64, _, sr, latency = tts_engine.synthesize(
            text=text,
            speed=req.speed or 1.0,
            speaker_name=req.speaker
        )
        tts_engine.register_job(job_id, {
            "status": "completed",
            "audio_b64": b64,
            "sample_rate": sr,
            "latency_ms": latency,
            "language": req.lang or "en-IN",
            "style": req.style or "default",
        })
        logger.info("[batch] %s completed (%d ms, %d chars)", job_id, latency, len(text))
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "job_id": job_id,
                "status": "completed",
                "language": req.lang or "en-IN",
                "style": req.style or "default",
                "text_length": len(text),
            }
        )
    except Exception as e:
        logger.exception("Batch synthesis failed for job %s: %s", job_id, e)
        tts_engine.register_job(job_id, {"status": "failed", "error": str(e)})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"synthesis failed: {e}", "job_id": job_id}
        )


@router.get(
    "/batch/result/{job_id}",
    summary="Retrieve batch synthesis result (Gonzaga App compatible)"
)
@router.get(
    "/tts/result/{job_id}",
    summary="Retrieve batch synthesis result (/tts/result/{job_id})"
)
@router.get(
    "/tts/batch/result/{job_id}",
    summary="Retrieve batch synthesis result (/tts/batch/result/{job_id})"
)
async def get_batch_result(
    job_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    _verify_api_key(x_api_key)

    job = tts_engine.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Job not found", "job_id": job_id}
        )

    job_status = job.get("status")
    if job_status == "completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "audio_b64": job["audio_b64"],
            "sample_rate": job["sample_rate"],
            "latency_ms": job["latency_ms"],
            "language": job.get("language", "en-IN"),
            "style": job.get("style", "default"),
        }
    elif job_status == "failed":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"job_id": job_id, "status": "failed", "error": job.get("error", "synthesis failed")}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"job_id": job_id, "status": job.get("status", "processing")}
        )
