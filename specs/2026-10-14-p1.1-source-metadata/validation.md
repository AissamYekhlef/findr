# P1.1: Source Metadata Schema and Endpoints — Validation

## How to Know P1.1 Is Complete

This document defines the tests, manual checks, and acceptance criteria that prove P1.1 is ready to merge and move to P1.2.

---

## Automated Tests (CI)

### Backend Tests (`backend/tests/`)

**1. Config & Startup**
```python
# test_config.py
def test_config_loaded_from_env():
    """Settings loads from environment variables."""
    # Set ALLOWED_SOURCE_ROOTS=C:\Data
    # Instantiate Settings
    # Assert allowed_source_roots includes C:\Data

def test_config_fails_on_missing_allowed_roots():
    """App refuses to boot without ALLOWED_SOURCE_ROOTS set."""
    # Unset ALLOWED_SOURCE_ROOTS
    # Try to create app
    # Expect startup error
```

**2. Source Model & Database**
```python
# test_models.py
def test_source_model_fields():
    """Source ORM model has all required fields."""
    assert hasattr(SourceModel, 'id')
    assert hasattr(SourceModel, 'name')
    assert hasattr(SourceModel, 'kind')
    assert hasattr(SourceModel, 'config')
    assert hasattr(SourceModel, 'config_version')
    assert hasattr(SourceModel, 'identity_hash')
    assert hasattr(SourceModel, 'fingerprint')
    # ... etc

def test_unique_index_on_identity_hash():
    """identity_hash has unique constraint."""
    # Create 2 sources with same identity_hash
    # Expect IntegrityError on second insert
```

**3. Config Models & Validation**
```python
# test_configs.py
def test_csv_config_valid():
    """Valid CsvConfig parses."""
    config = CsvConfig(
        kind="csv",
        path="C:\\Data\\sales.csv",
        delimiter=",",
        encoding="utf-8"
    )
    assert config.kind == "csv"

def test_csv_config_identity():
    """csv_config.identity() returns normalized path."""
    config = CsvConfig(kind="csv", path="C:\\Data\\sales.csv")
    identity = config.identity()
    # On Windows: identity == "c:\\data\\sales.csv" (lowercase, absolute)
    assert identity == config.identity()  # Deterministic

def test_xlsx_config_valid():
    """Valid XlsxConfig parses."""
    config = XlsxConfig(kind="xlsx", path="C:\\Data\\data.xlsx", sheet="Sheet1")
    assert config.kind == "xlsx"

def test_discriminated_union_csv():
    """Discriminated union parses CSV."""
    data = {"kind": "csv", "path": "C:\\Data\\sales.csv"}
    config = SourceConfig.model_validate(data)
    assert isinstance(config, CsvConfig)

def test_discriminated_union_xlsx():
    """Discriminated union parses XLSX."""
    data = {"kind": "xlsx", "path": "C:\\Data\\data.xlsx"}
    config = SourceConfig.model_validate(data)
    assert isinstance(config, XlsxConfig)

def test_relative_path_rejected():
    """Relative paths raise ValidationFailed."""
    config_dict = {"kind": "csv", "path": "data/sales.csv"}
    # Validation should fail
    # (Either Pydantic or service-layer validation)

def test_path_outside_allowed_roots_rejected():
    """Paths outside ALLOWED_SOURCE_ROOTS are rejected."""
    # Set ALLOWED_SOURCE_ROOTS=[C:\Data]
    # Try to register C:\Temp\file.csv
    # Expect ValidationFailed
```

**4. Connector Protocol & Registry**
```python
# test_connectors.py
def test_source_connector_protocol():
    """SourceConnector protocol has required attributes."""
    assert hasattr(SourceConnector, 'kind')
    assert hasattr(SourceConnector, 'capabilities')
    assert hasattr(SourceConnector, 'config_model')

def test_csv_connector_implements_protocol():
    """CsvConnector implements SourceConnector."""
    assert CsvConnector.kind == "csv"
    assert Capability.READ in CsvConnector.capabilities
    assert CsvConnector.config_model == CsvConfig

def test_xlsx_connector_implements_protocol():
    """XlsxConnector implements SourceConnector."""
    assert XlsxConnector.kind == "xlsx"
    assert Capability.READ in XlsxConnector.capabilities

def test_registry_register_and_get():
    """Registry registers and retrieves connectors."""
    registry = SourceConnectorRegistry()
    registry.register("csv", CsvConnector())
    connector = registry.get("csv")
    assert connector.kind == "csv"

def test_registry_unknown_kind_raises():
    """Registry.get() raises for unknown kind."""
    registry = SourceConnectorRegistry()
    # No registration for "fake_kind"
    try:
        registry.get("fake_kind")
        assert False, "Should raise"
    except UnknownKindError:
        pass

def test_registry_list_kinds():
    """Registry.list_kinds() returns all registered kinds."""
    registry = SourceConnectorRegistry()
    registry.register("csv", CsvConnector())
    registry.register("xlsx", XlsxConnector())
    kinds = registry.list_kinds()
    assert "csv" in kinds
    assert "xlsx" in kinds
```

**5. Connector Validation & Schema**
```python
# test_csv_connector.py
@pytest.mark.asyncio
async def test_csv_connector_validate_success():
    """CSV connector validates readable CSV."""
    connector = CsvConnector()
    config = CsvConfig(kind="csv", path="tests/fixtures/sample.csv")
    # Should not raise
    await connector.validate(config)

@pytest.mark.asyncio
async def test_csv_connector_validate_missing_file():
    """CSV connector rejects missing file."""
    connector = CsvConnector()
    config = CsvConfig(kind="csv", path="/nonexistent/file.csv")
    try:
        await connector.validate(config)
        assert False, "Should raise"
    except ValidationFailed:
        pass

@pytest.mark.asyncio
async def test_csv_connector_get_schema():
    """CSV connector returns normalized schema."""
    connector = CsvConnector()
    config = CsvConfig(kind="csv", path="tests/fixtures/sample.csv")
    schema = await connector.get_schema(config)
    assert "entities" in schema
    assert len(schema.entities) > 0
    # First entity has fields
    entity = schema.entities[0]
    assert "fields" in entity
    # Fields have name, type, nullable, samples
    field = entity.fields[0]
    assert hasattr(field, 'name')
    assert hasattr(field, 'type')
    assert hasattr(field, 'nullable')
    assert hasattr(field, 'samples')

@pytest.mark.asyncio
async def test_csv_connector_fingerprint():
    """CSV connector computes SHA-256 fingerprint."""
    connector = CsvConnector()
    config = CsvConfig(kind="csv", path="tests/fixtures/sample.csv")
    fp = await connector.fingerprint(config)
    # Should be consistent
    fp2 = await connector.fingerprint(config)
    assert fp == fp2

# test_xlsx_connector.py
# Similar tests for XLSX connector
```

**6. Repository (Persistence)**
```python
# test_repository.py (with real SQLite)
@pytest.mark.asyncio
async def test_repository_create():
    """Repository creates and persists source."""
    repo = SourceRepository(session)
    source = Source(
        id=UUID(...),
        name="test",
        kind="csv",
        config={"kind": "csv", "path": "..."},
        identity_hash="abc123",
        created_at=...,
        updated_at=...
    )
    result = await repo.create(source)
    assert result.id == source.id

@pytest.mark.asyncio
async def test_repository_unique_identity_hash():
    """Repository rejects duplicate identity_hash."""
    # Create source A with identity_hash="x"
    # Try to create source B with identity_hash="x"
    # Expect IntegrityError (caught and re-raised as ConflictError)

@pytest.mark.asyncio
async def test_repository_get():
    """Repository retrieves source by ID."""
    # Create source
    # Get by ID
    # Assert retrieved source matches

@pytest.mark.asyncio
async def test_repository_list_with_cursor():
    """Repository list respects limit and cursor."""
    # Create 10 sources
    # Call list(limit=5, cursor=None)
    # Assert returns first 5, next_cursor is not None
    # Call list(limit=5, cursor=next_cursor)
    # Assert returns next 5

@pytest.mark.asyncio
async def test_repository_update():
    """Repository updates source."""
    # Create source
    # Update name
    # Assert updated in DB

@pytest.mark.asyncio
async def test_repository_delete():
    """Repository deletes source."""
    # Create source
    # Delete by ID
    # Assert not found on get
```

**7. Service Layer**
```python
# test_service.py (with fake repo, fixed clock, fixed ID)
@pytest.mark.asyncio
async def test_service_create_source():
    """Service creates source with validation."""
    # Call service.create_source("test", "csv", {"kind": "csv", "path": "..."})
    # Assert identity_hash computed
    # Assert source persisted (via fake repo)

@pytest.mark.asyncio
async def test_service_create_duplicate_identity_hash():
    """Service rejects duplicate identity_hash."""
    # Create source A
    # Try to create source with same path
    # Expect ConflictError

@pytest.mark.asyncio
async def test_service_create_unknown_kind():
    """Service rejects unknown kind."""
    # Call service.create_source("test", "unknown_kind", {...})
    # Expect ValidationFailed with code "UNKNOWN_KIND"

@pytest.mark.asyncio
async def test_service_create_invalid_path():
    """Service rejects invalid path."""
    # Call service.create_source with path outside ALLOWED_SOURCE_ROOTS
    # Expect ValidationFailed

@pytest.mark.asyncio
async def test_service_get_schema():
    """Service calls connector to get schema."""
    # Create source
    # Call service.get_schema(source_id)
    # Assert fingerprint updated
    # Assert last_opened_at updated

@pytest.mark.asyncio
async def test_service_update_source():
    """Service updates source, recomputes identity_hash if config changes."""
    # Create source
    # Update config to new path
    # Assert identity_hash recomputed
    # Check for conflicts with new hash

@pytest.mark.asyncio
async def test_service_delete_source():
    """Service deletes source."""
    # Create source
    # Call service.delete_source(id)
    # Assert not found afterward
```

**8. API Endpoints**
```python
# test_api.py (with real app, SQLite)
def test_get_sources_empty():
    """GET /api/v1/sources returns empty list."""
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0

def test_post_sources_success():
    """POST /api/v1/sources creates source."""
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "test_source",
            "kind": "csv",
            "config": {"kind": "csv", "path": "tests/fixtures/sample.csv"}
        }
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "test_source"
    assert body["kind"] == "csv"
    assert "id" in body
    assert "identity_hash" in body

def test_post_sources_duplicate_identity_hash():
    """POST with duplicate path returns 409."""
    # Create source A
    # Try to create with same path
    response = client.post(...)
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "CONFLICT"

def test_post_sources_unknown_kind():
    """POST with unknown kind returns 400."""
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "test",
            "kind": "unknown_kind",
            "config": {}
        }
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_FAILED"

def test_post_sources_path_outside_roots():
    """POST with path outside ALLOWED_SOURCE_ROOTS returns 400."""
    # ALLOWED_SOURCE_ROOTS set to [C:\Data]
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "test",
            "kind": "csv",
            "config": {"kind": "csv", "path": "C:\\Temp\\file.csv"}
        }
    )
    assert response.status_code == 400

def test_get_sources_list():
    """GET /api/v1/sources returns created sources."""
    # Create 2 sources
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

def test_get_sources_cursor_pagination():
    """GET /api/v1/sources with cursor works."""
    # Create 100 sources
    response = client.get("/api/v1/sources?limit=50")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 50
    assert "next_cursor" in body
    # Get next page
    response = client.get(f"/api/v1/sources?limit=50&cursor={body['next_cursor']}")
    assert len(response.json()["items"]) == 50

def test_get_source_by_id():
    """GET /api/v1/sources/{id} returns source."""
    # Create source
    # GET by ID
    response = client.get(f"/api/v1/sources/{source_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == source_id

def test_get_source_not_found():
    """GET /api/v1/sources/{id} for non-existent returns 404."""
    response = client.get("/api/v1/sources/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"

def test_patch_source_update_name():
    """PATCH /api/v1/sources/{id} updates name."""
    # Create source
    response = client.patch(
        f"/api/v1/sources/{source_id}",
        json={"name": "new_name"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "new_name"

def test_patch_source_update_config():
    """PATCH updates config and recomputes identity_hash."""
    # Create CSV source
    # PATCH to new path
    response = client.patch(
        f"/api/v1/sources/{source_id}",
        json={"config": {"kind": "csv", "path": "tests/fixtures/other.csv"}}
    )
    assert response.status_code == 200
    body = response.json()
    # identity_hash should be different
    assert body["identity_hash"] != original_hash

def test_patch_source_conflict():
    """PATCH to config that conflicts with another source returns 409."""
    # Create source A, source B
    # PATCH source A's config to match source B's
    response = client.patch(...)
    assert response.status_code == 409

def test_delete_source():
    """DELETE /api/v1/sources/{id} removes source."""
    # Create source
    response = client.delete(f"/api/v1/sources/{source_id}")
    assert response.status_code == 204
    # Verify not found
    response = client.get(f"/api/v1/sources/{source_id}")
    assert response.status_code == 404

def test_get_schema():
    """GET /api/v1/sources/{id}/schema returns normalized schema."""
    response = client.get(f"/api/v1/sources/{source_id}/schema")
    assert response.status_code == 200
    body = response.json()
    assert "entities" in body
    assert len(body["entities"]) > 0
    entity = body["entities"][0]
    assert "fields" in entity
    field = entity.fields[0]
    assert "name" in field
    assert "type" in field
    assert "nullable" in field
    assert "samples" in field

def test_source_kinds():
    """GET /api/v1/source-kinds returns registered kinds."""
    response = client.get("/api/v1/source-kinds")
    assert response.status_code == 200
    body = response.json()
    # Should have csv and xlsx
    kinds = {k["kind"] for k in body}
    assert "csv" in kinds
    assert "xlsx" in kinds
    # Each kind should have capabilities and config_schema
    for kind_info in body:
        assert "capabilities" in kind_info
        assert "config_schema" in kind_info

def test_error_format():
    """All errors return standard format."""
    response = client.get("/api/v1/sources/invalid-id")
    assert response.status_code == 400 or 404
    body = response.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
```

**9. Extensibility Proof**
```python
# test_extensibility.py
def test_register_fake_connector():
    """Can register a custom connector in test without production code changes."""
    
    class FakeConfig(BaseModel):
        kind: Literal["fake"]
        url: str
    
    class FakeConnector:
        kind = "fake"
        capabilities = Capability.READ
        config_model = FakeConfig
        
        async def validate(self, config):
            pass
        
        async def get_schema(self, config):
            return SourceSchema(entities=[...])
        
        async def fingerprint(self, config):
            return "fake-fingerprint"
    
    # In test container setup:
    registry.register("fake", FakeConnector())
    
    # Verify full flow works:
    response = client.post(
        "/api/v1/sources",
        json={
            "name": "fake_source",
            "kind": "fake",
            "config": {"kind": "fake", "url": "http://example.com"}
        }
    )
    assert response.status_code == 201
    
    # Get schema works
    response = client.get(f"/api/v1/sources/{source_id}/schema")
    assert response.status_code == 200
    
    # Prove no production code was changed (just registration)
```

---

## Manual Tests (Before Merge)

### Test 1: CSV Registration & Schema
```
1. Set ALLOWED_SOURCE_ROOTS=tests/fixtures
2. POST /api/v1/sources:
   { "name": "sales", "kind": "csv", "config": { "kind": "csv", "path": "tests/fixtures/sales.csv" } }
✓ 201, source created with identity_hash, fingerprint=null
3. GET /api/v1/sources/{id}/schema
✓ 200, returns schema with fields, samples, types
4. Verify fingerprint updated in DB (SELECT * FROM sources WHERE id=...)
✓ fingerprint is now SHA-256
5. Verify last_opened_at updated
✓ last_opened_at is recent timestamp
```

### Test 2: XLSX Registration
```
1. POST /api/v1/sources: { "name": "data", "kind": "xlsx", "config": { "kind": "xlsx", "path": "tests/fixtures/data.xlsx", "sheet": "Sheet1" } }
✓ 201, source created
2. GET /api/v1/sources
✓ Both CSV and XLSX listed
3. GET /api/v1/sources/{id}/schema
✓ Schema matches first sheet
```

### Test 3: Duplicate Registration Rejected
```
1. POST /api/v1/sources: { "name": "sales1", "kind": "csv", "config": { ... } } → 201
2. POST /api/v1/sources: { "name": "sales2", "kind": "csv", "config": { ... same path ... } }
✓ 409, error code "CONFLICT"
```

### Test 4: Path Validation
```
1. ALLOWED_SOURCE_ROOTS=C:\Data
2. POST /api/v1/sources with path C:\Temp\file.csv
✓ 400, VALIDATION_FAILED, message mentions allowed roots
3. POST with relative path (data/file.csv)
✓ 400, VALIDATION_FAILED, message mentions absolute path required
4. POST with non-existent path
✓ 400, VALIDATION_FAILED, message mentions file not found
```

### Test 5: Windows Path Normalization
```
1. POST: path = "C:\\Data\\sales.csv" → 201, identity_hash=X
2. POST: path = "c:/data/sales.csv" → 409, conflict (same identity)
✓ Paths are normalized and compared case-insensitively on Windows
```

### Test 6: Unknown Kind
```
1. POST with kind="unknown"
✓ 400, code "UNKNOWN_KIND", message is helpful
```

### Test 7: Cursor Pagination
```
1. Create 150 sources
2. GET /api/v1/sources?limit=50
✓ Returns 50, next_cursor is set, total=150
3. GET /api/v1/sources?limit=50&cursor={cursor}
✓ Returns next 50
4. GET /api/v1/sources?limit=50&cursor={last_cursor}
✓ Returns remaining 50, next_cursor=null
```

### Test 8: Update & Conflict
```
1. Create source A with path P1
2. Create source B with path P2
3. PATCH source A: config with path P2
✓ 409, CONFLICT (identity_hash already exists for B)
4. PATCH source A: name="new_name"
✓ 200, name updated
```

### Test 9: Delete
```
1. Create source
2. DELETE /api/v1/sources/{id}
✓ 204
3. GET /api/v1/sources/{id}
✓ 404 NOT_FOUND
4. GET /api/v1/sources
✓ Empty list
```

### Test 10: GET /api/v1/source-kinds
```
curl http://localhost:8000/api/v1/source-kinds
✓ Returns array with csv and xlsx
✓ Each has capabilities: ["read"]
✓ Each has config_schema (Pydantic JSON Schema)
```

---

## Code Quality Checks (Before Merge)

### Backend
```bash
# All tests pass
pytest backend/tests/unit -v --cov=src/app/modules/sources --cov-report=term-missing
✓ Coverage > 85%, all pass

pytest backend/tests/integration -v
✓ All pass

# Linting
ruff check backend/src/app/modules/sources
✓ No errors

# Type checking
mypy backend/src/app/modules/sources --strict
✓ No errors
```

### Frontend
```bash
npm run test
✓ All pass

npm run lint
✓ No errors

npm run type-check
✓ No errors
```

---

## Sign-Off Checklist

Before marking P1.1 as complete:

- [ ] Config validated at startup; app refuses to boot without ALLOWED_SOURCE_ROOTS.
- [ ] Source table created with unique index on identity_hash.
- [ ] CSV and XLSX connectors implement `SourceConnector` protocol; pass validation & schema tests.
- [ ] Discriminated union config works; `SourceConfig.model_validate()` routes to correct model.
- [ ] Registry: can register/get/list connectors; unknown kinds return error, not 500.
- [ ] Repository: CRUD operations, unique constraint, cursor pagination all work.
- [ ] Service: validates paths, prevents duplicates, raises correct errors, calls connectors.
- [ ] All 7 endpoints implemented: POST, GET (list/one), PATCH, DELETE, /schema, /source-kinds.
- [ ] All errors return `{"error": {"code", "message", "details"}}`.
- [ ] Unit tests >85%, integration tests >80%; all pass.
- [ ] `ruff`, `mypy --strict` pass; no linting errors.
- [ ] Extensibility test: dummy `fake_kind` connector registered and full flow works without production code changes.
- [ ] Manual tests 1–10 completed; documented results.
- [ ] No console errors or warnings in browser (frontend page loads cleanly).
- [ ] No exceptions in server logs.
- [ ] Documentation: `adding-a-source-kind.md` (step-by-step guide), `architecture-sources.md` (overview).
- [ ] PR description explains architecture decisions, links to docs.
- [ ] Code review approved.
- [ ] Merge to `main` branch.

---

## Known Limitations (Not Blocking)

- **Frontend:** No Add dialog yet (deferred to P2+); sources registered programmatically or via CLI.
- **Large files:** DuckDB fingerprint reads first 1MB or uses mod time + size for larger files (optimization, not blocker).
- **Real-time:** No WebSocket or real-time updates; frontend polls.
- **Secrets:** No secret store integration yet (v2+); `secret_ref` column reserved for future use.

---

## Rollback / Revert

If critical issues discovered post-merge:

1. Revert commit: `git revert <commit-hash>`
2. Drop migration: `alembic downgrade -1`
3. Create issue for blocker; prioritize fix.

Otherwise, proceed to P1.2 (Sheet Listing & Schema Detection).
