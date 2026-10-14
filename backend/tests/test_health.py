"""Tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.app.main import create_app


@pytest.fixture
def client():
    """Provide a test client."""
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    """Test liveness health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
