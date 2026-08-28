"""
MeloTTS Engine Module for server_old.
Provides thread-safe synthesis, LRU caching, job management, and loudness normalization.
"""

import os
os.environ.setdefault("PYTHONUTF8", "1")

import io
import time
import base64
import hashlib
import logging
import threading
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("uvicorn.error")

# Configuration from environment variables
SPEAKER = os.environ.get("MELO_SPEAKER", "EN_INDIA")
API_KEY = os.environ.get("MELO_API_KEY", "").strip()
TARGET_PEAK = float(os.environ.get("MELO_TARGET_PEAK", "0.95"))
CACHE_CAP = int(os.environ.get("MELO_CACHE_CAP", "256"))
JOBS_CAP = int(os.environ.get("MELO_JOBS_CAP", "200"))
MELO_THREADS = int(os.environ.get("MELO_THREADS", str(min(os.cpu_count() or 4, 10))))

# State & locks
_infer_lock = threading.Lock()
_state_lock = threading.Lock()
_cache: Dict[str, Tuple[str, int, int]] = {}  # key -> (audio_b64, sample_rate, latency_ms)
_cache_order = []
_jobs: Dict[str, Dict[str, Any]] = {}  # job_id -> {status, audio_b64, sample_rate, latency_ms, ...}
_jobs_order = []
_start_time = time.time()

_model = None
_spk2id = {}
_SID = None
_SR = 44100
_is_initialized = False
_init_error: Optional[str] = None


def get_model():
    """Lazy initialize the MeloTTS model in a thread-safe manner."""
    global _model, _spk2id, _SID, _SR, _is_initialized, _init_error
    if _is_initialized:
        return _model
    if _init_error is not None:
        raise RuntimeError(f"MeloTTS initialization previously failed: {_init_error}")

    with _infer_lock:
        if _is_initialized:
            return _model
        try:
            import torch
            torch.set_num_threads(MELO_THREADS)
            logger.info("Loading MeloTTS English model (CPU, %d threads)...", MELO_THREADS)
            t0 = time.time()
            from melo.api import TTS
            model = TTS(language="EN", device="cpu")
            spk2id = model.hps.data.spk2id
            if SPEAKER not in spk2id:
                raise ValueError(f"Speaker {SPEAKER!r} not found; available: {list(spk2id.keys())}")
            
            _model = model
            _spk2id = spk2id
            _SID = spk2id[SPEAKER]
            _SR = int(model.hps.data.sampling_rate)
            _is_initialized = True
            logger.info(
                "MeloTTS model loaded in %.1fs | speaker=%s sid=%s sample_rate=%d",
                time.time() - t0, SPEAKER, _SID, _SR
            )
            return _model
        except Exception as e:
            _init_error = str(e)
            logger.exception("Failed to initialize MeloTTS engine: %s", e)
            raise


def is_ready() -> bool:
    """Check if MeloTTS is initialized and ready to serve."""
    return _is_initialized


def get_status() -> Dict[str, Any]:
    """Return health/status details of the TTS engine."""
    with _state_lock:
        cache_size = len(_cache)
        active_jobs = len(_jobs)
    return {
        "status": "ready" if _is_initialized else ("error" if _init_error else "uninitialized"),
        "model": "melotts-english",
        "speaker": SPEAKER,
        "device": "cpu",
        "sample_rate": _SR,
        "cache_size": cache_size,
        "jobs_tracked": active_jobs,
        "uptime_seconds": round(time.time() - _start_time, 1),
        "init_error": _init_error,
    }


def synthesize(text: str, speed: float = 1.0, speaker_name: Optional[str] = None) -> Tuple[str, bytes, int, int]:
    """
    Synthesize text to speech.
    Returns: (audio_b64, raw_wav_bytes, sample_rate, latency_ms)
    Thread-safe with LRU cache and loudness normalization.
    """
    import numpy as np
    import soundfile as sf

    text = (text or "").strip()
    if not text:
        raise ValueError("Text cannot be empty")

    model = get_model()
    target_speaker = speaker_name or SPEAKER
    sid = _spk2id.get(target_speaker, _SID)

    cache_key = hashlib.sha1(f"{target_speaker}|{speed}|{text}".encode("utf-8")).hexdigest()

    # 1. Cache hit check
    with _state_lock:
        hit = _cache.get(cache_key)
    if hit:
        b64, sr, _ = hit
        raw_wav = base64.b64decode(b64)
        return b64, raw_wav, sr, 1  # 1ms latency for cache hit

    # 2. Synthesize under inference lock
    with _infer_lock:
        # Re-check cache in case another thread just completed it
        with _state_lock:
            hit = _cache.get(cache_key)
        if hit:
            b64, sr, _ = hit
            raw_wav = base64.b64decode(b64)
            return b64, raw_wav, sr, 1

        t0 = time.time()
        audio = model.tts_to_file(text, sid, output_path=None, speed=speed, quiet=True)
        audio = np.asarray(audio, dtype=np.float32).squeeze()
        if audio.size == 0:
            raise ValueError("MeloTTS produced empty audio")

        peak = float(np.abs(audio).max())
        if peak > 1e-6:
            audio = audio * (TARGET_PEAK / peak)  # Normalize loudness for speakers

        buf = io.BytesIO()
        sf.write(buf, audio, _SR, format="WAV", subtype="PCM_16")
        raw_wav = buf.getvalue()
        b64 = base64.b64encode(raw_wav).decode("ascii")
        latency = max(1, int((time.time() - t0) * 1000))

        # Store in LRU cache
        with _state_lock:
            _cache[cache_key] = (b64, _SR, latency)
            _cache_order.append(cache_key)
            while len(_cache_order) > CACHE_CAP:
                old = _cache_order.pop(0)
                _cache.pop(old, None)

        return b64, raw_wav, _SR, latency


def register_job(job_id: str, payload: Dict[str, Any]):
    """Register or update an async/batch job status."""
    with _state_lock:
        _jobs[job_id] = payload
        _jobs_order.append(job_id)
        while len(_jobs_order) > JOBS_CAP:
            old = _jobs_order.pop(0)
            _jobs.pop(old, None)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve job information by job_id."""
    with _state_lock:
        return _jobs.get(job_id)


def warmup():
    """Warm up the model (downloads/loads BERT text-encoder) on server startup."""
    try:
        get_model()
        logger.info("Warming up MeloTTS BERT text-encoder...")
        w_start = time.time()
        synthesize("Hello there, friends!", speed=1.0)
        logger.info("MeloTTS warm-up completed in %.1fs", time.time() - w_start)
    except Exception as e:
        logger.warning("MeloTTS warm-up failed or skipped: %s", e)
