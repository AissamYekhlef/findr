"""Database configuration and session management."""

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.app.core.config import settings

# Naming conventions for database constraints and indexes
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    metadata = MetaData(naming_convention=naming_convention)


# Create async engine with support for both SQLite and PostgreSQL
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

engine_kwargs = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
    "connect_args": connect_args,
}
if "sqlite" not in settings.database_url:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    """Dependency to get a transactional database session for a request.

    Commits the transaction on success and rolls back on any exception, so
    changes made by a request are actually persisted rather than silently
    discarded when the session is closed.

    Yields:
        AsyncSession: Database session that is automatically closed after use.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database on app startup.

    Creates tables if they don't exist (for development).
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Running in offline mode. Database features will not be available.")


async def close_db() -> None:
    """Close database connections on app shutdown."""
    await engine.dispose()
