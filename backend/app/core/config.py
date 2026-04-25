"""
AdTicks — Application configuration.

All settings are loaded from environment variables (or a .env file)
using pydantic-settings so that no secrets are hard-coded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field


class Settings(BaseSettings):
    """Central settings object for the AdTicks backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/adticks"

    # ------------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

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
        default_factory=lambda: ["https://adticks.com", "http://localhost:3002"],
        description="CORS allowed origins"
    )

    # ------------------------------------------------------------------
    # Storage Configuration
    # ------------------------------------------------------------------
    STORAGE_ROOT: str = "data"
    BASE_URL: str = Field(
        default="https://adticks.com",
        description="Base URL for generating file URLs"
    )

    # ------------------------------------------------------------------
    # AI providers
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Google OAuth / Search Console
    # ------------------------------------------------------------------
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = Field(
        default="https://adticks.com/api/gsc/callback",
        description="Google OAuth callback URL"
    )

    # ------------------------------------------------------------------
    # Monitoring & Error Tracking
    # ------------------------------------------------------------------
    SENTRY_DSN: str = ""

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
            # Check for localhost/development origins
            dev_origins = [o for o in v if "localhost" in o or "127.0.0.1" in o]
            if dev_origins:
                raise ValueError(
                    f"Development origins not allowed in production CORS: {dev_origins}"
                )
        return v


# Singleton used throughout the application
settings = Settings()
