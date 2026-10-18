# P1.1: Source Metadata Schema and Endpoints — Requirements

## Scope

Implement the **source connector abstraction** for Findr: a backend system that registers and manages data sources (CSV, XLSX files) through a protocol-based architecture. Sources are registered from local file paths (not uploaded); the system enforces path safety, prevents duplicate registration, and provides a foundation for extensibility without code changes.

## Context

- **Phase:** PHASE 1 (MVP Read-Only Viewer), Week 3
- **Related:** P1.2 (sheet listing via connectors), P1.3 (data reading), later: P6 (more connectors)
- **Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic, DuckDB (for reading), pytest
- **Architecture Style:** Domain-driven, dependency inversion, protocol-based extensibility
- **File Storage:** Local filesystem; paths must be within `ALLOWED_SOURCE_ROOTS` environment setting (least privilege)

## Core Design Principles

### 1. Extensibility Without Code Changes
- **New source kinds are registered, not hard-coded.**
- Adding PostgreSQL, MySQL, Google Sheets, or MongoDB requires:
  1. A new config model (Pydantic discriminated union member).
  2. A new connector class implementing the `SourceConnector` protocol.
  3. One `register(...)` call in the container.
  - **No changes to:** router, service, repository, database schema, or application code paths.

### 2. Single Responsibility & Dependency Inversion
- **Router:** HTTP only; parses input, calls service, returns response.
- **Service:** Business rules only; depends on protocols (`SourceRepository`, `SourceConnectorRegistry`, `Clock`, `IdGenerator`), never on ORM or file I/O directly.
- **Repository:** Persistence only; SQLAlchemy implementation of `SourceRepository` protocol.
- **Connectors:** Each kind is a separate module; all implement `SourceConnector` protocol.
- **Wiring:** All concrete dependencies injected in `container.py`; no module imports another's concrete class.

### 3. Safety & Least Privilege
- **Path validation:** Only paths inside `ALLOWED_SOURCE_ROOTS` (env list) can be registered.
- **Path normalization:** Windows-safe; `E:\Data\a.csv` and `e:/data/A.csv` are treated as identical on Windows.
- **Read-only:** App opens files read-only; never modifies user's original file.
- **Duplicate prevention:** `identity_hash` (SHA-256 of normalized identity) must be unique; prevents double-registration of same file.

### 4. Fail Fast & Explicit Errors
- **Config validated at startup:** `Settings` must be valid; app refuses to boot with bad `ALLOWED_SOURCE_ROOTS`.
- **All errors follow one format:** `{"error": {"code", "message", "details"}}`.
- **Unknown kinds are validation errors, not 500s.**

## Decisions

### 1. Source Registration Model
- **Decision:** Sources reference local file paths (not uploads).
- **Why:** MVP is local; avoids storage infrastructure complexity. Uploading comes in v2 if needed.
- **How:** User provides `kind` (csv, xlsx) and config dict with `path`. App validates path exists, is readable, is within allowed roots.

### 2. Config as Discriminated Union
- **Decision:** Use Pydantic discriminated union on `kind` field.
  ```python
  class CsvConfig(BaseModel):
      kind: Literal["csv"]
      path: str
      delimiter: str = ","
      encoding: str = "utf-8"
      header_row: int = 0

  class XlsxConfig(BaseModel):
      kind: Literal["xlsx"]
      path: str
      sheet: str | None = None
      header_row: int = 0

  SourceConfig = Annotated[CsvConfig | XlsxConfig, Field(discriminator="kind")]
  ```
- **Why:** Type-safe, Pydantic validates per kind, future kinds (PostgreSQL, Sheets, etc.) are just new union members.

### 3. Connector Protocol
- **Decision:** All sources implement `SourceConnector` protocol:
  - `validate(config)`: Check file exists, readable, parseable.
  - `get_schema(config)`: Return normalized schema (entities, fields).
  - `fingerprint(config)`: SHA-256 for later conflict detection.
- **Why:** New kinds don't touch service, router, or schema.

### 4. DuckDB for Unified Reading
- **Decision:** Use DuckDB to read all CSV/XLSX files.
- **Why:** Single reader, consistent type inference, no separate xlsx/csv logic.

### 5. Identity Hash Instead of Fingerprint
- **Decision:** `identity_hash` (SHA-256 of kind + normalized identity) uniquely identifies a source connection.
- **Why:** Prevents duplicate registration; "normalized identity" for files = absolute, normalized path.
- **Fingerprint** (content hash): Separate, computed on first read, used later for conflict detection (P3+).

### 6. Config Version Field
- **Decision:** `config_version: int` in database; starts at 1.
- **Why:** If a kind's config shape evolves (e.g., CSV adds a new field), migrations can handle old versions.

### 7. No Secrets in Config
- **Decision:** `config` column stores no passwords, API keys, or credentials.
- **Why:** Secrets stored separately (env, secret manager); `secret_ref` column points to secret store if needed (v2+).

### 8. Cursor-Based Pagination
- **Decision:** `GET /api/v1/sources` accepts `limit` and `cursor` (opaque string, not offset).
- **Why:** Scales with large result sets; cursor can be a timestamp or ID.

## Database Schema

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    config_version INT DEFAULT 1,
    identity_hash VARCHAR(64) NOT NULL UNIQUE,
    fingerprint VARCHAR(64),
    secret_ref VARCHAR(255),
    created_at TIMESTAMP UTC NOT NULL,
    updated_at TIMESTAMP UTC NOT NULL,
    last_opened_at TIMESTAMP UTC
);

CREATE INDEX uq_sources_identity_hash ON sources(identity_hash);
```

- **No `type` or `file-specific` columns:** Schema is generic; all kind-specific data in `config`.
- **Naming conventions enforced by Alembic.**

## API Endpoints

### `POST /api/v1/sources` — Create Source
**Request:**
```json
{
  "name": "sales_data",
  "kind": "csv",
  "config": {
    "path": "C:\\Data\\sales.csv",
    "delimiter": ",",
    "encoding": "utf-8",
    "header_row": 0
  }
}
```

**Response (201):**
```json
{
  "id": "uuid-v7",
  "name": "sales_data",
  "kind": "csv",
  "config": {...},
  "identity_hash": "sha256(...)",
  "fingerprint": null,
  "created_at": "2026-10-14T08:50:00Z",
  "updated_at": "2026-10-14T08:50:00Z",
  "last_opened_at": null
}
```

**Errors:**
- `400 VALIDATION_FAILED`: Unknown kind, bad path (outside allowed roots), path doesn't exist, invalid config.
- `409 CONFLICT`: Identity hash already registered (duplicate file).

### `GET /api/v1/sources` — List Sources
**Query params:** `limit=50`, `cursor=<opaque>` (optional)

**Response (200):**
```json
{
  "items": [
    { "id": "...", "name": "...", "kind": "csv", ... }
  ],
  "total": 1,
  "next_cursor": "opaque-string-or-null"
}
```

### `GET /api/v1/sources/{id}` — Get One Source
**Response (200):** Source object.
**Errors:** `404 NOT_FOUND`.

### `PATCH /api/v1/sources/{id}` — Update Source
**Request (all optional):**
```json
{
  "name": "sales_data_updated",
  "config": { "path": "...", ... }
}
```

**Response (200):** Updated source.
**Errors:** 
- `404 NOT_FOUND`
- `409 CONFLICT`: If new config's identity_hash is already registered.
- `400 VALIDATION_FAILED`: Bad config.

### `DELETE /api/v1/sources/{id}` — Delete Source
**Response (204):** No content.
**Errors:** `404 NOT_FOUND`.

### `GET /api/v1/sources/{id}/schema` — Get Schema
**Response (200):**
```json
{
  "entities": [
    {
      "name": "sales",
      "fields": [
        { "name": "amount", "type": "number", "nullable": false, "samples": [100, 200, 150] },
        { "name": "date", "type": "date", "nullable": true, "samples": ["2026-01-01", null, "2026-01-03"] }
      ]
    }
  ]
}
```

**Side effects:** Updates `fingerprint` and `last_opened_at` in the database.
**Errors:** `404 NOT_FOUND`, `400 VALIDATION_FAILED` (if file became unreadable).

### `GET /api/v1/source-kinds` — List Registered Kinds
**Response (200):**
```json
[
  {
    "kind": "csv",
    "capabilities": ["read"],
    "config_schema": { "type": "object", "properties": {...} }
  },
  {
    "kind": "xlsx",
    "capabilities": ["read"],
    "config_schema": { "type": "object", "properties": {...} }
  }
]
```

- Frontend can build dynamic forms without hardcoding kinds.

## Error Response Format

All errors return:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": "Optional extra info"
  }
}
```

**Standard codes:**
- `VALIDATION_FAILED`: Input validation error (unknown kind, bad path, etc.).
- `NOT_FOUND`: Source not found.
- `CONFLICT`: Duplicate identity_hash.
- `INTERNAL_ERROR`: Unexpected server error.

## Configuration (Environment)

```bash
# Allowed source root directories (semicolon-separated on Windows, colon-separated on Unix)
ALLOWED_SOURCE_ROOTS=C:\Data;D:\ProjectData

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/findr

# Logging level
LOG_LEVEL=INFO
```

**Validation:** App starts only if `ALLOWED_SOURCE_ROOTS` is set and directories exist.

## Frontend Integration

- **Page:** `pages/sources.vue` — lists sources, empty main area (filled in P1.2).
- **Sidebar:** `components/SourcesList.vue` — clickable list of registered sources.
- **API:** Pinia store calls `GET /api/v1/sources`, `GET /api/v1/source-kinds` on load.
- **No Add dialog yet:** Postponed to P2 (when editing is ready); for now, sources are registered programmatically or via admin CLI.

## Testing Strategy

### Unit Tests (No DB, No File I/O)
- Service with fake repository, fixed clock, fixed ID generator.
- Verify: config validation, duplicate detection, error messages.

### Integration Tests (Real SQLite, Real Files)
- Repository CRUD, unique constraint on `identity_hash`.
- Connector validation: path normalization, Windows-safe checks.
- **Extensibility proof:** Register a dummy `fake_kind` connector; create/list/get works without production code changes.

### API Tests
- All 7 endpoints with valid/invalid inputs.
- Error codes and messages.

## Acceptance Criteria

- [ ] Source model, table, and migration created; `alembic upgrade head` succeeds.
- [ ] CSV and XLSX connectors implemented; can read first 100 rows, infer schema, compute fingerprint.
- [ ] `SourceConnectorRegistry` works; registering and retrieving connectors works.
- [ ] Service validates config, checks file paths, prevents duplicates, raises correct errors.
- [ ] All 7 endpoints implemented and tested.
- [ ] All errors follow standard format; unknown kinds return 400, not 500.
- [ ] Unit tests >85%, integration tests >80%; all pass.
- [ ] `ruff check`, `mypy --strict` pass.
- [ ] Extensibility test: dummy `fake_kind` connector registered and works.
- [ ] Frontend page loads; sidebar shows registered sources; no API calls fail.
- [ ] Documentation: `adding-a-source-kind.md` + `architecture-sources.md`.

## Open Questions / Deferred

- **Upload support:** MVP registers local paths only. Uploading files comes in v2 or when needed.
- **Concurrent requests:** Assuming stateless FastAPI; no shared state concerns.
- **Real-time updates:** Frontend polls via HTTP; no WebSocket yet.
- **Permissions:** MVP is single-user; multi-user and per-source permissions in v2+.

## Success Metrics

- **Code quality:** No linting or type errors; >85% test coverage.
- **Extensibility:** New source kind (mock connector) added in test with zero production code changes.
- **Performance:** `GET /api/v1/sources` responds in <100ms (in-memory list, SQLite).
- **Security:** All paths validated, no secrets in logs/responses, read-only file access.
