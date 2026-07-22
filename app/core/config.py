"""
Configuración central de la aplicación Padel Scouter.

Gestiona todas las variables de entorno y secretos usando Pydantic Settings.
Los valores por defecto son para desarrollo local; en producción deben
sobrescribirse mediante el archivo .env o variables de entorno del sistema.

Seguridad:
- SecretStr para secret_key, google_api_key y resend_api_key:
  evita que se filtren en logs o trazas.
- El secret_key por defecto es inseguro — en producción debe ser una
  cadena aleatoria de al menos 32 caracteres.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    """Configuración tipada de la aplicación cargada desde .env y entorno."""

    # ── Base de datos y caché ──────────────────────────────────
    database_url: str = "postgresql+psycopg2://padel:padel123@localhost:5432/padel_scouter"
    redis_url: str = "redis://localhost:6379"

    # ── Seguridad JWT ──────────────────────────────────────────
    secret_key: SecretStr = SecretStr("cambia_esto_en_produccion_minimo_32_chars_xxx")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Reset password token — corta duración (15 min) por OWASP A07
    reset_token_expire_minutes: int = 15

    # ── Google AI (Gemini) ─────────────────────────────────────
    google_api_key: SecretStr = SecretStr("")

    # ── Email (Resend) ─────────────────────────────────────────
    resend_api_key: SecretStr = SecretStr("")
    app_url: str = "http://localhost:8000"
    emails_from: str = "Padel Scouter <onboarding@resend.dev>"
    # En desarrollo, Resend solo permite enviar al email del dueño de la cuenta
    resend_owner_email: str = "rubenet1984@gmail.com"

    # ── Entorno ────────────────────────────────────────────────
    app_env: str = "development"
    # Orígenes permitidos para CORS (separados por coma)
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    def get_allowed_origins(self) -> list[str]:
        """Convierte la cadena de orígenes separados por coma en una lista limpia."""
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Instancia singleton de configuración para toda la aplicación
settings = Settings()