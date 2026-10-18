"""Integration and API tests for authentication."""

import pytest
from fastapi.testclient import TestClient

from src.app.main import create_app
from src.app.core import database


@pytest.fixture
def client(monkeypatch):
    """Provide a test client with fresh in-memory database."""
    monkeypatch.setattr("src.app.core.config.settings.database_url", "sqlite+aiosqlite:///:memory:")

    test_engine = database.create_async_engine(
        database.settings.database_url,
        echo=database.settings.database_echo,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False}
    )
    test_session_maker = database.async_sessionmaker(
        test_engine,
        class_=database.AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "async_session_maker", test_session_maker)

    import asyncio
    async def reset():
        async with test_engine.begin() as conn:
            await conn.run_sync(database.Base.metadata.create_all)
    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(reset())
    except RuntimeError:
        asyncio.run(reset())

    app = create_app()

    from src.app.core.database import get_session
    async def override_get_session():
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(test_engine.dispose())
    except RuntimeError:
        asyncio.run(test_engine.dispose())


def test_auth_workflow(client):
    """Test full registration, login, and profile workflow."""
    email = "test@example.com"
    password = "securepassword123"

    # 1. Register user
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    print("REG1 STATUS:", response.status_code, "BODY:", response.text)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data

    # 2. Duplicate registration conflict
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    print("REG2 STATUS:", response.status_code, "BODY:", response.text)
    assert response.status_code == 409

    # 3. Login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 4. Get current user profile (/me)
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == email

    # 5. Invalid token profile access
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 404
