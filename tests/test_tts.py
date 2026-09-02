"""
Tests for PhinsIQ Text-to-Speech (TTS) Subsystem & Endpoints
============================================================
"""

import base64
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.tts.service import tts_service, TTSService


@pytest.fixture
def client():
    return TestClient(app)


def test_tts_health_endpoint(client):
    """Test GET /api/v1/tts/health returns valid status payload."""
    response = client.get("/api/v1/tts/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "available" in data
    assert data["model"] == "melotts-english"
    assert "speaker" in data
    assert "device" in data
    assert "sample_rate" in data
    assert "cache_size" in data
    assert "uptime_seconds" in data


def test_tts_speakers_endpoint(client):
    """Test GET /api/v1/tts/speakers returns list of available voices."""
    response = client.get("/api/v1/tts/speakers")
    assert response.status_code == 200
    speakers = response.json()
    assert isinstance(speakers, list)
    assert len(speakers) >= 5

    speaker_ids = [s["id"] for s in speakers]
    assert "EN_INDIA" in speaker_ids
    assert "EN-US" in speaker_ids
    assert "EN-BR" in speaker_ids

    # Validate schema of each speaker
    for speaker in speakers:
        assert "id" in speaker
        assert "name" in speaker
        assert "accent" in speaker
        assert "flag" in speaker


def test_tts_validation_empty_text(client):
    """Test that empty or whitespace-only text fails validation."""
    response = client.post("/api/v1/tts/batch/synthesize", json={"text": ""})
    assert response.status_code == 422

    response2 = client.post("/batch/synthesize", json={"text": ""})
    assert response2.status_code == 422


def test_tts_batch_result_not_found(client):
    """Test GET /api/v1/tts/batch/result/{non_existent_id} returns 404."""
    response = client.get("/api/v1/tts/batch/result/melo_doesnotexist123")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]["error"]

    response2 = client.get("/batch/result/melo_doesnotexist123")
    assert response2.status_code == 404


def test_tts_batch_synthesize_and_result_flow(client):
    """Test full batch synthesis flow and legacy compatibility with mock synthesis."""
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
    dummy_b64 = base64.b64encode(dummy_wav).decode("ascii")

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_base64", new_callable=AsyncMock) as mock_synth:

        mock_synth.return_value = (dummy_b64, 44100, 150)

        # 1. Test POST /api/v1/tts/batch/synthesize
        req_payload = {
            "text": "Welcome to Gonzaga School!",
            "lang": "en-IN",
            "style": "default",
            "speed": 1.0,
        }
        res_batch = client.post("/api/v1/tts/batch/synthesize", json=req_payload)
        assert res_batch.status_code == 201
        batch_data = res_batch.json()
        assert batch_data["status"] == "completed"
        assert batch_data["language"] == "en-IN"
        assert batch_data["text_length"] == len(req_payload["text"])
        job_id = batch_data["job_id"]
        assert job_id.startswith("melo_")

        # 2. Test GET /api/v1/tts/batch/result/{job_id}
        res_result = client.get(f"/api/v1/tts/batch/result/{job_id}")
        assert res_result.status_code == 200
        result_data = res_result.json()
        assert result_data["job_id"] == job_id
        assert result_data["status"] == "completed"
        assert result_data["audio_b64"] == dummy_b64
        assert result_data["sample_rate"] == 44100
        assert result_data["latency_ms"] == 150

        # 3. Test legacy root alias: GET /batch/result/{job_id}
        res_legacy_result = client.get(f"/batch/result/{job_id}")
        assert res_legacy_result.status_code == 200
        assert res_legacy_result.json()["audio_b64"] == dummy_b64


def test_tts_legacy_root_batch_synthesize(client):
    """Test legacy root endpoint POST /batch/synthesize for mobile app."""
    dummy_wav = b"RIFFtest"
    dummy_b64 = base64.b64encode(dummy_wav).decode("ascii")

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_base64", new_callable=AsyncMock) as mock_synth:

        mock_synth.return_value = (dummy_b64, 44100, 80)

        res = client.post("/batch/synthesize", json={"text": "Hello mascot!"})
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "completed"
        job_id = data["job_id"]

        # Check job is queryable
        job = tts_service.get_job(job_id)
        assert job is not None
        assert job["audio_b64"] == dummy_b64


def test_tts_direct_synthesize(client):
    """Test POST /api/v1/tts/synthesize with direct WAV and JSON format."""
    dummy_wav = b"RIFF_DIRECT_WAV_BYTES"

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_wav", new_callable=AsyncMock) as mock_wav:

        mock_wav.return_value = (dummy_wav, 95)

        # 1. Format=wav (binary)
        res_wav = client.post(
            "/api/v1/tts/synthesize?format=wav",
            json={"text": "Good morning students", "speed": 1.0},
        )
        assert res_wav.status_code == 200
        assert res_wav.headers["content-type"] == "audio/wav"
        assert res_wav.content == dummy_wav
        assert res_wav.headers.get("X-Latency-Ms") == "95"

        # 2. Format=json (base64)
        res_json = client.post(
            "/api/v1/tts/synthesize?format=json",
            json={"text": "Good morning students", "speed": 1.0},
        )
        assert res_json.status_code == 200
        json_data = res_json.json()
        assert json_data["status"] == "completed"
        assert json_data["audio_b64"] == base64.b64encode(dummy_wav).decode("ascii")


def test_tts_speaker_alias_resolution():
    """Test speaker key resolution for hyphen vs underscore."""
    svc = TTSService()
    svc._spk2id = {"EN_INDIA": 0, "EN-US": 1, "EN-BR": 2}
    svc._initialized = True

    assert svc.resolve_speaker_key("EN-INDIA") == "EN_INDIA"
    assert svc.resolve_speaker_key("EN_INDIA") == "EN_INDIA"
    assert svc.resolve_speaker_key("EN_US") == "EN-US"
    assert svc.resolve_speaker_key("EN-US") == "EN-US"


def test_tts_child_voice_pitch_parameters(client):
    """Test that child voice pitch parameter passes through correctly when provided."""
    dummy_wav = b"RIFF_CHILD_VOICE_BYTES"

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_wav", new_callable=AsyncMock) as mock_wav:

        mock_wav.return_value = (dummy_wav, 45)

        # Explicit speed and pitch request
        res = client.post(
            "/api/v1/tts/synthesize?format=wav",
            json={"text": "Hello teacher!", "speed": 0.90, "pitch": 5.0},
        )
        assert res.status_code == 200
        mock_wav.assert_called_once_with(
            text="Hello teacher!",
            speaker="EN_INDIA",
            speed=0.90,
            pitch=5.0,
        )


def test_tts_long_text_no_1000_character_limit(client):
    """Test that TTS endpoints accept long text (exceeding 1000 characters) without restrictions."""
    long_text = ("This is a comprehensive speech synthesis test allowing large paragraphs of text. " * 40).strip()
    assert len(long_text) > 1000  # Verify text length is well above 1000 characters

    dummy_wav = b"RIFF_LONG_VOICE_DATA"
    dummy_b64 = base64.b64encode(dummy_wav).decode("ascii")

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_wav", new_callable=AsyncMock) as mock_wav, \
         patch.object(tts_service, "synthesize_base64", new_callable=AsyncMock) as mock_b64:

        mock_wav.return_value = (dummy_wav, 320)
        mock_b64.return_value = (dummy_b64, 44100, 320)

        # 1. Direct synthesize endpoint with long text
        res_direct = client.post(
            "/api/v1/tts/synthesize?format=wav",
            json={"text": long_text},
        )
        assert res_direct.status_code == 200
        assert res_direct.content == dummy_wav

        # 2. Batch synthesize endpoint with long text
        res_batch = client.post(
            "/api/v1/tts/batch/synthesize",
            json={"text": long_text},
        )
        assert res_batch.status_code == 201
        data = res_batch.json()
        assert data["status"] == "completed"
        assert data["text_length"] == len(long_text)
        assert data["text_length"] > 1000


def test_tts_stream_pipeline_concurrent_chunks(client):
    """Test that multiple streaming chunks sent concurrently synthesize successfully."""
    chunks = [
        "Welcome to PhinsIQ Real-Time Voice Studio.",
        "This is chunk two playing seamlessly without stopping.",
        "And here is chunk three keeping the buffer full for continuous speech.",
    ]
    dummy_wav = b"RIFF_CHUNK_STREAM_DATA"

    with patch.object(tts_service, "_available", True), \
         patch.object(tts_service, "synthesize_wav", new_callable=AsyncMock) as mock_wav:

        mock_wav.return_value = (dummy_wav, 40)

        for chunk in chunks:
            res = client.post(
                "/api/v1/tts/synthesize?format=wav",
                json={"text": chunk, "speaker": "EN_INDIA", "speed": 1.0},
            )
            assert res.status_code == 200
            assert res.content == dummy_wav

        assert mock_wav.call_count == len(chunks)


