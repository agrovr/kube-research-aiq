from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from KRAI_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="KRAI_", env_file=".env", extra="ignore", populate_by_name=True
    )

    app_name: str = "KubeResearch AIQ"
    environment: str = "development"

    # Models. "mock" writes reports offline from retrieved sources; "nvidia" calls an
    # OpenAI-compatible endpoint (NVIDIA hosted NIM by default, or any vLLM/NIM base URL).
    provider: str = Field(default="mock", description="mock or nvidia")
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_api_key: str | None = None
    shallow_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    deep_model: str = "openai/gpt-oss-120b"
    classifier_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    request_timeout_seconds: float = 45.0

    # Retrieval. The bundled library is always searched; Tavily is added when a key is set.
    tavily_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("KRAI_TAVILY_API_KEY", "TAVILY_API_KEY")
    )
    sources_per_question: int = Field(default=4, ge=1, le=10)
    max_report_sections: int = Field(default=5, ge=2, le=8)

    # Storage and queue.
    redis_url: str | None = None
    database_url: str | None = None
    storage_path: Path = Path("/data/jobs.json")
    queue_name: str = "krai:research-jobs"
    enable_background_local_runs: bool = True

    # Worker reliability.
    stale_after_seconds: int = Field(default=300, ge=30)
    max_attempts: int = Field(default=3, ge=1, le=10)
    worker_metrics_port: int = 0  # 0 disables the worker's /metrics server

    # Offline mode pacing, so local demos show each stage. Keep 0 in tests.
    mock_latency_seconds: float = Field(default=0.0, ge=0.0, le=10.0)

    cors_origins: str = "*"

    @field_validator("nvidia_api_key", "redis_url", "database_url", "tavily_api_key", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def uses_model(self) -> bool:
        return self.provider != "mock" and self.nvidia_api_key is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
