"""Application configuration using Pydantic Settings."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Findr"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://findr_user:dev_password@localhost:5432/findr",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL statements to console (debug only)",
    )

    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        description="Secret key for JWT signing (must be set in production)",
    )
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # Logging
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **data: object) -> None:
        """Validate configuration on init."""
        super().__init__(**data)

        # Validate production config
        if self.environment == "production":
            if self.secret_key == "your-secret-key-change-in-production-min-32-chars":
                raise ValueError(
                    "SECRET_KEY must be set to a strong value in production"
                )
            if self.debug:
                raise ValueError("DEBUG must be False in production")


settings = Settings()
