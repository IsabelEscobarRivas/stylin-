"""
config.py — Application settings loaded from environment variables.
Switched from DeployAI to Anthropic API for both agents.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Anthropic API ─────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")

    # Model used for both Vision Scout and Style Curator
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        env="ANTHROPIC_MODEL"
    )

    # ── Pexels API (server-side only — never exposed to clients) ──────────────
    pexels_key: str = Field(default="", env="PEXELS_KEY")

    # ── App Config ────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_image_size_mb: int = Field(default=10, env="MAX_IMAGE_SIZE_MB")

    # ── Token limits ──────────────────────────────────────────────────────────
    vision_max_tokens: int = Field(default=1024, env="VISION_MAX_TOKENS")
    curator_max_tokens: int = Field(default=4096, env="CURATOR_MAX_TOKENS")

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton — import this everywhere
settings = Settings()
