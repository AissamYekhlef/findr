# Findr Tech Stack

## Frontend

| Layer | Technology | Notes |
|---|---|---|
| **Framework** | Nuxt 4 (Vue 3, TypeScript) | Full-stack Vue with SSR-ready structure; lazy module loading. |
| **State** | Pinia | Stores: `sources`, `activeSource`, `pendingChanges`, `undoStack`, `theme`. |
| **Styling** | CSS (design tokens) | No preprocessor; tokens as CSS custom properties. Derived colors use `color-mix()`. |
| **Table** | Vue component (virtualized) | Custom data table with inline editing, row selection, sticky headers. |
| **Type checking** | TypeScript (strict) | All `.ts` and `.vue` files typed; no `any` without justification. |
| **Build** | Nuxt build system | Vite under the hood. Single bundle per route; modules lazy-loaded. |
| **Package manager** | npm | Lock file committed. |
| **Node version** | 20 LTS+ | Pinned in `.nvmrc`. |

## Backend

| Layer | Technology | Notes |
|---|---|---|
| **Framework** | FastAPI (Python 3.12+) | Async first; Pydantic for validation; OpenAPI docs auto-generated. |
| **Async runtime** | asyncio + asyncpg | Async SQLAlchemy 2.0 ORM for database access. |
| **Database** | PostgreSQL 15+ | Stores source metadata only; user data stays in original files. |
| **Migration tool** | Alembic | Version-controlled, auto-generated migrations. Every schema change is a migration. |
| **File reading** | openpyxl (Excel), csv (CSV/TSV) | Chunked readers for large files; indexed access for paging. |
| **Security** | Argon2 (password hashing), JWT (auth tokens) | Refresh tokens in `HttpOnly` cookies (browser) or Authorization header (API clients). |
| **HTTP client** | httpx | Async, with timeouts, retries, and circuit breaking. |
| **Validation** | Pydantic | Request/response schemas; strict input validation. |
| **Testing** | pytest + pytest-asyncio | Unit tests (fake repos), integration tests (real PostgreSQL in container). |
| **Linting** | ruff | Fast Python linter and formatter; strict rules enforced in CI. |
| **Type checking** | mypy (strict mode) | All `.py` files typed; no implicit `Any`. |
| **Package manager** | uv | Fast installer with lock file. |

## Deployment & Infrastructure

| Component | Technology | Notes |
|---|---|---|
| **Container** | Docker (multi-stage build) | Slim base image, non-root user, minimal final layer. |
| **Compose** | Docker Compose | Local dev: app, PostgreSQL, Redis (for queue/cache in v2+). |
| **CI/CD** | GitHub Actions | Lint, type-check, security scan, test, migration check, spec diff, build. |
| **Reverse proxy** | nginx (in prod) | Serves frontend, proxies `/api` to Uvicorn. Handles TLS and compression. |
| **App server** | Uvicorn (multiple workers) | Graceful shutdown, request logging. |

## Shared Conventions

| Aspect | Decision |
|---|---|
| **API versioning** | `/api/v1` from day one. Breaking changes bump the version. |
| **Error format** | One standard JSON shape: `{ code, message, request_id, details }` |
| **Pagination** | Cursor-based (offset/limit for MVP); metadata: `{ items, total, page, size }` |
| **Timestamps** | ISO 8601, timezone-aware (UTC on backend, local display on frontend). |
| **IDs** | UUIDs (v7 preferred for time-ordering) in the database; stable row IDs per file load. |
| **CORS** | Explicit allow-list (no wildcard with credentials). |
| **Rate limiting** | Redis-backed, per-IP and per-user on auth endpoints. |
| **Logging** | Structured JSON to stdout; request ID propagated across layers. |
| **Secrets** | Environment variables or secret manager; never committed or logged. |

## Data Format: Theme File

```json
{
  "findrTheme": 1,
  "mode": "system",
  "preset": "teal",
  "density": "default",
  "colors": {
    "light": { "accent": "#0A6B60", "ground": "#EDF0EF", "surface": "#FAFBFA", "ink": "#16201E",
               "add": "#1F8A4C", "edit": "#C98A00", "del": "#CC3B3B", "info": "#2F6FCB" },
    "dark":  { "accent": "#3FC1AE", "ground": "#0E1413", "surface": "#151D1B", "ink": "#E3EBE8",
               "add": "#4CC37A", "edit": "#E3B341", "del": "#EF6B6F", "info": "#6FA3EA" }
  }
}
```

## Design System

- **Typography:** Schibsted Grotesk (UI), JetBrains Mono (data).
- **Colors:** Eight base tokens per mode (accent, ground, surface, ink, add, edit, del, info). Derived tokens use `color-mix()`.
- **Spacing:** 4 px base unit (4, 8, 12, 16, 20, 24).
- **Components:** Button, input, select, dialog, menu, table, drawer. No external UI library; components built from first principles.
- **Accessibility:** WCAG 2.1 AA contrast (default presets), keyboard navigation, visible focus, respects `prefers-color-scheme` and `prefers-reduced-motion`.

## Key Dependencies (Versions Pinned)

**Frontend:**
- `nuxt@^4.0.0`
- `vue@^3.4.0`
- `pinia@^2.1.0`
- `typescript@^5.3.0`

**Backend:**
- `fastapi@^0.104.0`
- `sqlalchemy@^2.0.0`
- `asyncpg@^0.29.0`
- `alembic@^1.12.0`
- `pydantic@^2.5.0`
- `pydantic-settings@^2.1.0`
- `argon2-cffi@^23.1.0`
- `python-jose[cryptography]@^3.3.0`
- `openpyxl@^3.1.0`

All versions locked in `pyproject.toml` (backend) and `package-lock.json` (frontend). Automated security scanning in CI.
