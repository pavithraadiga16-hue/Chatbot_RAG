"""
API v1 Router
===============

PURPOSE:
    Aggregates all v1 routes into a single router object that main.py mounts.
    This is the "index" of all API v1 endpoints.

WHY A ROUTER FILE?
    FastAPI's router system allows you to define routes in separate files
    and then combine them. main.py stays clean — it only mounts this router.

HOW VERSIONING WORKS:
    main.py mounts this router with prefix="/api/v1"
    This router includes:
        /health  (from health.py)
        /phinsiq/chat (from chat.py)

    Final routes:
        GET  /api/v1/health
        POST /api/v1/phinsiq/chat

    When we build v2, we create app/api/v2/router.py and mount it with
    prefix="/api/v2". Both versions run simultaneously — no downtime for
    clients on v1.
"""

from fastapi import APIRouter
from app.api.v1 import health, chat, admin, subject_engine, website, tts, voicelab

# Create the main v1 router
router = APIRouter()

# Include health routes — no prefix, so /health becomes /api/v1/health
router.include_router(health.router)

# Include chat routes — prefix /phinsiq, so /chat becomes /api/v1/phinsiq/chat
router.include_router(chat.router, prefix="/phinsiq")

# Include admin routes — prefix /admin, so /institutions becomes /api/v1/admin/institutions
router.include_router(admin.router, prefix="/admin")

# Include subject engine routes — routes are at /api/v1/subject-engine/...
router.include_router(subject_engine.router)

# Include website engine routes — routes are at /api/v1/admin/website/...
router.include_router(website.router)

# Include text-to-speech (TTS) routes — routes are at /api/v1/tts/...
router.include_router(tts.router, prefix="/tts")

# Include VoiceLab routes — exact concept from vexyl-tts-poc/voicelab/server.py
# Routes are at /api/v1/voicelab/...
router.include_router(voicelab.router, prefix="/voicelab")
