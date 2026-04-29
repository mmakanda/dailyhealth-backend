from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — set by Railway PostgreSQL plugin automatically
    database_url: str = "sqlite:///./pharmacy.db"

    # JWT — generate with: openssl rand -hex 32
    secret_key: str = "change-me-in-production"

    # Groq AI — get free key at https://console.groq.com
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"

    # CORS — set to your Vercel frontend URL in production
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
