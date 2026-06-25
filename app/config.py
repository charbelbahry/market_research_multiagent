from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI product research analyzer"
    model_name: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    open_router_api_key: str | None = None
    serpapi_api_key: str | None = None
    tavily_api_key: str | None = None
    use_real_crew: bool = False
    request_time_out_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", frozen=True
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
