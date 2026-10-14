# Architecture Decisions

This document records the key architectural decisions made for Findr, why they were chosen, and their trade-offs.

## 1. Async End-to-End (FastAPI + asyncpg + SQLAlchemy 2.0)

**Decision:** Use async/await throughout the stack: FastAPI, asyncpg driver, and SQLAlchemy 2.0 ORM.

**Rationale:**
- Large file handling: Paging 100k+ row files requires non-blocking I/O to avoid thread starvation
- Concurrent requests: Single thread pool handles many simultaneous requests efficiently
- External APIs: Async allows timeouts and retries without blocking the event loop
- Modern Python: Async is now mature and well-integrated in FastAPI

**Trade-offs:**
- Steeper learning curve: Developers must understand async/await patterns
- Library compatibility: Not all Python libraries support async (mitigated with thread pool wrapper)
- Debugging complexity: Async stack traces can be harder to read

**Impact:**
- All database access uses `async with get_session()`
- All repositories use `async def` methods
- Services layer is async-first
- Route handlers are async

## 2. One Transaction Per Request

**Decision:** The service layer commits transactions; repositories never commit.

**Rationale:**
- Clear ownership: One place to control the transaction boundary
- Atomic operations: Multi-step operations either fully commit or fully roll back
- Safety: Prevents accidental partial writes or inconsistent data
- Testability: Services can be tested in isolation with fake repositories

**Trade-offs:**
- All database changes must flow through services (no direct queries in routes)
- Requires careful dependency injection setup
- Long transactions must be short (never call external APIs inside a transaction)

**Implementation:**
```python
# Repositories do NOT commit
async def create_source(self, session: AsyncSession, data: SourceCreate) -> Source:
    source = Source(**data.dict())
    session.add(source)
    # Do NOT flush or commit
    return source

# Services DO commit
async def add_source(self, session: AsyncSession, data: SourceCreate) -> Source:
    source = await repository.create_source(session, data)
    await session.commit()
    return source
```

## 3. Modular Monolith (Not Microservices)

**Decision:** Single FastAPI application split into feature modules (sources, users, roles, etc.), not separate microservices.

**Rationale:**
- Simpler deployment: One process, one database, one deployment
- Easier debugging: Stack traces stay within one codebase
- Shared transactions: Can span multiple modules atomically
- Easy to split later: If a module needs scaling, split it into a service later
- Scaling: Findr's use case (CSV/database reading) doesn't require separate services yet

**Trade-offs:**
- One module's performance issues affect the whole app
- Must share database (no service-specific databases)
- Requires discipline to keep modules decoupled

**Structure:**
```
src/app/modules/
├── sources/
│   ├── router.py       (HTTP endpoints)
│   ├── schemas.py      (request/response models)
│   ├── models.py       (database models)
│   ├── service.py      (business logic)
│   ├── repository.py   (database access)
│   └── exceptions.py   (domain errors)
├── users/             (same structure, future)
└── roles/             (same structure, future)
```

## 4. Custom Components Over UI Library

**Decision:** Build UI components from scratch using CSS custom properties, not Material Design or Bootstrap.

**Rationale:**
- Full control: Design system is exactly what we need, nothing extra
- Smaller bundle: No bloated library, no unused components
- Themeable: CSS variables make light/dark/custom themes trivial
- Accessibility: Can enforce WCAG standards throughout
- Performance: Only the CSS we use, no framework overhead

**Trade-offs:**
- More work to build basics: buttons, inputs, tables
- No component library ecosystem
- Requires discipline in token management

**Implementation:**
- 8 base color tokens per mode (light/dark)
- Derived tokens with `color-mix()` (no CSS preprocessor)
- Density tokens (row height, padding)
- Spacing scale (4px base unit)

## 5. SQLAlchemy ORM (Not Raw SQL)

**Decision:** Use SQLAlchemy 2.0 ORM for all database access, never raw SQL.

**Rationale:**
- Security: Prevents SQL injection via parameterized queries
- Maintainability: Queries are Python code, easier to version control and test
- Type safety: ORM provides type hints for models
- Migration support: Alembic integrates with ORM for schema versioning
- Async support: SQLAlchemy 2.0 has excellent async support

**Trade-offs:**
- ORM can be slower than hand-tuned SQL (but Findr doesn't have complex queries yet)
- Learning curve for ORM patterns

## 6. Pydantic for Validation (Not Custom)

**Decision:** Use Pydantic v2 for all input/output validation.

**Rationale:**
- Type-safe: Full TypeScript-like type checking
- Fast: Optimized C implementation
- Documented: OpenAPI schema auto-generated from schemas
- Ecosystem: Integrates with FastAPI, SQLAlchemy, etc.
- Strict by default: No implicit type coercion

**Trade-offs:**
- Schemas must be kept in sync with models (use factories to avoid duplication)
- Validation errors need translation to HTTP errors

## 7. PostgreSQL (Not SQLite)

**Decision:** Use PostgreSQL for production; SQLite for testing.

**Rationale:**
- Production-ready: Handles concurrent access, large data, complex queries
- Async driver: asyncpg is the fastest PostgreSQL client for Python
- Mature: Battle-tested at scale
- Open source: No licensing issues

**Trade-offs:**
- Requires Docker Compose for local development
- More setup than SQLite
- Need to manage database manually in production

## 8. Alembic for Migrations (Not ORM Auto-Create)

**Decision:** Use Alembic for all schema changes; never create tables at startup.

**Rationale:**
- Version control: Every schema change is tracked and reviewable
- Reversibility: Can roll back bad migrations
- Team collaboration: Migrations can be discussed in PRs
- Safety: No accidental schema changes in production
- Consistency: Same process for local, staging, and production

**Trade-offs:**
- Must write migrations manually (or use autogenerate, then review)
- Extra process step before deploying

## 9. Pinia for Frontend State (Not Context API)

**Decision:** Use Pinia (Vue's store library) for all global state.

**Rationale:**
- Type-safe: Full TypeScript support
- Composable: Stores are composables, not classes
- DevTools: Browser extension for time-travel debugging
- Testing: Stores are easy to mock and test
- Scalable: Works well for small and large apps

**Trade-offs:**
- One more library to learn
- Requires discipline not to put everything in stores

## 10. Environment Variables (Not Config Files)

**Decision:** All configuration comes from environment variables; `.env` file for local development only.

**Rationale:**
- 12-factor app: Standard practice for cloud-native apps
- Secret management: Secrets never committed to git
- Environment parity: Same code runs in dev, staging, production
- Container friendly: Docker and Kubernetes use env vars natively

**Trade-offs:**
- No `.gitignore` for config files (they're all env vars)
- Must document all required variables

**Implementation:**
- Pydantic settings read from environment
- `.env.example` documents all variables
- Production requires explicit env var setup
- Validation at startup fails loudly if required vars are missing

---

## Future Considerations

**When to reconsider:**
- Microservices: If individual modules scale separately, split then
- CQRS: If read/write patterns diverge significantly
- Event sourcing: If audit trails become critical
- GraphQL: If client queries become complex
- Real-time: If WebSockets become necessary (for now, REST + polling)

**Current good enough, no change needed:**
- Single FastAPI app (scales with more workers)
- PostgreSQL only (can add read replicas later)
- Pinia stores (fine for current scope)
- Custom components (keep until library becomes necessary)

