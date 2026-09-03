"""
PhinsIQ - MeloTTS Speech Synthesis Service
===========================================

PURPOSE:
    Centralized service for offline, CPU-based Text-to-Speech (TTS) using MeloTTS.
    Provides thread-safe audio synthesis, peak loudness normalization,
    in-memory phrase caching, and job tracking for mobile/batch clients.

FEATURES:
    - Thread-safe model inference serialized with threading.Lock
    - Non-blocking async execution using asyncio.to_thread
    - LRU in-memory cache for instant repeated phrase synthesis
    - Graceful fallback & dependency checks if melo/torch/soundfile are missing
    - Multi-accent English voice catalog (Indian, American, British, Australian)
"""

import asyncio
import base64
import hashlib
import io
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SPEAKER_META: Dict[str, Dict[str, str]] = {
    "EN_INDIA": {"name": "Priya (Indian)", "accent": "Indian English (en-IN)", "flag": "🇮🇳"},
    "EN-Default": {"name": "Alex (Neutral)", "accent": "Neutral English", "flag": "🌐"},
    "EN-US": {"name": "Sam (American)", "accent": "American English", "flag": "🇺🇸"},
    "EN-BR": {"name": "Oliver (British)", "accent": "British English", "flag": "🇬🇧"},
    "EN-AU": {"name": "Lena (Australian)", "accent": "Australian English", "flag": "🇦🇺"},
}


class TTSService:
    """
    Singleton service managing the MeloTTS synthesis engine.
    """

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._infer_lock = threading.Lock()
        self._state_lock = threading.Lock()

        # Cache: hash -> (wav_bytes, latency_ms)
        self._cache: Dict[str, Tuple[bytes, int]] = {}
        self._cache_order: List[str] = []

        # Batch jobs: job_id -> dict
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._jobs_order: List[str] = []
        self._jobs_cap: int = 256

        # Lazy model references
        self._model: Any = None
        self._spk2id: Dict[str, int] = {}
        self._sample_rate: int = 44100
        self._available: bool = False
        self._init_error: Optional[str] = None
        self._initialized: bool = False

    def _ensure_initialized(self) -> None:
        """
        Safely and lazily initializes MeloTTS and PyTorch dependencies.
        Ensures PhinsIQ startup is never blocked or crashed if ML libraries are missing.
        """
        if self._initialized:
            return

        with self._infer_lock:
            if self._initialized:
                return

            try:
                import soundfile  # noqa: F401
                import torch
                from melo.api import TTS

                # Determine compute device
                device = settings.tts_device.lower()
                if device == "auto":
                    if torch.cuda.is_available():
                        target_device = "cuda"
                    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        target_device = "mps"
                    else:
                        target_device = "cpu"
                else:
                    target_device = device

                # Set PyTorch thread count for CPU inference
                if target_device == "cpu":
                    torch.set_num_threads(settings.tts_threads)

                logger.info(
                    "melo_tts_loading_model",
                    device=target_device,
                    threads=settings.tts_threads,
                    default_speaker=settings.tts_speaker,
                    default_speed=settings.tts_speed,
                )
                # Ensure NLTK English taggers and cmudict are available for g2p_en / MeloTTS
                try:
                    import nltk
                    import ssl
                    try:
                        ssl._create_default_https_context = ssl._create_unverified_context
                    except AttributeError:
                        pass
                    for pkg in ("averaged_perceptron_tagger_eng", "averaged_perceptron_tagger", "cmudict"):
                        try:
                            nltk.download(pkg, quiet=True)
                        except Exception:
                            pass
                except Exception:
                    pass

                t0 = time.time()
                self._model = TTS(language="EN", device=target_device)
                self._spk2id = dict(self._model.hps.data.spk2id.items())
                self._sample_rate = int(self._model.hps.data.sampling_rate)
                self._available = True
                self._init_error = None

                logger.info(
                    "melo_tts_model_loaded",
                    duration_s=round(time.time() - t0, 2),
                    available_speakers=list(self._spk2id.keys()),
                    sample_rate=self._sample_rate,
                )
            except ImportError as e:
                self._available = False
                self._init_error = (
                    f"TTS dependencies not installed: {e}. "
                    "Run 'pip install melotts soundfile' with PyTorch to enable TTS."
                )
                logger.warning("melo_tts_dependencies_missing", error=str(e))
            except Exception as e:
                self._available = False
                self._init_error = f"Failed to initialize MeloTTS engine: {e}"
                logger.error("melo_tts_init_failed", error=str(e))
            finally:
                self._initialized = True

    @property
    def is_available(self) -> bool:
        """Return True if TTS engine and dependencies are available."""
        self._ensure_initialized()
        return self._available

    @property
    def init_error(self) -> Optional[str]:
        self._ensure_initialized()
        return self._init_error

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 1)

    @property
    def cache_size(self) -> int:
        with self._state_lock:
            return len(self._cache)

    def resolve_speaker_key(self, speaker_input: Optional[str] = None) -> str:
        """
        Resolves speaker key matching model dictionaries, supporting both
        'en-IN', 'EN-INDIA', and 'EN_INDIA' formatting.
        """
        self._ensure_initialized()
        target = (speaker_input or settings.tts_speaker).strip()

        # Direct exact match
        if target in self._spk2id:
            return target

        # Language code / shorthand mapping
        low = target.lower()
        if low in ("en-in", "en_in", "en-india", "en_india", "india", "indian"):
            return "EN_INDIA" if "EN_INDIA" in self._spk2id else target
        if low in ("en-us", "en_us", "us", "american"):
            return "EN-US" if "EN-US" in self._spk2id else target
        if low in ("en-br", "en_br", "br", "british", "uk"):
            return "EN-BR" if "EN-BR" in self._spk2id else target
        if low in ("en-au", "en_au", "au", "australian"):
            return "EN-AU" if "EN-AU" in self._spk2id else target
        if low in ("en-default", "en_default", "default", "neutral"):
            return "EN-Default" if "EN-Default" in self._spk2id else target

        alt_under = target.replace("-", "_")
        if alt_under in self._spk2id:
            return alt_under

        alt_dash = target.replace("_", "-")
        if alt_dash in self._spk2id:
            return alt_dash

        # Fallback to configured default or first available speaker
        if settings.tts_speaker in self._spk2id:
            return settings.tts_speaker

        if self._spk2id:
            return next(iter(self._spk2id.keys()))

        return target

    def get_available_speakers(self) -> List[Dict[str, str]]:
        """Return metadata list of supported speaker voices."""
        self._ensure_initialized()
        speakers: List[Dict[str, str]] = []

        # Standard known metadata
        for spk_id, meta in SPEAKER_META.items():
            resolved = self.resolve_speaker_key(spk_id) if self._spk2id else spk_id
            speakers.append({
                "id": spk_id,
                "name": meta["name"],
                "accent": meta["accent"],
                "flag": meta["flag"],
            })

        # Extra speakers detected in model
        if self._spk2id:
            for k in self._spk2id.keys():
                if not any(s["id"] == k or s["id"].replace("-", "_") == k for s in speakers):
                    speakers.append({
                        "id": k,
                        "name": k,
                        "accent": "English",
                        "flag": "🎙️",
                    })

        return speakers

    def _synthesize_sync(
        self,
        text: str,
        speaker_key: str,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
    ) -> Tuple[bytes, int]:
        """
        Synchronous audio synthesis execution with locking, caching, and child pitch transformation.
        Should be called via asyncio.to_thread in async routes.
        """
        import numpy as np
        import soundfile as sf

        target_speed = float(speed if speed is not None else settings.tts_speed)
        target_pitch = float(pitch if pitch is not None else settings.tts_pitch)
        cache_key = hashlib.sha1(f"{speaker_key}|{target_speed:.3f}|{target_pitch:.2f}|{text}".encode("utf-8")).hexdigest()

        # Check cache under state lock
        with self._state_lock:
            if cache_key in self._cache:
                return self._cache[cache_key][0], 1

        # Perform inference under inference lock
        with self._infer_lock:
            # Re-check cache in case another worker synthesized it while waiting
            with self._state_lock:
                if cache_key in self._cache:
                    return self._cache[cache_key][0], 1

            if not self._available or not self._model:
                raise RuntimeError(self._init_error or "TTS model is not available")

            sid = self._spk2id.get(speaker_key)
            if sid is None:
                raise ValueError(f"Speaker '{speaker_key}' not found in MeloTTS model")

            t0 = time.time()
            audio = self._model.tts_to_file(text, sid, output_path=None, speed=target_speed, quiet=True)
            audio = np.asarray(audio, dtype=np.float32).squeeze()

            if audio.size == 0:
                raise ValueError("MeloTTS produced empty audio output")

            # Authentic Small Child Voice transformation via pitch shifting (+5.0 semitones)
            if abs(target_pitch) > 0.05:
                try:
                    import torch
                    import torchaudio
                    waveform = torch.from_numpy(audio).unsqueeze(0)
                    shifted = torchaudio.functional.pitch_shift(waveform, self._sample_rate, n_steps=target_pitch)
                    audio = shifted.squeeze(0).numpy()
                except Exception as e:
                    logger.warning("pitch_shift_fallback", error=str(e))

            # Loudness peak normalization for phone speakers
            peak = float(np.abs(audio).max())
            if peak > 1e-6:
                audio = audio * (settings.tts_target_peak / peak)

            buf = io.BytesIO()
            sf.write(buf, audio, self._sample_rate, format="WAV", subtype="PCM_16")
            wav_bytes = buf.getvalue()
            latency_ms = max(1, int((time.time() - t0) * 1000))

            # Store in cache
            with self._state_lock:
                self._cache[cache_key] = (wav_bytes, latency_ms)
                self._cache_order.append(cache_key)
                while len(self._cache_order) > settings.tts_cache_cap:
                    evicted = self._cache_order.pop(0)
                    self._cache.pop(evicted, None)

            return wav_bytes, latency_ms

    async def synthesize_wav(
        self,
        text: str,
        speaker: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
    ) -> Tuple[bytes, int]:
        """
        Asynchronously synthesize text to 16-bit PCM WAV bytes without blocking event loop.
        """
        self._ensure_initialized()
        if not self._available:
            raise RuntimeError(self._init_error or "TTS engine unavailable")

        speaker_key = self.resolve_speaker_key(speaker)
        target_speed = speed if speed is not None else settings.tts_speed
        target_pitch = pitch if pitch is not None else settings.tts_pitch
        return await asyncio.to_thread(self._synthesize_sync, text, speaker_key, target_speed, target_pitch)

    async def synthesize_base64(
        self,
        text: str,
        speaker: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
    ) -> Tuple[str, int, int]:
        """
        Synthesizes text and returns (audio_b64, sample_rate, latency_ms).
        """
        target_speed = speed if speed is not None else settings.tts_speed
        target_pitch = pitch if pitch is not None else settings.tts_pitch
        wav_bytes, latency_ms = await self.synthesize_wav(text, speaker, target_speed, target_pitch)
        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
        return audio_b64, self._sample_rate, latency_ms

    def register_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        """Register or update status of a batch synthesis job."""
        with self._state_lock:
            self._jobs[job_id] = payload
            self._jobs_order.append(job_id)
            while len(self._jobs_order) > self._jobs_cap:
                evicted = self._jobs_order.pop(0)
                self._jobs.pop(evicted, None)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the payload of a batch job."""
        with self._state_lock:
            return self._jobs.get(job_id)


# Global singleton instance
tts_service = TTSService()
