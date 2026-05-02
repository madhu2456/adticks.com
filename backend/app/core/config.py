"""
AdTicks — Application configuration.

All settings are loaded from environment variables (or a .env file)
using pydantic-settings so that no secrets are hard-coded.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field

# Determine the directory of this file
_current_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate to the backend root where .env is located
_backend_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
_env_file = os.path.join(_backend_root, ".env")

class Settings(BaseSettings):
    """Central settings object for the AdTicks backend."""

    model_config = SettingsConfigDict(
        env_file=_env_file if os.path.exists(_env_file) else ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/adticks",
        description="Database connection URL - override with env variable for production"
    )

    # ------------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------------
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL - override with env variable for production"
    )

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = "changeme-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ------------------------------------------------------------------
    # CORS Configuration
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [],
        description="CORS allowed origins - MUST be set from environment variable in production"
    )

    # ------------------------------------------------------------------
    # Storage Configuration
    # ------------------------------------------------------------------
    STORAGE_ROOT: str = "data"
    BASE_URL: str = Field(
        default="",
        description="Base URL for generating file URLs - MUST be set from environment variable in production"
    )

    # ------------------------------------------------------------------
    # AI providers
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Google OAuth / Search Console / Analytics
    # ------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = Field(
        default="",
        description="Google OAuth callback URL - MUST be set from environment variable in production"
    )

    # ------------------------------------------------------------------
    # Bing Webmaster Tools OAuth
    # ------------------------------------------------------------------
    BING_CLIENT_ID: str = ""
    BING_CLIENT_SECRET: str = ""
    BING_REDIRECT_URI: str = Field(
        default="",
        description="Bing OAuth callback URL - MUST be set from environment variable in production"
    )

    # ------------------------------------------------------------------
    # Monitoring & Error Tracking
    # ------------------------------------------------------------------
    SENTRY_DSN: str = ""

    # ------------------------------------------------------------------
    # SEO API Keys
    # ------------------------------------------------------------------
    PSI_API_KEY: str = Field(default="", description="PageSpeed Insights API Key")
    SERPAPI_KEY: str = Field(default="", description="SerpApi Key")

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------
    ENVIRONMENT: str = "development"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info):
        """Ensure SECRET_KEY is not the default in production."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and v == "changeme-super-secret-key":
            raise ValueError(
                "SECRET_KEY must not be the default value in production. "
                "Set a strong random key via environment variable."
            )
        if len(v) < 32 and environment == "production":
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in production. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: any) -> list[str]:
        """Parse ALLOWED_ORIGINS from string or list."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: list[str], info):
        """Validate CORS origins in production."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production":
            if not v or len(v) == 0:
                raise ValueError(
                    "ALLOWED_ORIGINS must be set from environment variable in production. "
                    "Example: ALLOWED_ORIGINS='[\"https://adticks.com\"]'"
                )
            # Check for localhost/development origins
            dev_origins = [o for o in v if "localhost" in o or "127.0.0.1" in o]
            if dev_origins:
                raise ValueError(
                    f"Development origins not allowed in production CORS: {dev_origins}"
                )
        return v

    @field_validator("BASE_URL")
    @classmethod
    def validate_base_url(cls, v: str, info):
        """Validate BASE_URL in production."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            raise ValueError(
                "BASE_URL must be set from environment variable in production. "
                "Example: BASE_URL='https://adticks.com'"
            )
        return v

    @field_validator("GOOGLE_REDIRECT_URI")
    @classmethod
    def validate_google_redirect(cls, v: str, info):
        """Validate Google redirect URI in production."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            raise ValueError(
                "GOOGLE_REDIRECT_URI must be set from environment variable in production. "
                "Example: GOOGLE_REDIRECT_URI='https://adticks.com/gsc-callback'"
            )
        return v

    @field_validator("BING_REDIRECT_URI")
    @classmethod
    def validate_bing_redirect(cls, v: str, info):
        """Validate Bing redirect URI in production."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and not v:
            raise ValueError(
                "BING_REDIRECT_URI must be set from environment variable in production. "
                "Example: BING_REDIRECT_URI='https://adticks.com/bing-callback'"
            )
        return v
        return v


# Singleton used throughout the application
settings = Settings()
