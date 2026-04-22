from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="KRAI_", env_file=".env", extra="ignore")

    app_name: str = "KubeResearch AIQ"
    environment: str = "development"
    provider: str = Field(default="mock", description="mock or nvidia")
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str | None = None
    shallow_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    deep_model: str = "openai/gpt-oss-120b"
    classifier_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    redis_url: str | None = None
    database_url: str | None = None
    storage_path: Path = Path("/data/jobs.json")
    queue_name: str = "krai:research-jobs"
    request_timeout_seconds: float = 45.0
    max_report_sections: int = 5
    enable_background_local_runs: bool = True
    cors_origins: str = "*"

    @field_validator("nvidia_api_key", "redis_url", "database_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
