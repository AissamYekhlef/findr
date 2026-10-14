"""Unit tests for source service and connectors."""

import pytest
from pathlib import Path
from uuid import UUID

from src.app.modules.sources.configs import CsvConfig
from src.app.modules.sources.connectors.csv import CsvConnector
from src.app.modules.sources.connectors.registry import SourceConnectorRegistry
from src.app.modules.sources.domain import Source
from src.app.modules.sources.service import Clock, IdGenerator, SourceService


class FakeRepository:
    """Fake repository for unit testing."""

    def __init__(self) -> None:
        self.sources: dict[UUID, Source] = {}
        self.by_identity: dict[str, Source] = {}

    async def create(self, source: Source) -> Source:
        self.sources[source.id] = source
        self.by_identity[source.identity_hash] = source
        return source

    async def get(self, id: UUID) -> Source | None:
        return self.sources.get(id)

    async def get_by_identity_hash(self, identity_hash: str) -> Source | None:
        return self.by_identity.get(identity_hash)

    async def list(self, limit: int = 50, cursor: str | None = None) -> tuple[list[Source], str | None]:
        items = list(self.sources.values())
        return items[:limit], None

    async def update(self, id: UUID, **kwargs) -> Source | None:
        source = self.sources.get(id)
        if not source:
            return None
        # Simple update simulation
        updated = Source(
            id=source.id,
            name=kwargs.get("name", source.name),
            kind=source.kind,
            config=kwargs.get("config", source.config),
            config_version=source.config_version,
            identity_hash=kwargs.get("identity_hash", source.identity_hash),
            fingerprint=kwargs.get("fingerprint", source.fingerprint),
            secret_ref=source.secret_ref,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_opened_at=kwargs.get("last_opened_at", source.last_opened_at),
        )
        self.sources[id] = updated
        self.by_identity[updated.identity_hash] = updated
        return updated

    async def delete(self, id: UUID) -> bool:
        source = self.sources.pop(id, None)
        if source:
            self.by_identity.pop(source.identity_hash, None)
            return True
        return False


class FixedClock(Clock):
    """Fixed clock for testing."""
    def now(self):
        from datetime import datetime, timezone
        return datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)


class FixedIdGenerator(IdGenerator):
    """Fixed ID generator for testing."""
    def generate(self) -> UUID:
        return UUID("12345678-1234-5678-1234-567812345678")


@pytest.mark.asyncio
async def test_csv_config_identity():
    """Test CsvConfig identity normalization."""
    config = CsvConfig(kind="csv", path=str(Path("tests/fixtures/sample.csv").resolve()))
    identity = config.identity()
    assert identity.startswith("csv:")


def test_registry():
    """Test connector registry operations."""
    registry = SourceConnectorRegistry()
    connector = CsvConnector()
    registry.register("csv", connector)
    assert registry.get("csv") == connector
    assert "csv" in registry.list_kinds()
