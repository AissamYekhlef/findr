"""Source configuration models with discriminated union."""

import os
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from src.app.core.config import settings  # noqa: F401


class CsvConfig(BaseModel):
    """Configuration for CSV sources."""

    kind: Literal["csv"]
    path: str
    delimiter: str = ","
    encoding: str = "utf-8"
    header_row: int = 0

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path is absolute and exists."""
        if not v:
            raise ValueError("path is required")

        # Convert to absolute path
        path_obj = Path(v)

        # Reject relative paths
        if not path_obj.is_absolute():
            raise ValueError(
                f"path must be absolute (not relative): {v}. "
                f"Use absolute paths like 'C:\\Data\\file.csv' or '/data/file.csv'"
            )

        # Normalize and resolve
        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"path cannot be resolved: {v} ({e})")

        # Check path exists
        if not resolved_path.exists():
            raise ValueError(f"path does not exist: {resolved_path}")

        # Check path is within allowed roots
        cls._check_allowed_roots(resolved_path)

        return str(resolved_path)

    @field_validator("header_row")
    @classmethod
    def validate_header_row(cls, v: int) -> int:
        """Validate header_row is non-negative."""
        if v < 0:
            raise ValueError("header_row must be >= 0")
        return v

    @staticmethod
    def _check_allowed_roots(path: Path) -> None:
        """Check that path is within allowed roots."""
        if not settings.allowed_source_roots:
            raise ValueError(
                "ALLOWED_SOURCE_ROOTS not configured. "
                "Set ALLOWED_SOURCE_ROOTS environment variable to register sources."
            )

        allowed = False

        for root in settings.allowed_source_roots:
            # Check if path is under root or is root
            try:
                path.resolve().relative_to(Path(root).resolve())
                allowed = True
                break
            except ValueError:
                pass

        if not allowed:
            roots_str = ", ".join(settings.allowed_source_roots)
            raise ValueError(
                f"path is outside allowed roots: {path}. "
                f"Allowed roots: {roots_str}"
            )

    def identity(self) -> str:
        """Return normalized identity for duplicate detection."""
        # Normalize path: Windows-safe, lowercase
        normalized = os.path.normcase(str(Path(self.path).resolve()))
        return f"csv:{normalized}"


class XlsxConfig(BaseModel):
    """Configuration for XLSX sources."""

    kind: Literal["xlsx"]
    path: str
    sheet: str | None = None
    header_row: int = 0

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate path is absolute and exists."""
        if not v:
            raise ValueError("path is required")

        # Convert to absolute path
        path_obj = Path(v)

        # Reject relative paths
        if not path_obj.is_absolute():
            raise ValueError(
                f"path must be absolute (not relative): {v}. "
                f"Use absolute paths like 'C:\\Data\\file.xlsx' or '/data/file.xlsx'"
            )

        # Normalize and resolve
        try:
            resolved_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"path cannot be resolved: {v} ({e})")

        # Check path exists
        if not resolved_path.exists():
            raise ValueError(f"path does not exist: {resolved_path}")

        # Check path is within allowed roots
        CsvConfig._check_allowed_roots(resolved_path)

        return str(resolved_path)

    @field_validator("header_row")
    @classmethod
    def validate_header_row(cls, v: int) -> int:
        """Validate header_row is non-negative."""
        if v < 0:
            raise ValueError("header_row must be >= 0")
        return v

    def identity(self) -> str:
        """Return normalized identity for duplicate detection."""
        # Normalize path: Windows-safe, lowercase
        normalized = os.path.normcase(str(Path(self.path).resolve()))
        sheet_part = f":{self.sheet}" if self.sheet else ""
        return f"xlsx:{normalized}{sheet_part}"


# Discriminated union: route by 'kind' field
SourceConfig = Annotated[CsvConfig | XlsxConfig, Field(discriminator="kind")]
