import logging
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEV_SECRET = "dev-only-change-this-secret-krishiassist-2026"
SQLITE_PREFIX = "sqlite:///"


class Settings(BaseSettings):
    # "development" (default) or "production". Production refuses to start with a weak secret.
    app_env: str = "development"
    database_url: str = "sqlite:///./krishiassist.db"
    jwt_secret: str = DEFAULT_DEV_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    # Websites allowed to call this API from a browser, separated by commas.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    # Sign-in protection (see services/rate_limit.py).
    login_max_failures: int = 5
    login_max_failures_per_ip: int = 20
    login_window_minutes: int = 15
    register_max_per_hour: int = 10
    need_max_per_hour: int = 30
    # Document uploads (see services/document_storage.py)
    upload_dir: str = "storage/uploads"
    max_upload_mb: int = 5
    max_documents_per_user: int = 25
    max_storage_mb_per_user: int = 50
    upload_max_per_hour: int = 30
    openrouter_api_key: str = ""
    llm_model: str = ""
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def _sqlite_path_does_not_depend_on_the_folder(cls, url: str) -> str:
        """sqlite:///./krishiassist.db used to create a different database file depending on
        which folder the server was started from. A relative SQLite path now always means
        'inside the project folder'."""
        if url.startswith(SQLITE_PREFIX):
            path = url[len(SQLITE_PREFIX):]
            if path and not path.startswith(":memory:") and not Path(path).is_absolute():
                return f"{SQLITE_PREFIX}{(PROJECT_ROOT / path).resolve().as_posix()}"
        return url

    @model_validator(mode="after")
    def _production_needs_a_real_secret(self):
        if self.app_env.strip().lower() == "production" and (self.jwt_secret == DEFAULT_DEV_SECRET or len(self.jwt_secret) < 32):
            raise ValueError("APP_ENV=production needs JWT_SECRET set to a random value of at least 32 characters.")
        return self

    @property
    def upload_path(self) -> Path:
        """Where uploaded files are stored. A relative folder means 'inside the project folder'."""
        p = Path(self.upload_dir)
        return (p if p.is_absolute() else PROJECT_ROOT / p).resolve()

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

if settings.jwt_secret == DEFAULT_DEV_SECRET:
    logging.getLogger("uvicorn.error").warning(
        "JWT_SECRET is not set, so the built-in development secret is in use. "
        "Set JWT_SECRET in the .env file before sharing or deploying this app."
    )
