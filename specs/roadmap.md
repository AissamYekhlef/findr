⚠️ **IMPORTANT:** Before beginning implementation on the roadmap phases, use the AskUserQuestion tool to confirm:
1. **Backend preference:** Async end-to-end with FastAPI + asyncpg + PostgreSQL, or alternative stack?
2. **Frontend framework:** Nuxt 4 with Vue 3 + TypeScript, or alternative (SvelteKit, Next.js)?
3. **Deployment target:** Docker Compose for local dev, cloud platforms (AWS/GCP/Azure), or self-hosted?

These decisions affect tooling setup and all subsequent phases. Get explicit sign-off before proceeding to Phase 0.

---

# Findr Implementation Roadmap

The roadmap breaks the MVP (v0.1) and Part Two (v2.0) into small, shippable phases. Each phase is 1–2 weeks of focused work and ends with a tested, deployable increment.

---

## PHASE 0: Foundation Setup (Weeks 1–2)

### P0.1: Tooling, project structure, and CI
- [x] Initialize backend with `uv`, set up `src/` layout.
- [x] Initialize frontend with Nuxt 4, TypeScript, Pinia.
- [ ] Add ruff, mypy (strict), pre-commit hooks (backend).
- [ ] Add Prettier, TypeScript (strict), ESLint (frontend).
- [ ] Docker Compose: app, PostgreSQL, Redis shells ready.
- [ ] GitHub Actions: lint, type-check, test matrix (local first, then push).
- [ ] **Check:** `make install` and `make test` run cleanly; all CI checks pass.

### P0.2: Backend foundation (config, app factory, database)
- [ ] Centralized Pydantic settings (app, database, security, CORS).
- [ ] FastAPI app factory with lifespan, middleware, and exception handlers.
- [ ] SQLAlchemy async engine, session factory.
- [ ] Alembic setup with autogenerate enabled.
- [ ] Base model: ID (UUID v7), created/updated timestamps (UTC, database-set).
- [ ] Database naming conventions for constraints and indexes.
- [ ] **Check:** App starts cleanly; health endpoint returns 200; database connection works.

### P0.3: Frontend foundation (routing, Pinia, theming shell)
- [ ] Nuxt routes: `/sources` and `/modules/:name`.
- [ ] Pinia stores: `sources`, `theme`.
- [ ] CSS design token skeleton (8 base colors, derived tokens).
- [ ] `useTheme()` composable: sets `data-theme` on root, writes generated `<style>`, persists to localStorage.
- [ ] Light / Dark / System mode toggle (no colors yet, structure only).
- [ ] **Check:** Theme switches modes instantly; localStorage persists; no flash on page reload.

### P0.4: Error handling and API contract
- [ ] Global exception handlers (backend): `NotFound`, `ValidationError`, `PermissionDenied`, `Conflict`, `RateLimited`, catch-all.
- [ ] One error response shape: `{ code, message, request_id, details }`.
- [ ] Pydantic response schemas for all endpoints.
- [ ] OpenAPI spec exported and committed as an artifact.
- [ ] Frontend API client: typed wrapper around `fetch` with error handling.
- [ ] **Check:** Calling a non-existent endpoint returns the error shape; spec validates against schema.

---

## PHASE 1: MVP Read-Only Viewer (Weeks 3–5)

### P1.1: Source metadata schema and endpoints
- [ ] **Backend:** Source model: `id`, `name`, `type` (csv/xlsx), `location` (path), `options` (delimiter, encoding, header_row), `created_at`, `last_opened_at`.
- [ ] Migration to create `sources` table with unique name constraint.
- [ ] Endpoints: `GET /api/v1/sources`, `POST /api/v1/sources` (file upload or path + options), `PATCH /api/v1/sources/{id}`, `DELETE /api/v1/sources/{id}`.
- [ ] **Frontend:** Pinia store: `sources`, `activeSource`. Sidebar: source list, Add button.
- [ ] Add Source dialog: file picker, format options (CSV only for now), preview first 10 rows, confirm.
- [ ] **Check:** Upload a CSV, see it in the sidebar; rename it, delete it (removes from list, not disk).

### P1.2: Sheet listing and schema detection
- [ ] **Backend:** `SourceAdapter` interface (protocol): `list_sheets()`, `get_schema(sheet)`, `read_page(sheet, page, size, sort, filters)`, `apply_changes()`, `fingerprint()`.
- [ ] CSV adapter: single sheet, detect delimiter, headers, types (text, number, date, boolean). Chunked reader.
- [ ] Excel adapter: enumerate sheets; read headers; detect types.
- [ ] Endpoints: `GET /api/v1/sources/{id}/sheets`, `GET /api/v1/sources/{id}/sheets/{sheet}/schema`.
- [ ] **Frontend:** Pinia: `activeSheet`. UI: sheet selector (dropdown if multiple).
- [ ] **Check:** Select a multi-sheet Excel file; see all sheets in the dropdown; switching sheets updates the schema.

### P1.3: Paginated table display
- [ ] **Backend:** Endpoint `GET /api/v1/sources/{id}/sheets/{sheet}/rows?page=1&size=100&sort=name:asc`. Response: `{ items: [], total, page, size, has_next }`.
- [ ] For CSV: build row-offset index on first load (background worker or lazy) for instant paging. For Excel: read via workbook library with bounds to avoid loading all rows.
- [ ] **Frontend:** Data table component (virtualized or paginated). Sticky header. Columns: name, type badge. Rows: data cells.
- [ ] Pagination controls: previous / next, page indicator, size selector (50, 100, 250, 500).
- [ ] Loading state: skeleton rows while fetching.
- [ ] **Check:** Open a 100k-row CSV; first page loads in under 2 seconds; paging to page 50 is under 300 ms. Table scrolls smoothly.

### P1.4: Sorting and searching
- [ ] **Backend:** Query parameters: `sort=column:asc|desc` (allow-listed columns), `q=text` (global search across all columns), `filter=column:op:value` (contains, equals, gt, lt, is_empty).
- [ ] CSV adapter: in-memory filtering on the page; global search walks all rows (or uses index if built).
- [ ] Excel adapter: read the sheet once, filter in memory.
- [ ] **Frontend:** Sort UI: click column header to cycle asc/desc/none. Search input (top of table). Filter button (menu with per-column filters). UI shows active sort/search/filters.
- [ ] **Check:** Sort by amount (ascending); search for "John"; filter by date > 2026-01-01; all work together correctly.

### P1.5: Theme presets and live color editing
- [ ] **Backend:** Store theme in frontend localStorage only (MVP).
- [ ] **Frontend:** `useTheme()` composable: implement `setMode()`, `setPreset()`, `setColor()`, `resetColors()`, `exportTheme()`, `importTheme()`.
- [ ] Five presets: Teal, Indigo, Graphite, Copper, Plum (each with light and dark palettes).
- [ ] Theme page (inside Modules): mode switcher (System, Light, Dark), preset chips, color picker for eight base colors.
- [ ] Derived tokens computed with `color-mix()` in CSS.
- [ ] Contrast ratio badge: show AA / AAA for text on surface, accent on surface, button text.
- [ ] **Check:** Switch to Dark mode; app recolors instantly. Pick a custom color; all instances update live. Export theme as JSON; paste it back; same look restored.

---

## PHASE 2: MVP Editing & Pending Changes (Weeks 6–8)

### P2.1: Inline cell editing and validation
- [ ] **Frontend:** Table cell: double-click or Enter to edit. Input validates against column type.
- [ ] Type-aware inputs: text input, number input, date picker, checkbox.
- [ ] Invalid input shows inline error (e.g., "Must be a number"). Escape cancels; Tab or Enter commits.
- [ ] Edited cell marked with icon (✎) and soft highlight. Pending state: unsaved marker.
- [ ] **Check:** Edit a text cell; edit a number cell (reject non-numeric input); edit a date cell.

### P2.2: Add and delete rows
- [ ] **Frontend:** Toolbar button "Add row" (inserts blank row at top or bottom, user's preference). Rows are auto-numbered as "auto" until saved.
- [ ] Row selection: checkbox column, multi-select. "Delete" button removes selected rows from view. Deleted rows struck through, dimmed color.
- [ ] **Pinia:** `pendingChanges` store tracks inserts, updates, deletes with temp IDs for new rows.
- [ ] **Check:** Add three rows; edit one; delete one; see all three states (added, edited, deleted) in the UI with distinct markers.

### P2.3: Undo / Redo
- [ ] **Pinia:** `undoStack`, `redoStack` store snapshots of `pendingChanges`.
- [ ] Keyboard: Ctrl/Cmd+Z (undo), Ctrl/Cmd+Shift+Z (redo). Buttons in toolbar.
- [ ] Each edit (cell change, add, delete) is one undo step. Redo available after undo.
- [ ] **Check:** Edit a cell; undo; value reverts. Add a row; undo; row removed. Redo adds it back.

### P2.4: Pending changes drawer and review
- [ ] **Frontend:** Right sidebar (or drawer) lists all pending changes grouped by Added / Edited / Deleted.
- [ ] Each change shows: row number or temp ID, columns changed, old value (if update), new value.
- [ ] Per-change revert button; clears the change from pending.
- [ ] Counter badge in toolbar: "3 pending changes".
- [ ] **Check:** Add, edit, delete rows; drawer shows all grouped correctly. Revert one edit; it's removed from drawer and table.

### P2.5: Discard and unsaved-changes warning
- [ ] **Frontend:** Save bar (sticky at bottom when pending changes exist): "Discard" and "Save changes" buttons.
- [ ] Discard: clears all pending changes, resets table to original state.
- [ ] Leaving the page or switching source with unsaved changes: confirmation dialog.
- [ ] **Check:** Make changes; click Discard; table resets. Make changes; switch to a module; dialog appears.

---

## PHASE 3: MVP Atomic Save & File Safety (Weeks 9–11)

### P3.1: Change validation and application engine
- [ ] **Backend:** `ChangeSet` schema: `{ fingerprint, inserts: [{ temp_id, values }], updates: [{ row_id, values }], deletes: [row_id] }`.
- [ ] Service layer: validate each change (row exists for update/delete, values match column types, no ID or role fields changed).
- [ ] Apply changes to an in-memory copy of the sheet data first (dry run to detect conflicts).
- [ ] **Check:** Send invalid changes (bad type, missing row); service rejects with clear error.

### P3.2: Atomic file writes and backup
- [ ] **Backend:** Before first write in a session, create backup: `source.name + '.bak-' + timestamp`.
- [ ] Backup service: keep last 5 (configurable), delete older ones.
- [ ] Write: apply changes to a temp file, compare fingerprints, atomically replace original (move on Unix, replace on Windows).
- [ ] If write fails: original and temp are both on disk; original is untouched.
- [ ] **Frontend:** Save button shows progress spinner. On success: brief toast confirmation. On error: error dialog with message.
- [ ] **Check:** Save changes; backup exists on disk. Force a write error; original file is byte-identical to before. Reopen the file in Excel; changes are there.

### P3.3: Conflict detection (external file modification)
- [ ] **Backend:** `fingerprint()` method per adapter: hash of file contents or modification time + size.
- [ ] Endpoint `POST /api/v1/sources/{id}/sheets/{sheet}/changes` accepts fingerprint in request; compares to current.
- [ ] If mismatch: return `{ ok: false, conflict: true, current_fingerprint }` instead of applying.
- [ ] **Frontend:** On conflict response: dialog "The file changed on disk. [Reload] [Overwrite] [Cancel]".
- [ ] Reload: discard pending changes, refetch data from server. Overwrite: proceed with save (user's choice).
- [ ] **Check:** Save a change in Findr. Edit the file in Excel externally. Try to save in Findr; conflict dialog appears.

### P3.4: CSV and Excel format preservation
- [ ] **Backend:** CSV adapter: on write, preserve original delimiter, encoding, line endings.
- [ ] Excel adapter: preserve other sheets, column widths, number formats (where supported). Warn if macros or charts cannot be preserved.
- [ ] **Frontend:** Export endpoint `GET /api/v1/sources/{id}/sheets/{sheet}/export?format=csv|xlsx` with current filters and sort applied.
- [ ] Export dialog: choose format, choose rows (all, filtered, selected).
- [ ] **Check:** Add a row to CSV; save; reopen in text editor; delimiter and encoding unchanged. Add a row to Excel; save; other sheets and formats untouched.

### P3.5: Error states and recovery
- [ ] **Frontend:** Source list shows status icon: ok (checkmark), missing (warning), unsaved (dot).
- [ ] Click "Locate file" on missing source: file picker to find the file on disk, update path.
- [ ] Read-only files: show as read-only mode; no edit button.
- [ ] **Check:** Move a source file; Findr marks it missing. Use Locate to find it. Open a read-only file; editing is disabled.

---

## PHASE 4: MVP Polish & Accessibility (Weeks 12–14)

### P4.1: Column visibility and width persistence
- [ ] **Frontend:** Column menu: checkboxes to hide/show columns. Drag to reorder. Resizable column headers.
- [ ] Settings per source: saved to browser localStorage (MVP) or server (v2).
- [ ] **Pinia:** Store per-source column visibility and widths.
- [ ] **Check:** Hide a column; reload page; it's still hidden.

### P4.2: Keyboard shortcuts and table navigation
- [ ] Keyboard: Enter / double-click to edit cell; Escape to cancel; Tab / Shift+Tab to move to next/prev cell in edit mode.
- [ ] Arrow keys to move between rows and columns (not in edit mode).
- [ ] Ctrl/Cmd+S to save; Ctrl/Cmd+Z to undo; Delete to delete selected rows.
- [ ] **Check:** Navigate table with arrow keys; edit with Enter; switch cells with Tab; save with Ctrl+S.

### P4.3: Module previews (Dashboard, Users, Roles, History)
- [ ] **Frontend:** Module pages load fixture JSON files (zero API calls).
- [ ] Each page shows example data with the notice "Example data. This module becomes live in v2."
- [ ] Buttons (New role, Invite user, Restore) respond with toast: "<Action> arrives in v2".
- [ ] **Check:** Navigate to Dashboard, Users, Roles, History; no network requests made; notice shown.

### P4.4: Header and navigation refinement
- [ ] Header: Findr logo, [Sources] [Modules ▾] tabs, search (Sources only, hidden in Modules), Theme menu, Export.
- [ ] Modules menu: list items with description and `v2` or `Live` tag.
- [ ] Theme menu: mode quick-select, presets, link to Appearance.
- [ ] Active module/section highlighted in header.
- [ ] **Check:** Click Modules; menu appears. Click Dashboard; it's marked active. Hover over menu items; descriptions show.

### P4.5: Accessibility pass
- [ ] WCAG 2.1 AA: all presets meet 4.5:1 contrast (text, buttons).
- [ ] Focus outlines: 2 px accent outline, visible in every theme.
- [ ] Keyboard navigation: tab through all controls; no focus traps.
- [ ] Semantic HTML: buttons are `<button>`, links are `<a>`, tables use `<table>` with headers.
- [ ] Respects `prefers-color-scheme` and `prefers-reduced-motion`.
- [ ] Screen reader: table headers announced; state changes announced (edit mode, saved, error).
- [ ] **Check:** Run with axe or Lighthouse; pass WCAG AA. Navigate with keyboard only.

### P4.6: Responsive design (tablet & desktop)
- [ ] Sidebar: fixed on desktop (240 px), collapses to horizontal chips on tablet (<760 px).
- [ ] Table: scrolls horizontally on mobile/tablet if needed.
- [ ] Modals: full-width on mobile, centered on desktop.
- [ ] Touch-friendly: buttons ≥ 44 px, input ≥ 44 px touch target.
- [ ] **Check:** Test on desktop, tablet (768 px), mobile (375 px) viewports.

---

## PHASE 5: MVP Hardening & Deployment (Weeks 15–16)

### P5.1: Security hardening
- [ ] **Backend:** Input validation: Pydantic strict on all schemas, reject unknown fields, enforce length limits.
- [ ] SQL injection: ORM only, no string-built queries.
- [ ] CORS: explicit allow-list (no wildcard with credentials).
- [ ] Security headers: HSTS, X-Content-Type-Options, frame protection, CSP (if HTML served), Referrer-Policy.
- [ ] Rate limiting: Redis-backed, per-IP and per-user on file upload and API endpoints.
- [ ] Request limits: max upload 500 MB, max row size 1 MB, request timeout 30 s.
- [ ] Logging: structured JSON, no tokens or passwords, request ID propagated.
- [ ] **Check:** Run OWASP Top 10 checklist; all items addressed.

### P5.2: Performance optimization
- [ ] **Backend:** Connection pooling (asyncpg), query optimization (eager load related data), pagination limits enforced.
- [ ] Compression: gzip on responses.
- [ ] Caching: ETag for schema and metadata endpoints (cache-control: 1 hour).
- [ ] Large file handling: stream CSV reading, chunk Excel reading, avoid loading entire file into memory.
- [ ] **Frontend:** Lazy-load module pages. Virtualize table rows (only render visible). Minify and compress bundle.
- [ ] **Check:** Lighthouse score ≥ 90 (performance). 100k-row file opens in < 2 s, pages in < 300 ms.

### P5.3: Docker and CI/CD pipeline
- [ ] **Docker:** Multi-stage build; slim runtime image; non-root user; minimal final layer.
- [ ] **Compose:** App (port 8000), PostgreSQL (port 5432), Redis (port 6379 for v2).
- [ ] **CI:** GitHub Actions matrix (lint backend/frontend, type-check, test, migration check, security scan, build image).
- [ ] Pre-commit hooks: ruff, mypy, prettier, type-check run locally before push.
- [ ] **Check:** `docker compose up` starts all services. CI pipeline passes. Image builds and runs locally.

### P5.4: Observability and logging
- [ ] **Backend:** Structured JSON logs to stdout (request ID, method, path, status, duration, user if auth implemented).
- [ ] Health endpoints: `GET /health` (cheap liveness), `GET /health/ready` (database and cache check).
- [ ] Error logging: catch-all handler logs full stack trace with request ID (no output to client).
- [ ] **Frontend:** Client-side error logging (Sentry optional for MVP, or simple logging service).
- [ ] **Check:** Start app; logs appear as JSON in console. Make requests; request IDs correlate logs across layers.

### P5.5: Documentation and runbooks
- [ ] **Repo:**  README: 5-minute setup guide (clone, `make install`, `make run`, open http://localhost:3000).
- [ ] `docs/decisions.md`: Why PostgreSQL, why async, JWT + cookies, pagination strategy, API versioning.
- [ ] `docs/architecture.md`: Modular monolith layers, dependencies, module template.
- [ ] `docs/runbook.md`: Backup recovery, disaster restore, scaling to large files.
- [ ] **Check:** New dev clones repo, runs `make install && make run`, sees the app in browser.

### P5.6: Integration and smoke tests
- [ ] End-to-end test: upload CSV → add row → save → reopen in Excel; row is there.
- [ ] Upload Excel → add row → save → reopen in Excel; row is there, other sheets untouched.
- [ ] Conflict scenario: save in Findr, edit externally, save in Findr; conflict dialog appears.
- [ ] Theme persistence: set custom theme, reload page, theme is still applied.
- [ ] **Check:** All smoke tests pass. Manual QA sign-off.

---

## PHASE 6: Part Two — Multi-connector Support (v2.0, starting Week 17)

### P6.1: PostgreSQL adapter
- [ ] Implement `SourceAdapter` for PostgreSQL: list schemas/tables, read schema, page rows, apply changes.
- [ ] Credentials UI: host, port, database, user, password (stored encrypted).
- [ ] Connection pooling and timeouts.

### P6.2: Saved views
- [ ] Store: sort, filters, visible columns, page size per view.
- [ ] Views CRUD endpoints and UI.

### P6.3: Charts and dashboards
- [ ] Bar, line, pie, table charts; configurable axes and aggregation.
- [ ] Save charts with views.

### P6.4: Multi-user and history
- [ ] User accounts, roles (viewer, editor, admin), per-source permissions.
- [ ] Change log: who, when, what, restore.
- [ ] Users and Roles modules go live.

### P6.5: More connectors
- [ ] MySQL, SQLite, MS Access adapters.
- [ ] REST API source.

---

## Acceptance Criteria (MVP Complete)

- [ ] Adding CSV and XLSX files shows each with correct sheets.
- [ ] Selecting a source displays paginated data with sorting and search.
- [ ] Editing, adding, and deleting rows mark them pending with visual indicators.
- [ ] Save writes exactly those changes; reopening in Excel shows them.
- [ ] Backup exists after first save.
- [ ] External modification triggers conflict dialog.
- [ ] Discard and Undo work correctly.
- [ ] 100k-row CSV: <2s first page, <300ms per request.
- [ ] Header shows Sources and Modules; Modules lists Dashboard, Users, Roles, History (v2 tag), Appearance (Live).
- [ ] Unsaved changes persist when switching between Sources and Modules.
- [ ] Dashboard, Users, Roles, History show example data only; no API calls.
- [ ] Theme mode (Dark/Light/System) switches app instantly.
- [ ] Custom colors update live in the picker; exported theme can be re-imported.
- [ ] Theme persists across reload without flash of default.
- [ ] Appearance page shows contrast ratios; low-contrast flagged but applied.
- [ ] WCAG 2.1 AA pass: contrast, keyboard nav, focus outlines, semantics.
- [ ] Keyboard shortcuts work: Ctrl+S (save), Ctrl+Z (undo), Delete (delete rows), Enter (edit).
- [ ] All CI checks pass: lint, type, security, tests, spec diff.

---

## Timeline Summary

| Phase | Duration | Deliverable | Release |
|---|---|---|---|
| **P0** | 2 weeks | Tooling, foundation, theming shell | Internal |
| **P1** | 3 weeks | Read-only viewer + presets | Alpha 0.1 |
| **P2** | 3 weeks | Editing, undo, pending changes | Beta 0.1 |
| **P3** | 3 weeks | Atomic save, backups, conflict detection | RC 0.1 |
| **P4** | 3 weeks | Polish, accessibility, keyboard shortcuts | **MVP v0.1** |
| **P5** | 2 weeks | Security, performance, deployment | Production v0.1 |
| **P6** | TBD | Connectors, multi-user, history | **v2.0** |

**Total MVP:** ~16 weeks (4 months) to production-ready.
