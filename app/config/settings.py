

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.constants import DEFAULT_USER_AGENT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    request_timeout: float = 30.0
    max_retry: int = 3
    retry_backoff_base: float = 0.5
    follow_redirect: bool = True
    http2: bool = True
    verify_ssl: bool = True
    user_agent: str = DEFAULT_USER_AGENT

    max_connections: int = 100
    max_keepalive_connections: int = 20

    log_level: str = "INFO"

    tempo_session_cookie: str | None = None



@lru_cache
def get_settings() -> Settings:
    return Settings()
