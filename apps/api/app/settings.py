from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Boa Biblioteca API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/boabiblioteca",
        validation_alias="DATABASE_URL",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

    # JWT Configuration
    jwt_secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
