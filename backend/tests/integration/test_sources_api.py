"""Integration and API tests for sources endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app.main import create_app


@pytest.fixture
def client(monkeypatch):
    """Provide a test client with allowed source roots configured and clean db state."""
    fixture_dir = str(Path("tests/fixtures").resolve())
    from src.app.core.config import settings
    monkeypatch.setattr(settings, "allowed_source_roots", [fixture_dir])
    monkeypatch.setattr(settings, "database_url", "sqlite+aiosqlite:///:memory:")

    # Re-init db/engine for in-memory
    from src.app.core.database import Base, engine
    import asyncio
    async def reset():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(reset())
    except RuntimeError:
        asyncio.run(reset())

    app = create_app()
    return TestClient(app)


def test_sources_api_workflow(client):
    """Test full sources API workflow: create, list, get, schema, delete."""
    csv_path = str(Path("tests/fixtures/sample_brand_new.csv").resolve())

    # 1. List kinds
    response = client.get("/api/v1/sources/kinds")
    assert response.status_code == 200
    kinds_data = response.json()
    assert isinstance(kinds_data, list)
    assert any(k["kind"] == "csv" for k in kinds_data)

    # 2. Create source
    create_payload = {
        "name": "Integration CSV Source",
        "kind": "csv",
        "config": {
            "path": csv_path,
            "delimiter": ",",
        },
    }
    response = client.post("/api/v1/sources", json=create_payload)
    assert response.status_code == 201
    source_data = response.json()
    assert source_data["name"] == "Integration CSV Source"
    assert source_data["kind"] == "csv"
    source_id = source_data["id"]

    # 3. Get source by ID
    response = client.get(f"/api/v1/sources/{source_id}")
    assert response.status_code == 200
    assert response.json()["id"] == source_id

    # 4. Get source schema
    response = client.get(f"/api/v1/sources/{source_id}/schema")
    assert response.status_code == 200
    schema_data = response.json()
    assert "entities" in schema_data
    assert len(schema_data["entities"]) == 1

    # 5. List sources
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    list_data = response.json()
    assert "items" in list_data
    assert len(list_data["items"]) >= 1

    # 6. Delete source
    response = client.delete(f"/api/v1/sources/{source_id}")
    assert response.status_code == 204

    # 7. Verify deletion
    response = client.get(f"/api/v1/sources/{source_id}")
    assert response.status_code == 404
