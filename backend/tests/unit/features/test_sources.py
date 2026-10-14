"""Comprehensive unit tests for source service and connectors."""

from pathlib import Path
from uuid import UUID

import pytest

from src.app.core.exceptions import ConflictError, NotFoundError, ValidationError as DomainValidationError
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
        _ = cursor
        items = list(self.sources.values())
        return items[:limit], None

    async def update(self, id: UUID, **kwargs) -> Source | None:
        source = self.sources.get(id)
        if not source:
            return None
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


@pytest.fixture(autouse=True)
def setup_fixture_env(monkeypatch):
    """Configure ALLOWED_SOURCE_ROOTS to include tests/fixtures automatically."""
    fixture_dir = str(Path("tests/fixtures").resolve())
    from src.app.core.config import settings
    monkeypatch.setattr(settings, "allowed_source_roots", [fixture_dir])


@pytest.mark.asyncio
async def test_csv_config_identity():
    """Test CsvConfig identity normalization."""
    csv_path = str(Path("tests/fixtures/sample_brand_new.csv").resolve())
    config = CsvConfig(kind="csv", path=csv_path)
    identity = config.identity()
    assert identity.startswith("csv:")


def test_registry():
    """Test connector registry operations."""
    registry = SourceConnectorRegistry()
    connector = CsvConnector()
    registry.register("csv", connector)
    assert registry.get("csv") == connector
    assert "csv" in registry.list_kinds()

    # Test duplicate registration error
    with pytest.raises(ValueError, match="already registered"):
        registry.register("csv", connector)

    # Test unknown kind error
    with pytest.raises(ValueError, match="Unknown source kind"):
        registry.get("unknown")


@pytest.mark.asyncio
async def test_csv_connector_validation_and_schema():
    """Test CsvConnector validation, schema inference, and fingerprinting."""
    csv_path = str(Path("tests/fixtures/sample_brand_new.csv").resolve())
    config = CsvConfig(kind="csv", path=csv_path)
    connector = CsvConnector()

    # Validate
    await connector.validate(config)

    # Get schema
    schema = await connector.get_schema(config)
    assert len(schema.entities) == 1
    assert schema.entities[0].name == "sample_brand_new"
    assert len(schema.entities[0].fields) > 0

    # Fingerprint
    fp = await connector.fingerprint(config)
    assert isinstance(fp, str)
    assert len(fp) == 64


@pytest.mark.asyncio
async def test_source_service_create_and_duplicate():
    """Test SourceService creation and duplicate identity check."""
    repo = FakeRepository()
    registry = SourceConnectorRegistry()
    registry.register("csv", CsvConnector())
    service = SourceService(
        repository=repo,
        registry=registry,
        clock=FixedClock(),
        id_generator=FixedIdGenerator(),
    )

    csv_path = str(Path("tests/fixtures/sample_brand_new.csv").resolve())
    config_dict = {"path": csv_path, "delimiter": ","}

    # Create source
    source = await service.create_source(name="My CSV Source", kind="csv", config_dict=config_dict)
    assert source.id == UUID("12345678-1234-5678-1234-567812345678")
    assert source.name == "My CSV Source"
    assert source.kind == "csv"

    # Attempt to create duplicate source (same file path)
    with pytest.raises(ConflictError, match="already exists"):
        await service.create_source(name="Duplicate Source", kind="csv", config_dict=config_dict)


@pytest.mark.asyncio
async def test_source_service_not_found():
    """Test SourceService not found errors."""
    repo = FakeRepository()
    registry = SourceConnectorRegistry()
    service = SourceService(repository=repo, registry=registry)

    unknown_id = UUID("87654321-4321-8765-4321-876543218765")

    with pytest.raises(NotFoundError):
        await service.get_source(unknown_id)

    with pytest.raises(NotFoundError):
        await service.update_source(unknown_id, name="New Name")

    with pytest.raises(NotFoundError):
        await service.delete_source(unknown_id)

    with pytest.raises(NotFoundError):
        await service.get_schema(unknown_id)


@pytest.mark.asyncio
async def test_source_service_unknown_kind():
    """Test SourceService with unknown source kind."""
    repo = FakeRepository()
    registry = SourceConnectorRegistry()
    service = SourceService(repository=repo, registry=registry)

    with pytest.raises(DomainValidationError, match="Unknown source kind"):
        await service.create_source(name="Bad Kind", kind="unknown", config_dict={})
