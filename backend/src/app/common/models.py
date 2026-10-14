"""Common base models and utilities."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, func

from src.app.core import Base


class TimestampedModel(Base):
    """Base model with common fields: ID, created_at, updated_at."""

    __abstract__ = True

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False,
    )
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<{self.__class__.__name__} id={self.id}>"
