import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Boa Biblioteca API"
    app_version: str = "1.0.0"
    app_description: str = (
        "API da Boa Biblioteca com autenticacao JWT, CRUD de livros, "
        "pessoas e usuarios."
    )
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        raw = value.strip()
        if not raw:
            return []

        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [item.strip() for item in raw.split(",") if item.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if (
            self.environment.lower() == "production"
            and self.jwt_secret_key == "dev-secret-key-change-in-production"
        ):
            raise ValueError(
                "JWT_SECRET_KEY deve ser configurada com valor seguro em production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
