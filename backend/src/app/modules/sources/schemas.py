"""API request and response schemas for sources."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSourceRequest(BaseModel):
    """Request body for creating a source."""

    name: str = Field(..., min_length=1, max_length=255, description="Source name")
    kind: str = Field(..., min_length=1, max_length=50, description="Source kind (e.g. csv, xlsx)")
    config: dict[str, Any] = Field(..., description="Kind-specific configuration dictionary")


class UpdateSourceRequest(BaseModel):
    """Request body for updating a source."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Updated source name")
    config: dict[str, Any] | None = Field(None, description="Updated configuration dictionary")


class SourceResponse(BaseModel):
    """Response model for a source."""

    id: UUID
    name: str
    kind: str
    config: dict[str, Any]
    config_version: int
    identity_hash: str
    fingerprint: str | None
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None

    model_config = {"from_attributes": True}


class SourceListResponse(BaseModel):
    """Response model for listing sources with cursor pagination."""

    items: list[SourceResponse]
    total: int
    next_cursor: str | None = None


class SourceKindInfoResponse(BaseModel):
    """Response model for a registered source kind."""

    kind: str
    capabilities: list[str]
    config_schema: dict[str, Any]
