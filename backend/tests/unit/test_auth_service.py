"""Unit tests for AuthService."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app.core import Base
from src.app.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.app.modules.auth.models import UserModel
from src.app.modules.auth.service import AuthService


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Provide an async session for tests."""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.mark.anyio
async def test_register_user(async_session):
    """Test successful user registration."""
    service = AuthService(async_session)
    email = "test@example.com"
    password = "securepassword123"

    result = await service.register(email=email, password=password)
    assert result["email"] == email
    assert "id" in result
    assert "created_at" in result


@pytest.mark.anyio
async def test_register_duplicate_email(async_session):
    """Test registration with existing email raises ConflictError."""
    service = AuthService(async_session)
    email = "duplicate@example.com"
    password = "securepassword123"

    await service.register(email=email, password=password)

    with pytest.raises(ConflictError):
        await service.register(email=email, password=password)


@pytest.mark.anyio
async def test_authenticate_success(async_session):
    """Test successful authentication returns JWT token."""
    service = AuthService(async_session)
    email = "login@example.com"
    password = "securepassword123"

    await service.register(email=email, password=password)
    token = await service.authenticate(email=email, password=password)

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.anyio
async def test_authenticate_invalid_credentials(async_session):
    """Test authentication with invalid password or email raises NotFoundError."""
    service = AuthService(async_session)
    email = "user@example.com"
    password = "securepassword123"

    await service.register(email=email, password=password)

    # Wrong password
    with pytest.raises(NotFoundError):
        await service.authenticate(email=email, password="wrongpassword")

    # Non-existent email
    with pytest.raises(NotFoundError):
        await service.authenticate(email="nonexistent@example.com", password=password)


@pytest.mark.anyio
async def test_get_user_by_token_success(async_session):
    """Test retrieving user details via valid JWT token."""
    service = AuthService(async_session)
    email = "token@example.com"
    password = "securepassword123"

    await service.register(email=email, password=password)
    token = await service.authenticate(email=email, password=password)

    user_info = await service.get_user_by_token(token)
    assert user_info["email"] == email
    assert "id" in user_info
    assert "user" in user_info


@pytest.mark.anyio
async def test_get_user_by_token_invalid(async_session):
    """Test retrieving user with invalid token raises NotFoundError."""
    service = AuthService(async_session)

    with pytest.raises(NotFoundError):
        await service.get_user_by_token("invalid.jwt.token")
