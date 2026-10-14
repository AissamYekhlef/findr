"""SQLAlchemy ORM model for sources."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.core.database import Base


class SourceModel(Base):
    """Source ORM model for persistence."""

    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON in DB
    config_version: Mapped[int] = mapped_column(default=1, nullable=False)
    identity_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
