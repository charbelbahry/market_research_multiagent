from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI product research analyzer"
    cheap_model_name: str = "gpt-4o-mini"
    strong_model_name: str = "gpt-4o"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    open_router_api_key: str | None = None
    serper_api_key: str | None = None
    tavily_api_key: str | None = None
    use_real_crew: bool = False
    request_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", frozen=True, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
