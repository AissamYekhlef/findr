"""Base connector class with shared validation logic."""

import hashlib
import os
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from src.app.modules.sources.protocols import Capability, SourceConnector


class BaseConnector(SourceConnector):
    """Base class for source connectors with shared logic."""

    kind: ClassVar[str]
    capabilities: ClassVar[Capability]
    config_model: ClassVar[type[BaseModel]]

    @staticmethod
    def _validate_path_exists(path: str) -> Path:
        """Validate that a file path exists and is readable.

        Args:
            path: Absolute file path.

        Returns:
            Path: Resolved Path object.

        Raises:
            ValueError: If path doesn't exist or is not readable.
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise ValueError(f"File not found: {path}")

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        if not os.access(path_obj, os.R_OK):
            raise ValueError(f"File is not readable: {path}")

        return path_obj

    @staticmethod
    def _compute_sha256(file_path: str, chunk_size: int = 65536) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to file.
            chunk_size: Size of chunks to read (default 64KB).

        Returns:
            str: SHA-256 hex digest.

        Raises:
            ValueError: If file cannot be read.
        """
        sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    sha256.update(data)
        except OSError as e:
            raise ValueError(f"Cannot compute hash for file: {file_path} ({e})")

        return sha256.hexdigest()

    @staticmethod
    def _compute_fast_fingerprint(file_path: str) -> str:
        """Compute a fast fingerprint using file metadata.

        For large files, uses modification time and size instead of hashing contents.

        Args:
            file_path: Path to file.

        Returns:
            str: SHA-256 hex digest of (mtime, size).

        Raises:
            ValueError: If file metadata cannot be read.
        """
        try:
            stat = Path(file_path).stat()
            combined = f"{stat.st_mtime}:{stat.st_size}"
            return hashlib.sha256(combined.encode()).hexdigest()
        except OSError as e:
            raise ValueError(f"Cannot compute fingerprint for file: {file_path} ({e})")

