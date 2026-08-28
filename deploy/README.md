# AI Parrophins Server Deployment Guide

Production server hosting **Universal File Compressor** (`/compress_same`) and **MeloTTS Voice Server** (`/tts` & batch endpoints).

---

## 1. Quick Setup (Python 3.12.3)

Run the setup script inside `server_old`:

```bash
cd /home/backend-ai/htdocs/ai.parrophins.in
bash setup_venv.sh
```

This automatically:
- Prepares the Python 3.12.3 virtual environment in `./venv`
- Installs CPU-only PyTorch and all dependencies
- Installs MeloTTS and required NLTK taggers
- Verifies installation

---

## 2. API Endpoints

### 1. File Compression: `POST /compress_same`
- **URL**: `https://ai.parrophins.in/compress_same`
- **Supported Formats**: PDF (smart image-only downscaling, vector text untouched), DOCX, JPEG, PNG, WEBP, GIF, BMP, TIFF, ICO.
- **Example cURL**:
  ```bash
  curl -X POST "https://ai.parrophins.in/compress_same?target_kb=200" \
    -F "file=@sample.pdf" \
    --output compressed_sample.pdf
  ```

---

### 2. MeloTTS Voice Direct: `POST /tts`
- **URL**: `https://ai.parrophins.in/tts`
- **Payload** (JSON):
  ```json
  {
    "text": "Welcome to AI Parrophins mascot voice service!",
    "speed": 1.0,
    "speaker": "EN_INDIA",
    "lang": "en-IN"
  }
  ```
- **Response**:
  ```json
  {
    "status": "completed",
    "audio_b64": "UklGRi...",
    "sample_rate": 44100,
    "latency_ms": 140,
    "speaker": "EN_INDIA",
    "language": "en-IN",
    "text_length": 46
  }
  ```
- **Direct WAV streaming** (Optional):
  ```bash
  curl -X POST "https://ai.parrophins.in/tts?format=wav" \
    -H "Content-Type: application/json" \
    -d '{"text": "Hello world"}' \
    --output speech.wav
  ```

---

### 3. Gonzaga Mascot App / Batch API: `POST /batch/synthesize` & `GET /batch/result/{job_id}`
- **Create Job**: `POST https://ai.parrophins.in/batch/synthesize`
  ```bash
  curl -X POST "https://ai.parrophins.in/batch/synthesize" \
    -H "Content-Type: application/json" \
    -d '{"text": "Hello friends", "lang": "en-IN", "style": "default"}'
  ```
  Returns `201 Created`:
  ```json
  {
    "job_id": "melo_9f83a81a17c2a4e1",
    "status": "completed",
    "language": "en-IN",
    "style": "default",
    "text_length": 13
  }
  ```
- **Fetch Result**: `GET https://ai.parrophins.in/batch/result/{job_id}`
  ```bash
  curl -X GET "https://ai.parrophins.in/batch/result/melo_9f83a81a17c2a4e1"
  ```

---

### 4. Health Check: `GET /health` & `GET /tts/health`
- **URL**: `https://ai.parrophins.in/health`
- **Response**:
  ```json
  {
    "status": "ready",
    "model": "melotts-english",
    "speaker": "EN_INDIA",
    "device": "cpu",
    "sample_rate": 44100,
    "cache_size": 12,
    "uptime_seconds": 1240.5
  }
  ```

---

## 3. Systemd Service Deployment

Copy and enable the systemd service file:

```bash
sudo cp deploy/ai_server.service /etc/systemd/system/ai_server.service
sudo systemctl daemon-reload
sudo systemctl enable --now ai_server
```

To monitor logs:
```bash
journalctl -u ai_server -f
```
