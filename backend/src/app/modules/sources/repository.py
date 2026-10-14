"""Repository protocol and SQLAlchemy implementation for sources."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.modules.sources.domain import Source
from src.app.modules.sources.models import SourceModel


class SourceRepositoryProtocol(ABC):
    """Repository protocol for source persistence."""

    @abstractmethod
    async def create(self, source: Source) -> Source:
        """Create a new source."""
        pass

    @abstractmethod
    async def get(self, id: UUID) -> Source | None:
        """Get a source by ID."""
        pass

    @abstractmethod
    async def get_by_identity_hash(self, identity_hash: str) -> Source | None:
        """Get a source by its identity hash."""
        pass

    @abstractmethod
    async def list(self, limit: int = 50, cursor: str | None = None) -> tuple[list[Source], str | None]:
        """List sources with cursor-based pagination."""
        pass

    @abstractmethod
    async def update(
        self,
        id: UUID,
        name: str | None = None,
        config: dict | None = None,
        identity_hash: str | None = None,
        fingerprint: str | None = None,
        last_opened_at: datetime | None = None,
    ) -> Source | None:
        """Update a source."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete a source by ID."""
        pass


class SourceRepository(SourceRepositoryProtocol):
    """SQLAlchemy implementation of SourceRepositoryProtocol."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session."""
        self.session = session

    def _to_domain(self, model: SourceModel) -> Source:
        """Convert ORM model to domain object."""
        return Source(
            id=model.id,
            name=model.name,
            kind=model.kind,
            config=model.config,
            config_version=model.config_version,
            identity_hash=model.identity_hash,
            fingerprint=model.fingerprint,
            secret_ref=model.secret_ref,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_opened_at=model.last_opened_at,
        )

    async def create(self, source: Source) -> Source:
        """Create a new source in database."""
        model = SourceModel(
            id=source.id,
            name=source.name,
            kind=source.kind,
            config=source.config,
            config_version=source.config_version,
            identity_hash=source.identity_hash,
            fingerprint=source.fingerprint,
            secret_ref=source.secret_ref,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_opened_at=source.last_opened_at,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get(self, id: UUID) -> Source | None:
        """Get source by ID."""
        stmt = select(SourceModel).where(SourceModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_identity_hash(self, identity_hash: str) -> Source | None:
        """Get source by identity hash."""
        stmt = select(SourceModel).where(SourceModel.identity_hash == identity_hash)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list(self, limit: int = 50, cursor: str | None = None) -> tuple[list[Source], str | None]:
        """List sources with cursor-based pagination."""
        stmt = select(SourceModel).order_by(SourceModel.created_at.desc(), SourceModel.id.desc())

        if cursor:
            try:
                # Cursor format: timestamp_str:uuid_str
                ts_str, uuid_str = cursor.split(":")
                cursor_dt = datetime.fromisoformat(ts_str)
                cursor_id = UUID(uuid_str)
                stmt = stmt.where(
                    (SourceModel.created_at < cursor_dt) |
                    ((SourceModel.created_at == cursor_dt) & (SourceModel.id < cursor_id))
                )
            except (ValueError, TypeError):
                pass

        stmt = stmt.limit(limit + 1)
        result = await self.session.execute(stmt)
        models = list(result.scalars().all())

        next_cursor = None
        if len(models) > limit:
            models = models[:limit]
            last_model = models[-1]
            next_cursor = f"{last_model.created_at.isoformat()}:{last_model.id}"

        sources = [self._to_domain(m) for m in models]
        return sources, next_cursor

    async def update(
        self,
        id: UUID,
        name: str | None = None,
        config: dict | None = None,
        identity_hash: str | None = None,
        fingerprint: str | None = None,
        last_opened_at: datetime | None = None,
    ) -> Source | None:
        """Update source attributes."""
        stmt = select(SourceModel).where(SourceModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        if name is not None:
            model.name = name
        if config is not None:
            model.config = config
        if identity_hash is not None:
            model.identity_hash = identity_hash
        if fingerprint is not None:
            model.fingerprint = fingerprint
        if last_opened_at is not None:
            model.last_opened_at = last_opened_at

        model.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, id: UUID) -> bool:
        """Delete source by ID."""
        stmt = select(SourceModel).where(SourceModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True
