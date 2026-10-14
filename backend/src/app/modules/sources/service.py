"""Service layer for sources."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import TypeAdapter, ValidationError

from src.app.core.exceptions import ConflictError, NotFoundError, ValidationError as AppValidationError
from src.app.modules.sources.configs import SourceConfig
from src.app.modules.sources.connectors.registry import SourceConnectorRegistry
from src.app.modules.sources.domain import Source
from src.app.modules.sources.protocols import SourceSchema
from src.app.modules.sources.repository import SourceRepositoryProtocol


class Clock:
    """Clock for generating UTC datetimes (injected for testability)."""

    def now(self) -> datetime:
        """Return current UTC datetime."""
        return datetime.now(timezone.utc)


class IdGenerator:
    """ID generator for UUID v7 (injected for testability)."""

    def generate(self) -> UUID:
        """Generate a new UUID."""
        return uuid4()


class SourceService:
    """Service for managing data sources."""

    def __init__(
        self,
        repository: SourceRepositoryProtocol,
        registry: SourceConnectorRegistry,
        clock: Clock | None = None,
        id_generator: IdGenerator | None = None,
    ) -> None:
        """Initialize service with dependencies."""
        self.repository = repository
        self.registry = registry
        self.clock = clock or Clock()
        self.id_generator = id_generator or IdGenerator()

    async def create_source(self, name: str, kind: str, config_dict: dict[str, Any]) -> Source:
        """Create a new data source."""
        # Validate kind exists in registry
        try:
            connector = self.registry.get(kind)
        except ValueError as e:
            raise AppValidationError(f"Unknown source kind: {kind}", details={"code": "UNKNOWN_KIND"})

        # Validate config using TypeAdapter for discriminated union
        try:
            # Ensure kind is set in config dict
            config_dict["kind"] = kind
            adapter = TypeAdapter(SourceConfig)
            config_obj = adapter.validate_python(config_dict)
        except ValidationError as e:
            raise AppValidationError(f"Invalid configuration: {e}", details=e.errors())

        # Validate source is accessible via connector
        try:
            await connector.validate(config_obj)
        except Exception as e:
            raise AppValidationError(f"Source validation failed: {e}")

        # Compute identity hash
        identity_hash = hashlib.sha256(config_obj.identity().encode()).hexdigest()

        # Check for duplicate identity hash
        existing = await self.repository.get_by_identity_hash(identity_hash)
        if existing:
            raise ConflictError(f"A source with identity '{config_obj.identity()}' already exists")

        now = self.clock.now()
        source = Source(
            id=self.id_generator.generate(),
            name=name.strip(),
            kind=kind,
            config=config_dict,
            config_version=1,
            identity_hash=identity_hash,
            fingerprint=None,
            secret_ref=None,
            created_at=now,
            updated_at=now,
            last_opened_at=None,
        )

        return await self.repository.create(source)

    async def get_source(self, id: UUID) -> Source:
        """Get source by ID."""
        source = await self.repository.get(id)
        if not source:
            raise NotFoundError(f"Source with id {id} not found")
        return source

    async def list_sources(self, limit: int = 50, cursor: str | None = None) -> tuple[list[Source], str | None]:
        """List sources with cursor pagination."""
        return await self.repository.list(limit=limit, cursor=cursor)

    async def update_source(
        self,
        id: UUID,
        name: str | None = None,
        config_dict: dict[str, Any] | None = None,
    ) -> Source:
        """Update source name or configuration."""
        source = await self.get_source(id)

        new_name = name.strip() if name is not None else source.name
        new_config_dict = source.config
        new_identity_hash = source.identity_hash

        if config_dict is not None:
            kind = source.kind
            connector = self.registry.get(kind)
            config_dict["kind"] = kind

            try:
                adapter = TypeAdapter(SourceConfig)
                config_obj = adapter.validate_python(config_dict)
            except ValidationError as e:
                raise AppValidationError(f"Invalid configuration: {e}", details=e.errors())

            try:
                await connector.validate(config_obj)
            except Exception as e:
                raise AppValidationError(f"Source validation failed: {e}")

            new_identity_hash = hashlib.sha256(config_obj.identity().encode()).hexdigest()

            # Check conflict if identity changed
            if new_identity_hash != source.identity_hash:
                existing = await self.repository.get_by_identity_hash(new_identity_hash)
                if existing:
                    raise ConflictError(f"A source with identity '{config_obj.identity()}' already exists")
            new_config_dict = config_dict

        updated = await self.repository.update(
            id=id,
            name=new_name,
            config=new_config_dict,
            identity_hash=new_identity_hash,
        )
        if not updated:
            raise NotFoundError(f"Source with id {id} not found")
        return updated

    async def delete_source(self, id: UUID) -> None:
        """Delete source by ID."""
        deleted = await self.repository.delete(id)
        if not deleted:
            raise NotFoundError(f"Source with id {id} not found")

    async def get_schema(self, id: UUID) -> SourceSchema:
        """Get normalized schema for source and update fingerprint/last_opened_at."""
        source = await self.get_source(id)
        connector = self.registry.get(source.kind)

        try:
            adapter = TypeAdapter(SourceConfig)
            config_obj = adapter.validate_python(source.config)
        except ValidationError as e:
            raise AppValidationError(f"Stored configuration is invalid: {e}")

        try:
            schema = await connector.get_schema(config_obj)
            fp = await connector.fingerprint(config_obj)
            now = self.clock.now()

            await self.repository.update(
                id=id,
                fingerprint=fp,
                last_opened_at=now,
            )
            return schema
        except Exception as e:
            raise AppValidationError(f"Failed to read source schema: {e}")


import hashlib
