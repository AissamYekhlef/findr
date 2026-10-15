"""Application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Findr"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./findr.db",
        description="Database connection URL with async driver (supports SQLite and PostgreSQL)",
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

    # Source Management
    allowed_source_roots: list[str] = Field(
        default=[],
        description="Allowed root directories for source file registration (semicolon-separated on Windows, colon-separated on Unix)",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @field_validator("allowed_source_roots", mode="before")
    @classmethod
    def parse_allowed_roots(cls, v: str | list[str]) -> list[str]:
        """Parse allowed roots from environment variable or list."""
        if isinstance(v, list):
            return v
        if not v:
            return []
        # Split by semicolon on Windows, colon on Unix
        separator = ";" if os.name == "nt" else ":"
        roots = [root.strip() for root in v.split(separator) if root.strip()]
        return roots

    def __init__(self, **data: object) -> None:
        """Validate configuration on init."""
        super().__init__(**data)

        # Validate allowed source roots exist
        if self.allowed_source_roots:
            for root in self.allowed_source_roots:
                root_path = Path(root)
                if not root_path.exists():
                    raise ValueError(
                        f"ALLOWED_SOURCE_ROOTS directory does not exist: {root}"
                    )
                if not root_path.is_dir():
                    raise ValueError(
                        f"ALLOWED_SOURCE_ROOTS must be a directory: {root}"
                    )

        # Validate production config
        if self.environment == "production":
            if self.secret_key == "your-secret-key-change-in-production-min-32-chars":
                raise ValueError(
                    "SECRET_KEY must be set to a strong value in production"
                )
            if self.debug:
                raise ValueError("DEBUG must be False in production")


settings = Settings()
