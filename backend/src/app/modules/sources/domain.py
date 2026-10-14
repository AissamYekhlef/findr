"""Domain models for sources."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Source:
    """Immutable source domain object."""

    id: UUID
    name: str
    kind: str
    config: dict
    config_version: int
    identity_hash: str
    fingerprint: str | None
    secret_ref: str | None
    created_at: datetime
    updated_at: datetime
    last_opened_at: datetime | None
