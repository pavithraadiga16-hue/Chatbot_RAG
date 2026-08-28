"""
MeloTTS mascot voice server (Phinsiq) — CPU-only, self-hosted, MIT model.

Speaks the SAME batch REST API the Gonzaga app already calls:
  GET  /health
  POST /batch/synthesize   {"text": "...", "lang": "en-IN", "style": "default"}
        -> 201 {"job_id","status":"completed","language","style","text_length"}
  GET  /batch/result/{job_id}
        -> 200 {"job_id","status":"completed","audio_b64","sample_rate","latency_ms",...}
        -> 202 {"job_id","status":"processing"} | 404 if unknown

Design notes:
- MeloTTS EN_INDIA generates ~1.6 s per phrase on CPU (RTF ~0.47), so we
  synthesize synchronously inside the POST and mark the job completed
  immediately -> the app's first poll returns 200 with no extra delay.
- stdlib ThreadingHTTPServer: no asyncio, no POSIX signal handler -> boots
  cleanly on Windows (unlike the Indic-Parler websockets server).
- A single inference lock serializes model calls (MeloTTS isn't guaranteed
  thread-safe); an in-memory cache makes repeated phrases instant.
- Output is peak-normalized (MeloTTS is quiet, ~0.37 peak) so it's audible
  on a phone speaker.
"""
import os
os.environ.setdefault("PYTHONUTF8", "1")
import io
import json
import time
import base64
import hashlib
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import numpy as np
import soundfile as sf
import torch

# Thread count: default min(cores, 10). Override with MELO_THREADS on a box with
# a different CPU (e.g. a 2-vCPU cloud server -> MELO_THREADS=2).
torch.set_num_threads(
    int(os.environ.get("MELO_THREADS", str(min(os.cpu_count() or 4, 10))))
)

from melo.api import TTS

# ---- config (all overridable via environment variables for production) ----
HOST = os.environ.get("MELO_HOST", "0.0.0.0")   # LAN default; use 127.0.0.1 behind a proxy
PORT = int(os.environ.get("MELO_PORT", "8092"))
SPEAKER = os.environ.get("MELO_SPEAKER", "EN_INDIA")  # Indian-English speaker
API_KEY = os.environ.get("MELO_API_KEY", "").strip()  # if set, require X-API-Key header
TARGET_PEAK = 0.95        # peak-normalize loudness for phone speakers
CACHE_CAP = 256
JOBS_CAP = 200

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MeloTTS] %(levelname)s %(message)s",
)
log = logging.getLogger("melo")

# ---- load model ----
log.info("Loading MeloTTS English model (CPU, %d threads)...", torch.get_num_threads())
_t = time.time()
_model = TTS(language="EN", device="cpu")
_spk2id = _model.hps.data.spk2id
if SPEAKER not in _spk2id:
    raise SystemExit(f"Speaker {SPEAKER!r} not found; available: {list(_spk2id.keys())}")
_SID = _spk2id[SPEAKER]
_SR = int(_model.hps.data.sampling_rate)
log.info("Model loaded in %.1fs | speaker=%s sid=%s sample_rate=%d",
         time.time() - _t, SPEAKER, _SID, _SR)

# ---- state ----
_infer_lock = threading.Lock()
_state_lock = threading.Lock()
_cache = {}          # key -> (audio_b64, sample_rate, latency_ms)
_cache_order = []
_jobs = {}           # job_id -> {status, audio_b64, sample_rate, latency_ms}
_jobs_order = []
_start_time = time.time()


def _synthesize(text, speed=1.0):
    """Return (audio_b64_wav, sample_rate, latency_ms). Thread-safe + cached."""
    key = hashlib.sha1(f"{SPEAKER}|{speed}|{text}".encode("utf-8")).hexdigest()
    with _state_lock:
        hit = _cache.get(key)
    if hit:
        return hit[0], hit[1], 1  # cache hit ~instant

    with _infer_lock:
        # re-check: another thread may have generated the same text meanwhile
        with _state_lock:
            hit = _cache.get(key)
        if hit:
            return hit[0], hit[1], 1

        t0 = time.time()
        audio = _model.tts_to_file(text, _SID, output_path=None, speed=speed, quiet=True)
        audio = np.asarray(audio, dtype=np.float32).squeeze()
        if audio.size == 0:
            raise ValueError("MeloTTS produced empty audio")
        peak = float(np.abs(audio).max())
        if peak > 1e-6:
            audio = audio * (TARGET_PEAK / peak)  # normalize loudness
        buf = io.BytesIO()
        sf.write(buf, audio, _SR, format="WAV", subtype="PCM_16")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        latency = int((time.time() - t0) * 1000)

        with _state_lock:
            _cache[key] = (b64, _SR, latency)
            _cache_order.append(key)
            while len(_cache_order) > CACHE_CAP:
                old = _cache_order.pop(0)
                _cache.pop(old, None)
        return b64, _SR, latency


def _register_job(job_id, payload):
    with _state_lock:
        _jobs[job_id] = payload
        _jobs_order.append(job_id)
        while len(_jobs_order) > JOBS_CAP:
            old = _jobs_order.pop(0)
            _jobs.pop(old, None)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # keep-alive; we always send Content-Length

    def _send(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # route stdlib logs through our logger
        log.info("%s %s", self.address_string(), fmt % args)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            with _state_lock:
                cache_size = len(_cache)
            self._send(200, {
                "status": "ok",
                "model": "melotts-english",
                "speaker": SPEAKER,
                "device": "cpu",
                "sample_rate": _SR,
                "cache_size": cache_size,
                "uptime_seconds": round(time.time() - _start_time, 1),
            })
            return
        if path.startswith("/batch/result/"):
            if API_KEY and self.headers.get("X-API-Key") != API_KEY:
                self._send(401, {"error": "unauthorized"})
                return
            job_id = path.rsplit("/", 1)[-1]
            with _state_lock:
                job = _jobs.get(job_id)
            if not job:
                self._send(404, {"error": "Job not found", "job_id": job_id})
                return
            if job.get("status") == "completed":
                self._send(200, {
                    "job_id": job_id,
                    "status": "completed",
                    "audio_b64": job["audio_b64"],
                    "sample_rate": job["sample_rate"],
                    "latency_ms": job["latency_ms"],
                    "language": "en-IN",
                    "style": "default",
                })
            elif job.get("status") == "failed":
                self._send(500, {"job_id": job_id, "status": "failed",
                                 "error": job.get("error", "synthesis failed")})
            else:
                self._send(202, {"job_id": job_id, "status": job.get("status", "processing")})
            return
        self._send(404, {"error": "not found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/batch/synthesize":
            self._send(404, {"error": "not found", "path": path})
            return
        if API_KEY and self.headers.get("X-API-Key") != API_KEY:
            self._send(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            self._send(400, {"error": f"bad request: {e}"})
            return

        text = (data.get("text") or "").strip()
        if not text:
            self._send(400, {"error": "text is required"})
            return
        speed = float(data.get("speed", 1.0))
        job_id = "melo_" + hashlib.sha1(
            f"{time.time()}|{text}".encode("utf-8")).hexdigest()[:16]
        _register_job(job_id, {"status": "processing"})

        try:
            b64, sr, latency = _synthesize(text, speed=speed)
            _register_job(job_id, {
                "status": "completed",
                "audio_b64": b64,
                "sample_rate": sr,
                "latency_ms": latency,
            })
            log.info("[batch] %s completed (%d ms, %d chars)", job_id, latency, len(text))
            self._send(201, {
                "job_id": job_id,
                "status": "completed",
                "language": data.get("lang", "en-IN"),
                "style": data.get("style", "default"),
                "text_length": len(text),
            })
        except Exception as e:
            log.exception("synthesis failed")
            _register_job(job_id, {"status": "failed", "error": str(e)})
            self._send(500, {"error": f"synthesis failed: {e}", "job_id": job_id})


def main():
    # Warm-up: first tts call loads the BERT text-encoder (~40s once); after
    # this every request is ~1.6s regardless of text.
    log.info("Warming up (loading BERT text-encoder)...")
    _w = time.time()
    try:
        _synthesize("Hello there, friends!", speed=1.0)
        log.info("Warm-up complete in %.1fs — server is now fast (~1.6s/phrase)",
                 time.time() - _w)
    except Exception as e:
        log.warning("Warm-up failed (%r); starting anyway", e)

    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    log.info("MeloTTS server listening on http://%s:%d  (speaker=%s)", HOST, PORT, SPEAKER)
    log.info("Reachable from a phone on this Wi-Fi at http://<PC-LAN-IP>:%d", PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        httpd.shutdown()


if __name__ == "__main__":
    main()
