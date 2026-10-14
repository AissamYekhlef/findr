"""Connector protocols and capabilities."""

from __future__ import annotations

from enum import Flag, auto
from typing import ClassVar, Protocol

from pydantic import BaseModel


class Capability(Flag):
    """Source connector capabilities."""

    READ = auto()
    WRITE = auto()
    SQL = auto()


class SourceSchema(BaseModel):
    """Normalized schema returned by connectors."""

    class Field(BaseModel):
        """Field definition."""

        name: str
        type: str  # text, number, date, boolean, etc.
        nullable: bool
        samples: list[str | int | float | bool | None]

    class Entity(BaseModel):
        """Entity (table/sheet) definition."""

        name: str
        fields: list[SourceSchema.Field]

    entities: list[Entity]

    model_config = {"from_attributes": True}


class SourceConnector(Protocol):
    """Protocol for source connectors."""

    kind: ClassVar[str]
    capabilities: ClassVar[Capability]
    config_model: ClassVar[type[BaseModel]]

    async def validate(self, config: BaseModel) -> None:
        """Validate that the source is accessible and readable.

        Raises:
            ValueError: If source is invalid, inaccessible, or cannot be parsed.
        """
        ...

    async def get_schema(self, config: BaseModel) -> SourceSchema:
        """Get normalized schema from the source.

        Returns:
            SourceSchema: Normalized schema with entities and fields.

        Raises:
            ValueError: If schema cannot be determined.
        """
        ...

    async def fingerprint(self, config: BaseModel) -> str:
        """Compute a content hash for the source.

        Returns:
            str: SHA-256 hex digest or similar stable identifier.

        Raises:
            ValueError: If fingerprint cannot be computed.
        """
        ...

