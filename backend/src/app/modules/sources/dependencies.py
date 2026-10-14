"""Dependency injection wiring for FastAPI router."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.container import connector_registry, get_db_session
from src.app.modules.sources.connectors.registry import SourceConnectorRegistry
from src.app.modules.sources.repository import SourceRepository
from src.app.modules.sources.service import Clock, IdGenerator, SourceService


async def get_source_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SourceService:
    """Provide fully wired SourceService instance with database session."""
    repository = SourceRepository(session)
    return SourceService(
        repository=repository,
        registry=connector_registry,
        clock=Clock(),
        id_generator=IdGenerator(),
    )


async def get_connector_registry() -> SourceConnectorRegistry:
    """Provide singleton connector registry instance."""
    return connector_registry
