"""
PhinsIQ Core Configuration
===========================

PURPOSE:
    Central configuration module. Reads all environment variables once at
    startup and exposes them as a typed, validated Settings object.

WHY CENTRALIZED CONFIGURATION?
    If every module reads os.environ directly, there are several problems:
    1. Typos in variable names cause silent failures
    2. No type validation (an env var is always a string — we want integers for PORT)
    3. No default values in one place
    4. No documentation of what variables exist

    By centralizing here, the entire application shares ONE validated config object.

HOW IT WORKS:
    pydantic-settings reads the .env file automatically when Settings() is instantiated.
    It validates types (e.g., APP_PORT must be an integer), applies defaults,
    and raises a clear error at startup if a required variable is missing.

USAGE:
    from app.core.config import settings

    print(settings.mongodb_url)
    print(settings.app_env)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.

    Pydantic automatically reads these from environment variables with matching
    names (case-insensitive). If a variable is not set and has no default,
    startup will fail with a clear error — this is intentional.

    WHY TYPE ANNOTATIONS MATTER:
        app_port: int  ← pydantic converts "8000" (string from env) to 8000 (int)
        This prevents bugs like concatenating a port number to a URL as a string.
    """

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------

    app_name: str = Field(default="PhinsIQ", description="Application display name")
    app_env: str = Field(default="development", description="Runtime environment")
    app_port: int = Field(default=8000, description="Port for the HTTP server")
    public_api_base_url: str = Field(
        default="",
        description=(
            "Public API base URL used by the browser console. Leave empty to "
            "auto-derive from APP_ENV (localhost in development, production domain "
            "in production) via effective_public_api_base_url."
        ),
    )

    # -------------------------------------------------------------------------
    # MongoDB
    # -------------------------------------------------------------------------

    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="Full MongoDB connection string. Never hardcode credentials here."
    )
    mongodb_database: str = Field(
        default="phinsiq",
        description="MongoDB database name for PhinsIQ configuration data"
    )
    mongodb_timeout: int = Field(
        default=5,
        description="Seconds before MongoDB query times out"
    )

    # -------------------------------------------------------------------------
    # Redis Caching
    # -------------------------------------------------------------------------

    redis_enabled: bool = Field(
        default=True,
        description="Enable Redis caching for fast repeated query responses",
        validation_alias=AliasChoices("redis_enabled", "REDIS_ENABLED"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (e.g. redis://localhost:6379/0)",
        validation_alias=AliasChoices("redis_url", "REDIS_URL"),
    )
    redis_ttl_general: int = Field(
        default=3600,
        description="Cache TTL in seconds for general/institutional RAG queries (1 hour)",
        validation_alias=AliasChoices("redis_ttl_general", "REDIS_TTL_GENERAL"),
    )
    redis_ttl_student: int = Field(
        default=300,
        description="Cache TTL in seconds for student-specific ERP queries (5 minutes)",
        validation_alias=AliasChoices("redis_ttl_student", "REDIS_TTL_STUDENT"),
    )

    # -------------------------------------------------------------------------
    # Institutional Document RAG
    # -------------------------------------------------------------------------

    rag_enabled: bool = Field(
        default=True,
        description="Route institutional and academic document questions through local document retrieval",
        validation_alias=AliasChoices("rag_enabled", "RAG_ENABLED"),
    )
    rag_top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum knowledge chunks returned for a RAG query",
        validation_alias=AliasChoices("rag_top_k", "RAG_TOP_K"),
    )
    rag_vector_db_path: str = Field(
        default="data/rag/index/rag.sqlite3",
        description="SQLite vector store path, relative to the project root",
        validation_alias=AliasChoices("rag_vector_db_path", "RAG_VECTOR_DB_PATH"),
    )

    # -------------------------------------------------------------------------
    # ERP API Client
    # -------------------------------------------------------------------------

    erp_timeout: int = Field(
        default=10,
        description="Seconds before ERP API call times out"
    )
    erp_retry_count: int = Field(
        default=2,
        description="Number of retry attempts for failed ERP API calls"
    )

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------

    jwt_secret_key: str = Field(
        default="change-this-in-production",
        description="Secret for signing JWT tokens. MUST be changed in production."
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60)
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins. Set in .env via CORS_ORIGINS.",
        validation_alias=AliasChoices("cors_origins", "allowed_origins", "CORS_ORIGINS", "ALLOWED_ORIGINS"),
    )

    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------

    rate_limit_per_minute: int = Field(
        default=30,
        description="Max chat requests per user per minute"
    )

    # -------------------------------------------------------------------------
    # Text-to-Speech (MeloTTS)
    # -------------------------------------------------------------------------

    tts_speaker: str = Field(
        default="EN_INDIA",
        description="Default MeloTTS speaker identifier (e.g. EN_INDIA, EN-US, EN-BR)",
        validation_alias=AliasChoices("tts_speaker", "melo_speaker", "vexyl_speaker"),
    )
    tts_speed: float = Field(
        default=1.0,
        description="Default speech playback speed (1.0 = standard rate)",
        validation_alias=AliasChoices("tts_speed", "melo_speed", "vexyl_speed"),
    )
    tts_pitch: float = Field(
        default=0.0,
        description="Pitch shift in semitones (0.0 = original adult voice)",
        validation_alias=AliasChoices("tts_pitch", "melo_pitch", "vexyl_pitch"),
    )
    tts_lang: str = Field(
        default="en-IN",
        description="Default language code (e.g. en-IN, en-US)",
        validation_alias=AliasChoices("tts_lang", "melo_lang", "vexyl_lang"),
    )
    tts_style: str = Field(
        default="default",
        description="Default voice style",
        validation_alias=AliasChoices("tts_style", "melo_style", "vexyl_style"),
    )
    tts_device: str = Field(
        default="cpu",
        description="Inference device: 'cpu', 'cuda', or 'mps'",
        validation_alias=AliasChoices("tts_device", "melo_device", "vexyl_device"),
    )
    tts_threads: int = Field(
        default=8,
        description="PyTorch CPU inference threads",
        validation_alias=AliasChoices("tts_threads", "melo_threads"),
    )
    tts_api_key: str = Field(
        default="",
        description="Optional API key for TTS endpoints. If empty, endpoints are open.",
        validation_alias=AliasChoices("tts_api_key", "melo_api_key"),
    )
    tts_cache_cap: int = Field(
        default=256,
        description="In-memory cache capacity for synthesized phrases",
    )
    tts_target_peak: float = Field(
        default=0.95,
        description="Audio peak normalization level for mobile phone speakers",
    )

    # -------------------------------------------------------------------------
    # Subject Engine (Mathematics & Science)
    # -------------------------------------------------------------------------

    enable_subject_engine: bool = Field(
        default=True,
        description="Toggle local Subject Engines (Mathematics, Science).",
        validation_alias=AliasChoices(
            "enable_subject_engine",
            "subject_engine_enabled",
            "ENABLE_SUBJECT_ENGINE",
            "SUBJECT_ENGINE_ENABLED",
        ),
    )
    enable_math_engine: bool = Field(
        default=True,
        description="Toggle local Mathematics engine.",
        validation_alias=AliasChoices(
            "enable_math_engine",
            "math_engine_enabled",
            "ENABLE_MATH_ENGINE",
            "MATH_ENGINE_ENABLED",
        ),
    )
    enable_science_engine: bool = Field(
        default=True,
        description="Toggle local Science engine (Physics, Chemistry, Biology).",
        validation_alias=AliasChoices(
            "enable_science_engine",
            "science_engine_enabled",
            "ENABLE_SCIENCE_ENGINE",
            "SCIENCE_ENGINE_ENABLED",
        ),
    )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="console", description="'console' or 'json'")

    # -------------------------------------------------------------------------
    # Computed Properties (derived from other settings)
    # -------------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        """
        Returns True when running in development mode.

        Used to toggle debug information in API responses and to enable
        mock ERP providers instead of real HTTP calls.
        """
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Returns True when running in production mode."""
        return self.app_env.lower() == "production"

    @property
    def effective_public_api_base_url(self) -> str:
        """
        Resolves the browser console's API base URL for the current environment.

        Set PUBLIC_API_BASE_URL in .env to force a specific value (e.g. staging).
        Otherwise this switches automatically with APP_ENV, so flipping one
        variable is enough to go from local dev to production.
        """
        if self.public_api_base_url:
            return self.public_api_base_url.rstrip("/")
        return f"http://localhost:{self.app_port}/api/v1"

    @property
    def claude_enabled(self) -> bool:
        """Cloud LLM fallback is permanently disabled in the 2-path architecture."""
        return False

    @property
    def llm_model(self) -> str:
        return ""

    @property
    def llm_api_url(self) -> str:
        return ""

    @property
    def direct_llm_fallback(self) -> bool:
        return False

    # -------------------------------------------------------------------------
    # Pydantic Configuration
    # -------------------------------------------------------------------------

    model_config = SettingsConfigDict(
        # Tell pydantic-settings to load variables from the .env file.
        # Variables set directly in the shell environment take priority over .env.
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra fields in .env without raising errors.
        # Useful when .env has project-wide variables beyond PhinsIQ's scope.
        extra="ignore",
        # Make the settings object immutable after creation.
        # This prevents accidental mutation during the application lifetime.
        frozen=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the application settings singleton.

    WHY lru_cache?
        The @lru_cache decorator caches the return value after the first call.
        Without it, every call to get_settings() would re-read and re-validate
        the .env file. With it, the file is read ONCE and the same object is
        returned on every subsequent call.

        maxsize=1 means only one result is cached — which is exactly what we want
        since there are no arguments to this function.

    USAGE:
        from app.core.config import get_settings
        settings = get_settings()

    WHY NOT A GLOBAL VARIABLE?
        A function with lru_cache is better than a module-level singleton because:
        1. It is testable — tests can clear the cache with get_settings.cache_clear()
        2. It is lazy — the .env file is not read until the first call
        3. It is explicit — consumers import get_settings, not a magic global
    """
    return Settings()


# Convenience singleton for direct import.
# Most modules use: from app.core.config import settings
settings = get_settings()
