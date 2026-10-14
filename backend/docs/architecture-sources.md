# Source Architecture Overview

Findr's source management system is built on strict domain-driven design, dependency inversion, and the open/closed principle.

## Layer Structure

```
backend/src/app/modules/sources/
├── configs.py          # Pydantic discriminated union configs (CsvConfig, XlsxConfig)
├── domain.py           # Immutable domain objects (Source)
├── models.py           # SQLAlchemy ORM model (SourceModel)
├── repository.py       # Persistence layer (SourceRepository)
├── service.py          # Business logic (SourceService)
├── router.py           # FastAPI HTTP endpoints (/api/v1/sources)
├── schemas.py          # Request/response validation schemas
├── dependencies.py     # FastAPI dependency injection wiring
└── connectors/
    ├── base.py         # Shared validation and hashing utilities
    ├── registry.py     # Registry mapping kind -> connector
    ├── csv.py          # CSV connector using DuckDB
    └── xlsx.py         # XLSX connector using DuckDB
```

## Key Principles

1. **Open/Closed Principle:** Adding new source connectors requires zero changes to the router, service, repository, or database schema.
2. **Dependency Inversion:** `SourceService` depends on `SourceRepositoryProtocol` and `SourceConnector` protocol, never on concrete implementations.
3. **Identity & Duplication:** Each source has an `identity_hash` (SHA-256 of normalized connection identity, e.g. absolute path), preventing duplicate registrations.
4. **Least Privilege:** Source paths must be within configured `ALLOWED_SOURCE_ROOTS`.
5. **Unified Reading:** DuckDB is used for consistent, high-performance schema inference and data preview across CSV and XLSX files.
