# P1.1: Source Metadata Schema and Endpoints — Implementation Plan

## Overview
Implement the backend **source connector abstraction** with CSV and XLSX support, following strict architecture principles: dependency inversion, open/closed principle, and single responsibility. The backend will support extensible source registration without schema changes. File paths are registered directly (not uploaded); validation ensures paths exist and are within allowed roots.

**Estimated duration:** 7–9 days (1.5 weeks)
**Team:** Backend (6–7 days), Frontend (2–3 days); can work in parallel after core foundation

---

## Key Architectural Changes from Earlier Plan

1. **No file uploads MVP:** Sources reference local paths (CSV/XLSX files on disk), not multipart uploads.
2. **Connector abstraction:** `SourceConnector` protocol + registry for extensibility without code changes.
3. **DuckDB reader:** Use DuckDB for all CSV/XLSX reading; unified schema normalization.
4. **Config discriminated union:** `kind`-based config (CsvConfig, XlsxConfig) validated with Pydantic.
5. **Identity hash instead of fingerprint:** SHA-256 of normalized connection identity (path) to prevent duplicates.
6. **Least privilege paths:** Only paths in `ALLOWED_SOURCE_ROOTS` env can be registered.
7. **One error format:** Standard `{"error": {"code", "message", "details"}}` from all endpoints.
8. **Wiring in one place:** All dependencies injected in `container.py`.

---

## Task Groups

### Group 1: Backend — Core Foundation (Days 1–2)

**1.1: Config & Error Hierarchy**
- [ ] Update `src/app/core/config.py`: add `ALLOWED_SOURCE_ROOTS` (env list, validated at startup), `MAX_SOURCE_SIZE` (bytes, for read safety).
- [ ] Ensure `Settings` validates at init; app refuses to boot on bad config.
- [ ] Review `src/app/core/errors.py`: confirm `AppError` base class, `NotFoundError`, `ConflictError`, `ValidationFailed` exist.
- [ ] Ensure all errors follow standard format: `{"error": {"code", "message", "details"}}` (already done in P0.4, verify).

**Acceptance:** `python -c "from src.app.core.config import settings; print(settings.ALLOWED_SOURCE_ROOTS)"` works; app starts with valid env, fails to start with bad env.

**1.2: Database (Source Table)**
- [ ] Create `src/app/features/sources/models.py` with SQLAlchemy ORM model `Source`:
  - Columns: id (UUID v7, PK), name (str, max 255), kind (str), config (JSON), config_version (int, default 1), identity_hash (str, unique index), fingerprint (nullable), secret_ref (nullable), created_at/updated_at (UTC, server-set), last_opened_at (nullable).
  - Use `sqlalchemy.orm.mapped_column` with defaults and constraints.
- [ ] Create Alembic migration: initial migration for `sources` table with unique index on `identity_hash`.
- [ ] Use batch mode (`op.batch_alter_table`) for SQLite compatibility.
- [ ] Run `alembic upgrade head`; verify schema in test database.

**Acceptance:** `psql` or SQLite shows `sources` table with correct columns and unique index on `identity_hash`.

**1.3: Unit of Work & Session Management**
- [ ] Review `src/app/core/db.py`: ensure async session factory and unit of work context manager are correct.
- [ ] One transaction boundary per request (FastAPI dependency).
- [ ] Repositories and services never commit; only the boundary does.

**Acceptance:** Test confirms one open/commit per request; nested calls re-use session.

---

### Group 2: Backend — Domain, Protocols & Connector Abstraction (Days 2–3)

**2.1: Domain Objects & Config Models**
- [ ] Create `src/app/features/sources/domain.py`:
  - `Source` domain object (id, name, kind, config, identity_hash, fingerprint, created_at, etc.).
  - Not an ORM model; values are immutable or DTO-like.
- [ ] Create `src/app/features/sources/configs.py`:
  - `CsvConfig(BaseModel)`: kind="csv", path, delimiter, encoding, header_row.
  - `XlsxConfig(BaseModel)`: kind="xlsx", path, sheet, header_row.
  - `SourceConfig = Annotated[CsvConfig | XlsxConfig, Field(discriminator="kind")]` (Pydantic discriminated union).
  - Each config includes `identity(self) -> str` method: normalized absolute path (Windows: `os.path.normcase(os.path.abspath(...))`).
- [ ] Validation: relative paths rejected, non-existent paths rejected, paths outside `ALLOWED_SOURCE_ROOTS` rejected.

**Acceptance:** `SourceConfig.model_validate({"kind": "csv", "path": "C:\\Data\\sales.csv"})` works; relative paths raise `ValidationFailed`.

**2.2: Connector Protocol & Base Class**
- [ ] Create `src/app/features/sources/protocols.py`:
  - `Capability(Flag)`: READ, WRITE, SQL (bitwise flags).
  - `SourceConnector(Protocol)`:
    - `kind: ClassVar[str]`
    - `capabilities: ClassVar[Capability]`
    - `config_model: ClassVar[type[BaseModel]]`
    - `async def validate(config) -> None` (check file exists, readable, parseable)
    - `async def get_schema(config) -> SourceSchema` (returns normalized schema)
    - `async def fingerprint(config) -> str` (SHA-256 of file contents, for P3)
  - `SourceSchema(BaseModel)`: entities, fields (name, type, nullable, sample rows).
- [ ] Create `src/app/features/sources/connectors/base.py`:
  - Base class with shared validation logic (path normalization, allowed roots check).
  - Abstract methods for subclasses.

**Acceptance:** Protocol is defined; connectors implement it; mypy is happy.

**2.3: Connector Registry**
- [ ] Create `src/app/features/sources/connectors/registry.py`:
  - `SourceConnectorRegistry` class: maps kind → connector.
  - Methods: `register(kind, connector)`, `get(kind)`, `list_kinds()`.
  - Thread-safe (or ensures single-threaded setup in container).
- [ ] Reject unknown kinds at registration or query time; return validation error, not 500.

**Acceptance:** Can register dummy connector in test; unknown kind is rejected with code "UNKNOWN_KIND".

---

### Group 3: Backend — CSV & XLSX Connectors (Days 3–4)

**3.1: CSV Connector**
- [ ] Create `src/app/features/sources/connectors/csv.py`:
  - Implements `SourceConnector` protocol.
  - `kind = "csv"`, `capabilities = Capability.READ`, `config_model = CsvConfig`.
  - `async def validate(config)`: check file exists, is readable, can parse first row (DuckDB).
  - `async def get_schema(config)`: use DuckDB to read first 100 rows; infer types (text, number, date, bool); return normalized schema with sample rows.
  - `async def fingerprint(config)`: SHA-256 of file contents (read first 1MB for large files; if larger, use modification time + size).
- [ ] Use DuckDB connector: `duckdb.sql(f"SELECT * FROM '{path}' LIMIT 100")` with delimiter/encoding options from config.
- [ ] Error handling: invalid delimiter, missing file, unreadable, parse errors → raise `ValidationFailed`.

**Acceptance:** Test: read a CSV with non-default delimiter; schema detected correctly. Test: try to read non-existent file; validation fails with clear message.

**3.2: XLSX Connector**
- [ ] Create `src/app/features/sources/connectors/xlsx.py`:
  - Implements `SourceConnector` protocol.
  - `kind = "xlsx"`, `capabilities = Capability.READ`, `config_model = XlsxConfig`.
  - `async def validate(config)`: check file exists, is readable, enumerate sheets, validate sheet exists (or use first sheet if not specified).
  - `async def get_schema(config)`: use DuckDB to read sheet; infer types; return schema.
  - `async def fingerprint(config)`: SHA-256 of file (or mod time + size).
- [ ] Use DuckDB: `duckdb.sql(f"SELECT * FROM '{path}' LIMIT 100")` (DuckDB auto-detects XLSX).
- [ ] If no sheet specified, use first sheet; store in config on create.

**Acceptance:** Test: read multi-sheet XLSX; schema from specified sheet. Test: create without sheet param; first sheet selected.

---

### Group 4: Backend — Repository & Persistence (Days 4–5)

**4.1: Repository Protocol & SQLAlchemy Implementation**
- [ ] Create `src/app/features/sources/protocols.py` (or extend):
  - `SourceRepository(Protocol)`:
    - `async def create(source: Source) -> Source`
    - `async def get(id: UUID) -> Source | None`
    - `async def list(limit, cursor) -> list[Source]`
    - `async def update(id, name?, config?) -> Source | None`
    - `async def delete(id: UUID) -> bool`
    - `async def get_by_identity_hash(hash: str) -> Source | None`
- [ ] Create `src/app/features/sources/repository.py`:
  - Implements `SourceRepository` using SQLAlchemy ORM.
  - Methods map domain objects ↔ ORM models.
  - No business logic; only persistence and mapping.
  - Queries: `Session.query(SourceModel).filter(...)`.

**Acceptance:** Unit tests with mocked Session; integration tests with real SQLite.

**4.2: Repository Tests**
- [ ] Unit tests (mocked session): create, get, list, update, delete all work (happy path).
- [ ] Integration tests (SQLite):
  - Create a source; read it back.
  - Duplicate identity_hash rejected (409 on insert attempt).
  - Pagination: cursor-based (limit, offset).
  - Windows path normalization: `E:\Data\a.csv` and `e:/data/A.csv` treated as same on Windows.

**Acceptance:** `pytest backend/tests/features/sources/test_repository.py -v` passes; coverage > 85%.

---

### Group 5: Backend — Service Layer (Days 5–6)

**5.1: Source Service**
- [ ] Create `src/app/features/sources/service.py`:
  - `SourceService` class.
  - Dependencies (injected via `__init__`):
    - `SourceRepository`
    - `SourceConnectorRegistry`
    - `Clock` (injected, fixed time in tests)
    - `IdGenerator` (injected, fixed UUID in tests)
  - Methods:
    - `async def create_source(name, kind, config_dict) -> Source`
      - Parse config with discriminated union; validate kind is registered.
      - Call connector.validate(config) to check file exists, readable, path allowed.
      - Compute identity_hash = SHA256(kind + config.identity()).
      - Check for duplicate identity_hash; raise `ConflictError` if found.
      - Generate id, set created_at via Clock, persist to repository.
      - Return domain Source.
    - `async def get_source(id) -> Source` (raise `NotFoundError` if not found)
    - `async def list_sources(limit, cursor) -> list[Source]`
    - `async def update_source(id, name?, config_dict?) -> Source`
      - If config changes, recompute identity_hash, check for duplicate.
      - If name changes, no uniqueness check (only identity_hash is unique).
    - `async def delete_source(id) -> None`
    - `async def get_schema(id) -> SourceSchema`
      - Fetch source, get connector, call connector.get_schema(config).
      - Update fingerprint and last_opened_at via repository.
      - Return schema.

**5.2: Service Validation**
- [ ] All config validation happens here; no business logic in router.
- [ ] Errors: `NotFoundError`, `ConflictError`, `ValidationFailed` (for bad kind, bad path, etc.).
- [ ] Unknown kind → `ValidationFailed` with code "UNKNOWN_KIND", not 500.

**Acceptance:** Unit tests (fake repository, fixed clock, fixed id generator):
  - Create source: identity_hash computed correctly.
  - Duplicate identity_hash: ConflictError raised.
  - Unknown kind: ValidationFailed raised.
  - Paths outside allowed roots: rejected during validate.

---

### Group 6: Backend — API Endpoints (Day 6)

**6.1: Router & Schemas**
- [ ] Create `src/app/features/sources/schemas.py`:
  - `SourceResponse(BaseModel)`: id, name, kind, config, identity_hash, fingerprint, created_at, last_opened_at.
  - `SourceListResponse`: items (list), total, next_cursor.
  - `SourceSchemaResponse`: entities, fields (name, type, nullable, samples).
  - `CreateSourceRequest(BaseModel)`: name, kind, config_dict (with discriminator validation).
  - `UpdateSourceRequest(BaseModel)`: name?, config_dict? (all optional).
  - `SourceKindInfo(BaseModel)`: kind, capabilities, config_json_schema.
- [ ] Create `src/app/features/sources/router.py`:
  - `POST /api/v1/sources`: create. Parse request, call service.create_source(), return 201.
  - `GET /api/v1/sources`: list. Query params: limit (default 50), cursor. Return SourceListResponse.
  - `GET /api/v1/sources/{id}`: get. Return SourceResponse or 404.
  - `PATCH /api/v1/sources/{id}`: update. Parse request, call service.update_source(), return 200.
  - `DELETE /api/v1/sources/{id}`: delete. Call service.delete_source(), return 204.
  - `GET /api/v1/sources/{id}/schema`: get schema. Call service.get_schema(), return SourceSchemaResponse.
  - `GET /api/v1/source-kinds`: list registered kinds. Return list of SourceKindInfo (capabilities, config JSON Schema).

**6.2: Error Handling**
- [ ] All exceptions caught by global handler (from P0.4); ensure all return standard format.
- [ ] Unknown kind, missing file, path validation failures → 400 with code and message.
- [ ] Duplicate identity_hash → 409 with code "CONFLICT".
- [ ] Not found → 404.

**Acceptance:** Manual API tests:
  - `POST /api/v1/sources` with valid CSV path → 201, source created.
  - `POST /api/v1/sources` with duplicate path → 409 "CONFLICT".
  - `POST /api/v1/sources` with unknown kind → 400 "UNKNOWN_KIND".
  - `GET /api/v1/source-kinds` → returns CSV and XLSX with capabilities.

---

### Group 7: Backend — Container & Wiring (Day 6–7)

**7.1: Dependency Injection Setup**
- [ ] Create `src/app/container.py` (or extend if exists):
  - Define `Clock` class (injected; `FixedClock` for tests).
  - Define `IdGenerator` class (injected; `FixedIdGenerator` for tests).
  - Define `FileSystem` class (optional; for future extensibility).
  - Instantiate `SourceConnectorRegistry`.
  - Register connectors: `registry.register("csv", CsvConnector())`, `registry.register("xlsx", XlsxConnector())`.
  - Create factory functions for `SourceService`, `SourceRepository` that inject all dependencies.
  - Wire into FastAPI dependencies so service is available to router.

**7.2: App Factory Updates**
- [ ] Update `src/app/main.py`:
  - Call container setup during app creation.
  - Mount `sources` router: `app.include_router(sources_router, prefix="/api/v1")`.
  - Ensure error handler catches all `AppError` subclasses.

**Acceptance:** App starts, `/api/v1/sources` endpoint is available.

---

### Group 8: Backend — Tests (Days 7–8)

**8.1: Unit Tests (Service)**
- [ ] `backend/tests/unit/features/sources/test_service.py`:
  - Fake repository, fixed clock, fixed ID generator.
  - No database, no file system.
  - Test: create, get, list, update, delete.
  - Test: duplicate identity_hash rejected.
  - Test: unknown kind rejected.
  - Test: config validation.

**8.2: Integration Tests (Repository & API)**
- [ ] `backend/tests/integration/features/sources/test_repository.py`:
  - Real SQLite in-memory or temp file.
  - CRUD operations.
  - Unique constraint on identity_hash.
  - Cursor-based pagination.
- [ ] `backend/tests/integration/features/sources/test_api.py`:
  - Test all endpoints: POST, GET, PATCH, DELETE, /schema, /source-kinds.
  - Test error cases: duplicate, unknown kind, not found, path validation.
  - Test Windows path normalization.
- [ ] `backend/tests/integration/features/sources/test_extensibility.py`:
  - Define a dummy `FakeKind` connector in the test.
  - Register it with the registry.
  - Create, list, get a source of kind `FakeKind`.
  - Prove no production code changed.

**8.3: Test Data & Fixtures**
- [ ] Fixture CSVs and XLSXs in `backend/tests/fixtures/`.
- [ ] Fixture config dicts.

**Acceptance:** `pytest backend/tests/unit -v` and `pytest backend/tests/integration -v` both pass; coverage > 85%.

---

### Group 9: Frontend — Pages & Sidebar (Days 7–8)

**9.1: Sources Sidebar Component**
- [ ] Create `frontend/components/SourcesList.vue`:
  - Display list of sources (from Pinia store).
  - Each item: name, kind badge (CSV/XLSX), created_at.
  - Click to select source (set `activeSourceId` in store).
  - No Add/Edit/Delete yet; focus on display.

**9.2: Sources Page**
- [ ] Create `frontend/pages/sources.vue`:
  - Header: "Sources" title.
  - Layout: sidebar on left, main area on right (empty for now, filled in P1.2).
  - On load: fetch sources from API via Pinia action.
  - Display loading/error states.

**9.3: Pinia Store Update**
- [ ] Update `stores/sources.ts`:
  - Action `fetchSources()`: `GET /api/v1/sources`.
  - Action `createSource(name, kind, config)`: `POST /api/v1/sources`.
  - Action `getSourceKinds()`: `GET /api/v1/source-kinds` (for future form builder).
  - Handle errors; set error state.

**Acceptance:** Manual test: page loads, shows "Add Source" (disabled/hidden for now), lists sources if any exist.

---

### Group 10: Documentation & Code Quality (Days 8–9)

**10.1: Linting & Type Checking**
- [ ] Run `ruff check backend/src` → no errors.
- [ ] Run `mypy backend/src --strict` → no errors.
- [ ] Run `black` or `ruff format` → all formatted.
- [ ] Frontend: `npm run lint`, `npm run type-check` → no errors.

**10.2: Migration Docs**
- [ ] Create `backend/docs/adding-a-source-kind.md`:
  - Step-by-step guide: define config model, implement connector, register in container, write test.
  - Example: add a dummy `mock` connector.
  - Emphasize: no schema changes needed, no router changes, no service changes.

**10.3: Architecture Summary**
- [ ] Create `backend/docs/architecture-sources.md`:
  - Overview of domain, protocols, connectors, repository, service, router.
  - Why each layer exists; dependency directions.
  - How to add a new source kind (link to adding-a-source-kind.md).

**10.4: Git & PR**
- [ ] Squash/rebase commits as needed; clear messages.
- [ ] Create PR: summarize changes, link to architecture docs, mention extensibility proof.

**Acceptance:** All linters pass; docs are clear; PR is approved.

---

## Dependencies & Blockers

- **Backend:** Requires P0.2 (app factory, DB, error handlers) — mostly done; may need small tweaks to error handler.
- **Frontend:** Requires P0.3 (routing, Pinia) — already done.
- **DuckDB:** Add to `backend/pyproject.toml` dependencies.
- **Alembic:** Already set up; just create initial migration.

---

## Success Criteria (P1.1 Complete)

- [ ] All tasks in Groups 1–10 are complete.
- [ ] **Backend:**
  - Config validated at startup; bad config prevents boot.
  - Source table with identity_hash unique index.
  - CSV and XLSX connectors implemented; paths validated, normalized (Windows-safe).
  - Discriminated union config (CsvConfig | XlsxConfig).
  - All 7 endpoints work: POST (create), GET (list, one), PATCH (update), DELETE, /schema, /source-kinds.
  - All errors return standard `{"error": {"code", "message", "details"}}` format.
  - Unit tests >85% coverage; integration tests pass (duplicate detection, path normalization, extensibility proof).
  - `ruff`, `mypy --strict` pass.
- [ ] **Frontend:**
  - Sources page loads; sidebar lists sources.
  - Pinia store actions work; API calls succeed.
  - No hardcoded kind logic; ready for future extensibility.
- [ ] **Docs:**
  - `adding-a-source-kind.md` explains how to extend without production code changes.
  - `architecture-sources.md` documents layers and dependencies.
- [ ] **PR merged to `main`.**

---

## Parallel Work

- **Backend Group 1** (Config/Errors) and **Frontend Group 9** (Pages) can start immediately; no dependencies.
- **Groups 2–3** (Protocols, Connectors) depend on Group 1; start after.
- **Group 4** (Repository) depends on Groups 2–3.
- **Group 5** (Service) depends on Groups 2–4.
- **Group 6** (Router) depends on Group 5.
- **Group 7** (Container) depends on all the above.
- **Group 8** (Tests) can run in parallel with Groups 5–7; just needs mocks/fixtures.
- **Groups 9–10** can be concurrent once Groups 1–6 are stable.

---

## Rollback Plan

If P1.1 needs to be abandoned:
1. Drop `sources` table: `alembic downgrade` to before P1.1 migration.
2. Delete feature branch: `git branch -D 2026-10-14-p1.1-source-metadata`.
3. Return to `main`.

Otherwise, merge PR and continue to P1.2 (Sheet Listing & Schema Detection).

---

## Dependencies & Blockers

- **Backend:** Requires P0.2 (app factory, DB connection) — already done.
- **Frontend:** Requires P0.3 (routing, Pinia) — already done.
- **PapaParse & xlsx.js:** Frontend dependencies for preview; add to `package.json`.

---

## Success Criteria (P1.1 Complete)

- [ ] All tasks in Groups 1–7 are complete.
- [ ] Backend: 4 endpoints (GET, POST, PATCH, DELETE) work correctly; file upload/storage functional.
- [ ] Frontend: dialog, sidebar, pages load; can add/rename/delete sources.
- [ ] End-to-end: upload CSV → appears in sidebar → can rename/delete.
- [ ] Tests: backend (>80%), frontend (>70%), E2E manual sign-off.
- [ ] Code: all linting, type-checking, security scans pass.
- [ ] PR merged to `main`.

---

## Parallel Work

- **Backend Group 1** (DB/Model) and **Frontend Group 3** (Store/API) can start simultaneously.
- **Backend Group 2** (Endpoints) depends on Group 1; start after migrations are tested.
- **Frontend Group 4** (Components) can start once Group 3 is stable; depends on API client being callable.
- **Group 6** (Tests) and **Group 7** (Review) happen concurrently with final implementation.

---

## Rollback Plan

If P1.1 needs to be abandoned:
1. Drop `sources` table: `alembic downgrade` to before P1.1 migration.
2. Delete feature branch: `git branch -D 2026-10-14-p1.1-source-metadata`.
3. Return to `main`.

Otherwise, merge PR and continue to P1.2.
