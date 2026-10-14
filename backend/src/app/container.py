"""Dependency injection container and wiring."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import async_session_maker
from src.app.modules.sources.connectors.csv import CsvConnector
from src.app.modules.sources.connectors.registry import SourceConnectorRegistry
from src.app.modules.sources.connectors.xlsx import XlsxConnector
from src.app.modules.sources.repository import SourceRepository
from src.app.modules.sources.service import Clock, IdGenerator, SourceService


# Initialize singleton connector registry and register connectors
connector_registry = SourceConnectorRegistry()
connector_registry.register("csv", CsvConnector())
connector_registry.register("xlsx", XlsxConnector())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_source_repository(
    session: AsyncSession = async_session_maker(),  # type: ignore
) -> SourceRepository:
    """Provide SourceRepository instance."""
    # Note: In FastAPI dependency injection, session is injected via get_db_session
    pass


def get_configured_source_service(session: AsyncSession) -> SourceService:
    """Factory to create SourceService with wired dependencies."""
    repository = SourceRepository(session)
    return SourceService(
        repository=repository,
        registry=connector_registry,
        clock=Clock(),
        id_generator=IdGenerator(),
    )


def get_connector_registry() -> SourceConnectorRegistry:
    """Provide singleton connector registry."""
    return connector_registry
