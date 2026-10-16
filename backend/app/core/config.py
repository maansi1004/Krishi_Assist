from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    database_url: str = "sqlite:///./krishiassist.db"
    jwt_secret: str = "dev-only-change-this-secret-krishiassist-2026"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    openrouter_api_key: str = ""
    llm_model: str = ""
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

settings = Settings()
