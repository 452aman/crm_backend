from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./crm.db"   # postgresql+psycopg://... in production
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 60
    refresh_token_days: int = 7
    groq_api_key: str | None = None
    llm_model: str = "openai/gpt-oss-120b"
    llm_timeout_s: int = 45
    cors_origins: list[str] = ["http://localhost:5173"]
    agent_max_steps: int = 6
    at_risk_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
