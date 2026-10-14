"""FastAPI router for data sources."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.app.core.exceptions import ValidationError as AppValidationError
from src.app.modules.sources.connectors.registry import SourceConnectorRegistry
from src.app.modules.sources.protocols import SourceSchema
from src.app.modules.sources.schemas import (
    CreateSourceRequest,
    SourceKindInfoResponse,
    SourceListResponse,
    SourceResponse,
    UpdateSourceRequest,
)
from src.app.modules.sources.service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


from src.app.modules.sources.dependencies import get_connector_registry, get_source_service


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: CreateSourceRequest,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceResponse:
    """Create a new data source."""
    source = await service.create_source(
        name=body.name,
        kind=body.kind,
        config_dict=body.config,
    )
    return SourceResponse.model_validate(source)


@router.get("", response_model=SourceListResponse)
async def list_sources(
    service: Annotated[SourceService, Depends(get_source_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> SourceListResponse:
    """List data sources with cursor-based pagination."""
    items, next_cursor = await service.list_sources(limit=limit, cursor=cursor)
    # Note: total count can be added or estimated; for MVP returning items count
    return SourceListResponse(
        items=[SourceResponse.model_validate(item) for item in items],
        total=len(items),
        next_cursor=next_cursor,
    )


@router.get("/kinds", response_model=list[SourceKindInfoResponse])
async def list_source_kinds(
    registry: Annotated[SourceConnectorRegistry, Depends(get_connector_registry)],
) -> list[SourceKindInfoResponse]:
    """List registered source kinds, their capabilities, and config schemas."""
    result = []
    for kind, connector in registry.all().items():
        # Convert capability flags to list of strings
        caps = []
        if connector.capabilities & connector.capabilities.READ:
            caps.append("read")
        if connector.capabilities & connector.capabilities.WRITE:
            caps.append("write")
        if connector.capabilities & connector.capabilities.SQL:
            caps.append("sql")

        # Get Pydantic JSON schema for config model
        config_schema = connector.config_model.model_json_schema()

        result.append(
            SourceKindInfoResponse(
                kind=kind,
                capabilities=caps,
                config_schema=config_schema,
            )
        )
    return result


@router.get("/{id}", response_model=SourceResponse)
async def get_source(
    id: UUID,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceResponse:
    """Get a single data source by ID."""
    source = await service.get_source(id)
    return SourceResponse.model_validate(source)


@router.patch("/{id}", response_model=SourceResponse)
async def update_source(
    id: UUID,
    body: UpdateSourceRequest,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceResponse:
    """Update a data source name or configuration."""
    source = await service.update_source(
        id=id,
        name=body.name,
        config_dict=body.config,
    )
    return SourceResponse.model_validate(source)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    id: UUID,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> None:
    """Delete a data source by ID."""
    await service.delete_source(id)


@router.get("/{id}/schema", response_model=SourceSchema)
async def get_source_schema(
    id: UUID,
    service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceSchema:
    """Get normalized schema for a source and update its fingerprint/last_opened_at."""
    return await service.get_schema(id)
