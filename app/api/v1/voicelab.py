"""
VoiceLab MeloTTS — All Voices Edition
=======================================

Exact concept from vexyl-tts-poc/voicelab/server.py, ported into PhinsIQ
as a dedicated FastAPI router. The synthesis logic, speaker resolution,
caching, and batch job tracking are kept verbatim from the original POC.

Routes (mounted at /api/v1/voicelab):
    GET  /health              -> model status, speaker count, uptime, cache
    GET  /speakers            -> [{id, key, name, accent, flag}]
    POST /synthesize          -> binary audio/wav stream (direct, no base64)
                                body: {text, speaker?, speed?}
    POST /batch/synthesize    -> legacy compat: {job_id, status, ...}
                                body: {text, speaker?, speed?, lang?, style?}
    GET  /batch/result/{id}   -> legacy compat result poll
"""

import base64
import hashlib
import io
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["VoiceLab — All Voices Edition"])

# ── Speaker metadata (verbatim from voicelab/server.py) ───────────────────────
SPEAKER_META: Dict[str, Dict[str, str]] = {
    "EN-Default": {"name": "Alex (Neutral)",     "accent": "Neutral English",    "flag": "🌐"},
    "EN-US":      {"name": "Sam (American)",      "accent": "American English",   "flag": "🇺🇸"},
    "EN-BR":      {"name": "Oliver (British)",    "accent": "British English",    "flag": "🇬🇧"},
    "EN_INDIA":   {"name": "Priya (Indian)",      "accent": "Indian English",     "flag": "🇮🇳"},
    "EN-AU":      {"name": "Lena (Australian)",   "accent": "Australian English", "flag": "🇦🇺"},
}

TARGET_PEAK: float = 0.95
CACHE_CAP:   int   = 512
JOBS_CAP:    int   = 256

# ── Internal state (verbatim from voicelab/server.py) ─────────────────────────
_infer_lock  = threading.Lock()
_state_lock  = threading.Lock()
_cache: Dict[str, Tuple[bytes, int]] = {}
_cache_order: List[str] = []
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_order: List[str] = []
_start_time: float = time.time()

# Lazy model references
_model: Any = None
_spk2id: Dict[str, int] = {}
_sr: int = 44100
_available_speakers: List[Dict[str, str]] = []
_init_lock = threading.Lock()
_initialized = False
_init_error: Optional[str] = None


# ── Model initialisation (lazy, once) ─────────────────────────────────────────

def _resolve_speaker_key(spk: str) -> Optional[str]:
    """Return exact speaker key as known to _spk2id, or None.
    Verbatim from voicelab/server.py _resolve_speaker()."""
    if spk in _spk2id:
        return spk
    alt = spk.replace("-", "_")
    if alt in _spk2id:
        return alt
    alt2 = spk.replace("_", "-")
    if alt2 in _spk2id:
        return alt2
    return None


def _ensure_model() -> None:
    """Lazily load MeloTTS exactly as voicelab/server.py does."""
    global _model, _spk2id, _sr, _available_speakers, _initialized, _init_error

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return
        try:
            import os
            import torch
            from melo.api import TTS

            torch.set_num_threads(
                int(os.environ.get("MELO_THREADS", str(min(os.cpu_count() or 4, 10))))
            )

            logger.info("voicelab_loading_model", device="cpu")
            t0 = time.time()
            _model = TTS(language="EN", device="cpu")
            _spk2id = dict(_model.hps.data.spk2id.items())
            _sr = int(_model.hps.data.sampling_rate)

            # Build advertised speaker list — verbatim from voicelab/server.py
            available: List[Dict[str, str]] = []
            for spk_id, meta in SPEAKER_META.items():
                key = _resolve_speaker_key(spk_id)
                if key:
                    available.append({
                        "id":     spk_id,
                        "key":    key,
                        "name":   meta["name"],
                        "accent": meta["accent"],
                        "flag":   meta["flag"],
                    })

            # Also add any model speakers not in our metadata
            for k in _spk2id.keys():
                if not any(s["key"] == k for s in available):
                    available.append({"id": k, "key": k, "name": k, "accent": "Unknown", "flag": "🎤"})

            _available_speakers = available
            logger.info(
                "voicelab_model_loaded",
                duration_s=round(time.time() - t0, 2),
                speakers=[s["id"] for s in _available_speakers],
                sample_rate=_sr,
            )
        except ImportError as e:
            _init_error = f"TTS dependencies not installed: {e}"
            logger.warning("voicelab_dependencies_missing", error=str(e))
        except Exception as e:
            _init_error = f"VoiceLab init failed: {e}"
            logger.error("voicelab_init_failed", error=str(e))
        finally:
            _initialized = True


# ── Core synthesis (verbatim from voicelab/server.py _synthesize_wav) ─────────

def _synthesize_wav(text: str, speaker_key: str, speed: float = 1.0) -> Tuple[bytes, int]:
    """Return (wav_bytes, latency_ms). Thread-safe + in-memory cached."""
    import numpy as np
    import soundfile as sf

    cache_key = hashlib.sha1(
        f"{speaker_key}|{speed:.3f}|{text}".encode("utf-8")
    ).hexdigest()

    with _state_lock:
        hit = _cache.get(cache_key)
    if hit:
        return hit[0], 1

    with _infer_lock:
        with _state_lock:
            hit = _cache.get(cache_key)
        if hit:
            return hit[0], 1

        sid = _spk2id[speaker_key]
        t0  = time.time()
        audio = _model.tts_to_file(text, sid, output_path=None, speed=speed, quiet=True)
        audio = np.asarray(audio, dtype=np.float32).squeeze()
        if audio.size == 0:
            raise ValueError("MeloTTS produced empty audio")
        peak = float(np.abs(audio).max())
        if peak > 1e-6:
            audio = audio * (TARGET_PEAK / peak)
        buf = io.BytesIO()
        sf.write(buf, audio, _sr, format="WAV", subtype="PCM_16")
        wav_bytes = buf.getvalue()
        latency = int((time.time() - t0) * 1000)

        with _state_lock:
            _cache[cache_key] = (wav_bytes, latency)
            _cache_order.append(cache_key)
            while len(_cache_order) > CACHE_CAP:
                _cache.pop(_cache_order.pop(0), None)

    return wav_bytes, latency


def _b64_synthesize(text: str, speaker_key: str, speed: float = 1.0):
    wav, latency = _synthesize_wav(text, speaker_key, speed)
    return base64.b64encode(wav).decode("ascii"), _sr, latency


def _register_job(job_id: str, payload: Dict[str, Any]) -> None:
    with _state_lock:
        _jobs[job_id] = payload
        _jobs_order.append(job_id)
        while len(_jobs_order) > JOBS_CAP:
            _jobs.pop(_jobs_order.pop(0), None)


def _check_api_key(x_api_key: Optional[str]) -> None:
    if settings.tts_api_key and x_api_key != settings.tts_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized"},
        )


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class VoiceLabSynthRequest(BaseModel):
    text:    str           = Field(..., min_length=1, description="Text to synthesize")
    speaker: Optional[str] = Field(None,              description="Speaker id (e.g. EN-US, EN_INDIA)")
    speed:   float         = Field(1.0,  ge=0.5, le=2.0, description="Speech speed")


class VoiceLabBatchRequest(BaseModel):
    text:    str           = Field(..., min_length=1)
    speaker: Optional[str] = Field(None)
    speed:   float         = Field(1.0, ge=0.5, le=2.0)
    lang:    Optional[str] = Field("en-IN")
    style:   Optional[str] = Field("default")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/health", summary="VoiceLab health — model status, speaker count, uptime, cache")
async def voicelab_health():
    """Returns VoiceLab TTS engine status, available speaker count, cache size, and uptime."""
    _ensure_model()
    with _state_lock:
        cs = len(_cache)
    return {
        "status":         "ok" if (_model is not None) else "unavailable",
        "model":          "melotts-english",
        "speakers":       len(_available_speakers),
        "sample_rate":    _sr,
        "cache_size":     cs,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "error":          _init_error,
    }


@router.get("/speakers", summary="List all available MeloTTS speaker voices")
async def voicelab_speakers() -> JSONResponse:
    """Returns the full speaker catalog: [{id, key, name, accent, flag}]."""
    _ensure_model()
    return JSONResponse({"speakers": _available_speakers})


@router.post(
    "/synthesize",
    summary="Synthesize text to raw audio/wav (all voices)",
    responses={200: {"content": {"audio/wav": {}}, "description": "Raw 16-bit PCM WAV stream."}},
)
async def voicelab_synthesize(
    request: VoiceLabSynthRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Direct text-to-WAV using the VoiceLab All-Voices engine.
    Returns binary audio/wav — no base64 wrapping — exactly as
    voicelab/server.py POST /synthesize.
    """
    _check_api_key(x_api_key)
    _ensure_model()

    if _model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_init_error or "VoiceLab TTS engine unavailable",
        )

    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "text is required"})

    req_spk = request.speaker or settings.tts_speaker
    spk_key = _resolve_speaker_key(req_spk)
    if not spk_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"unknown speaker: {req_spk!r}", "available": [s["id"] for s in _available_speakers]},
        )

    speed = max(0.5, min(request.speed, 2.0))

    try:
        import asyncio
        wav, latency = await asyncio.to_thread(_synthesize_wav, text, spk_key, speed)
        logger.info("voicelab_synth_ok", speaker=req_spk, chars=len(text), latency_ms=latency)
        return Response(
            content=wav,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'inline; filename="speech.wav"',
                "X-Latency-Ms":        str(latency),
                "X-Sample-Rate":       str(_sr),
                "X-Speaker":           spk_key,
            },
        )
    except Exception as exc:
        logger.exception("voicelab_synth_failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": str(exc)})


@router.post(
    "/batch/synthesize",
    status_code=status.HTTP_201_CREATED,
    summary="Batch synthesis job (legacy compat — returns job_id immediately)",
)
async def voicelab_batch_synthesize(
    request: VoiceLabBatchRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Creates an audio synthesis job synchronously, so the first poll always
    returns completed. Matches the exact batch API from voicelab/server.py.
    """
    _check_api_key(x_api_key)
    _ensure_model()

    if _model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_init_error or "VoiceLab TTS engine unavailable",
        )

    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "text is required"})

    req_spk = request.speaker
    spk_key = (
        _resolve_speaker_key(req_spk)
        if req_spk
        else (
            _resolve_speaker_key("EN_INDIA")
            or (_available_speakers[0]["key"] if _available_speakers else None)
        )
    )
    if not spk_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "no available speakers"})

    job_id = "melo_" + hashlib.sha1(f"{time.time()}|{text}".encode("utf-8")).hexdigest()[:16]
    _register_job(job_id, {"status": "processing"})

    try:
        import asyncio
        b64, sr, latency = await asyncio.to_thread(_b64_synthesize, text, spk_key, float(request.speed))
        _register_job(job_id, {"status": "completed", "audio_b64": b64, "sample_rate": sr, "latency_ms": latency})
        logger.info("voicelab_batch_ok", job_id=job_id, latency_ms=latency, chars=len(text))
        return {
            "job_id":      job_id,
            "status":      "completed",
            "language":    request.lang or "en-IN",
            "style":       request.style or "default",
            "text_length": len(text),
        }
    except Exception as exc:
        logger.exception("voicelab_batch_failed")
        _register_job(job_id, {"status": "failed", "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(exc), "job_id": job_id},
        )


@router.get("/batch/result/{job_id}", summary="Retrieve VoiceLab batch synthesis result")
async def voicelab_batch_result(
    job_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Polls and returns audio for a VoiceLab batch job. Verbatim from voicelab/server.py."""
    _check_api_key(x_api_key)

    with _state_lock:
        job = _jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Job not found", "job_id": job_id},
        )

    job_status = job.get("status")

    if job_status == "completed":
        return {
            "job_id":      job_id,
            "status":      "completed",
            "audio_b64":   job["audio_b64"],
            "sample_rate": job["sample_rate"],
            "latency_ms":  job["latency_ms"],
            "language":    "en-IN",
            "style":       "default",
        }
    elif job_status == "failed":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"job_id": job_id, "status": "failed", "error": job.get("error", "synthesis failed")},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"job_id": job_id, "status": job.get("status", "processing")},
        )
