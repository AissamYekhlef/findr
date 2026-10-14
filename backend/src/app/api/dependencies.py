"""API layer dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session as a dependency.

    Yields:
        AsyncSession: Database session for use in route handlers.
    """
    async with get_session() as session:
        yield session
