from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Any


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://padel:padel123@localhost:5432/padel_scouter"
    redis_url: str = "redis://localhost:6379"

    secret_key: SecretStr = SecretStr("cambia_esto_en_produccion_minimo_32_chars_xxx")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    google_api_key: SecretStr = SecretStr("")

    app_env: str = "development"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()