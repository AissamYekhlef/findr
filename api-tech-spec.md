# Production-grade FastAPI starter: build instructions

This is a build guide with no code, in the order I'd do it. Each step ends with a **check** so you know it's done before moving on.

## The target architecture

A **modular monolith with a layered core**: one deployable app, split into feature modules. Each module has the same four layers, and dependencies point in one direction only:

**API layer → Service layer → Repository layer → Database**

- **API layer:** HTTP only. It parses requests, calls one service, and shapes the response.
- **Service layer:** business rules. It knows nothing about HTTP or SQL.
- **Repository layer:** all database queries. It's the only place that knows the ORM.
- **Domain/schemas:** the data shapes shared across layers.

**The rule that keeps it clean:** a layer may only call the layer directly below it. Enforce this with an import linter in CI (Step 12).

## Phase 1: Foundation

### Step 1: Decide before you build
Write these down in a short `docs/decisions` file, because changing them later is expensive:
- Sync or async (I recommend **async end to end**: async SQLAlchemy 2.0 with asyncpg).
- Database: **PostgreSQL**. Auth style: JWT access plus refresh tokens in `HttpOnly` cookies for browsers, and the `Authorization` header for mobile or API clients.
- API versioning (`/api/v1`), one error format, and one pagination style.
- Python version (latest stable) and the supported deployment target (Docker).

**Check:** a decisions file exists and the team agrees on it.

### Step 2: Create the repository and tooling
1. Initialize the project with **uv**, using a `src/` layout so imports can't accidentally resolve from the working directory.
2. Put all configuration in `pyproject.toml`: dependencies split into runtime and dev groups, plus settings for ruff, mypy (or pyright), and pytest.
3. Pin dependencies with a lockfile and commit it.
4. Add **ruff** for linting and formatting, **mypy in strict mode** for types, and **pre-commit** hooks to run both.
5. Add `.gitignore`, `.env.example` (committed, with no real secrets), `.editorconfig`, and a `README` that lets a new developer run the project in five minutes.
6. Add a **Makefile or task runner** with one command each for: install, run, lint, type-check, test, migrate, and build image.

**Check:** a fresh clone runs `install` then `test` successfully with zero manual steps.

### Step 3: Lay out the folders

| Folder | Purpose |
|---|---|
| `src/app/main` | App factory: creates the app, registers routers, middleware, and handlers |
| `src/app/core` | Cross-cutting infrastructure: config, security, logging, database setup, exceptions, constants |
| `src/app/api` | Shared API pieces: dependencies, versioned router aggregation, error handlers |
| `src/app/modules/<feature>` | One folder per feature, each with `router`, `schemas`, `models`, `service`, `repository`, `exceptions`, `dependencies` |
| `src/app/common` | Genuinely shared building blocks: base repository, pagination, base schemas, utilities |
| `src/app/integrations` | Adapters for external systems: email, SMS, storage, payments |
| `src/app/workers` | Background jobs |
| `migrations` | Alembic migrations |
| `tests` | Mirrors `src/app`: unit, integration, and end-to-end |
| `deploy` | Dockerfile, compose files, CI configs |
| `docs` | Decisions, architecture notes, runbooks |

Organize **by feature, not by file type**. A top-level `models/` and `routers/` folder stops scaling around ten entities.

**Check:** you can explain where any new piece of code belongs without hesitation.

### Step 4: Centralized configuration
1. Create one settings object using **pydantic-settings**, read from environment variables.
2. Group settings: app, database, security, CORS, logging, external services.
3. Validate at startup so the app **refuses to boot** with missing or invalid values (for example, a weak secret key in production).
4. Support an environment flag (local, test, staging, production) and change behavior only through configuration, never `if env == ...` branches in business code.
5. Cache the settings object, and inject it through a dependency so tests can override it.

**Check:** deleting a required variable makes startup fail with a clear message.

### Step 5: The app factory
1. Build the app inside a **factory function** rather than at import time, so tests can create isolated instances.
2. Use the **lifespan** mechanism to open and close shared resources (database engine, HTTP clients, Redis) once.
3. Register, in this order: middleware, exception handlers, then the versioned router.
4. Disable interactive docs in production, or protect them.

**Check:** two app instances can exist in one test run without sharing state.

## Phase 2: The data and layering core

### Step 6: Database layer
1. Create the async engine and a **session factory** with `expire_on_commit` turned off, so returned objects stay usable.
2. Provide one session per request through a dependency that opens it, yields it, and always closes it.
3. Define a base model with shared columns: an ID, created and updated timestamps (timezone-aware, set by the database), and optionally a soft-delete flag.
4. Set **naming conventions** for constraints and indexes so migrations are deterministic.
5. Set up **Alembic** with async support, autogenerate on, and a rule that every schema change ships as a reviewed migration. Never create tables at startup outside local experiments.
6. Add indexes on every foreign key and every column you filter or sort by.

**Check:** you can create a database from scratch by running migrations only.

### Step 7: Define the transaction boundary
Decide this explicitly, because scattered commits cause subtle bugs:
- **One request equals one transaction.** The service layer decides when to commit. Repositories never commit.
- For operations that span several repositories, use a **unit of work**: a small object that holds the session and exposes the repositories.
- Keep transactions short. Never call slow external services while holding a transaction open.

**Check:** a failure halfway through a multi-step operation leaves no partial data.

### Step 8: Build the first module as the template
Pick `users` and build it fully, because every other module copies this pattern:
1. **Models:** the database entity only.
2. **Schemas:** separate Create, Update (all optional), Read, and internal variants. **Never return a database model from an endpoint**, and never accept fields like role, ID, or owner from the client.
3. **Repository:** one class per aggregate with get, list, create, update, and delete. It returns domain objects, hides query details, and handles eager loading to avoid N+1 queries.
4. **Service:** all business rules (uniqueness, state transitions, permission-sensitive logic). It raises **domain exceptions**, such as "user not found" or "email already used", never HTTP exceptions.
5. **Router:** thin. Validate input through the schema, call a service, and return a response model. No business logic, no queries.
6. **Dependencies:** wire the session to repository to service chain through the dependency system, so each layer receives its collaborators instead of creating them.

**Check:** you can swap the repository for an in-memory fake in a test without touching the service.

### Step 9: Consistent errors
1. Define a small **hierarchy of domain exceptions** (not found, conflict, validation, permission denied, rate limited).
2. Write **global exception handlers** that map each to an HTTP status and one standard error body: a machine-readable code, a human message, and a request ID.
3. Add a catch-all handler that logs the full detail and returns a generic message, so stack traces and internals never reach clients.
4. Make validation errors use the same body format.
5. Document error responses in the OpenAPI schema so generated frontend clients know about them.

**Check:** every failure, from a bad field to an unhandled crash, returns the same shape.

## Phase 3: Security

### Step 10: Authentication
1. Hash passwords with **Argon2**. Never store or log plain passwords.
2. Issue **short-lived access tokens** (minutes) and **rotating refresh tokens** (days). Store only a hash of each refresh token server-side, so you can revoke it and detect reuse.
3. For browser clients, deliver tokens in `HttpOnly`, `Secure`, `SameSite` cookies. For mobile or third-party clients, accept the `Authorization` header. Support both through one dependency.
4. Use a vetted JWT library with a pinned algorithm, validated expiry, issuer, and audience. Keep signing keys in a secret store and support key rotation.
5. Add email or phone verification, password reset with single-use expiring tokens, and generic responses that don't reveal whether an account exists.
6. Throttle login attempts per account and per IP, and consider temporary lockouts.

### Step 11: Authorization
1. Authentication answers "who are you", and authorization answers "may you do this to this object". The second is where most real breaches happen.
2. Start with **role-based access** (for example client, pro, admin), expressed as reusable dependencies.
3. Add **object-level checks** in the service layer: ownership and membership are verified for every read and write of a specific record.
4. Default to **deny**. A route with no explicit permission should be rejected by a test, not silently open.
5. Keep admin endpoints in a separate router with stricter dependencies.

### Step 12: Application hardening
Work through this list once, then keep it in your definition of done:
- **Input:** strict Pydantic validation with length limits, enums, and constrained types. Reject unknown fields on write schemas.
- **SQL injection:** use only the ORM or bound parameters, never string-built queries.
- **CORS:** an explicit allow-list of origins, never a wildcard together with credentials.
- **Security headers:** HSTS, `X-Content-Type-Options`, frame protection, a content security policy where HTML is served, and a restrictive referrer policy.
- **Rate limiting:** per IP and per user, backed by Redis, with stricter limits on auth endpoints.
- **Request limits:** maximum body size, upload size and type validation, and timeouts.
- **CSRF:** needed if you use cookie auth, so rely on `SameSite` plus an explicit token for state-changing requests when clients are cross-site.
- **Secrets:** environment or a secret manager only. Never commit them, log them, or return them. Run a secret scanner in CI.
- **Dependencies:** automated vulnerability scanning (pip-audit or similar) and scheduled updates.
- **Data protection:** TLS everywhere, encrypted backups, field-level encryption for particularly sensitive data, and minimal data retention.
- **Logging:** record security events (logins, failures, permission denials) and **never log tokens, passwords, or personal data**.
- **Containers:** non-root user, minimal base image, read-only filesystem where possible, and image scanning.

**Check:** run the OWASP API Security Top 10 as a checklist against your first module.

## Phase 4: Communication

### Step 13: API design contract
1. Version from day one (`/api/v1`) and promise not to break a version.
2. Use nouns for resources, correct HTTP methods and status codes, and **idempotency keys** for create operations that clients may retry.
3. Return flat objects for single resources, and wrap lists with items and pagination metadata. Prefer **cursor pagination** for large or fast-changing tables.
4. Support filtering and sorting through validated query parameters with an allow-list of sortable fields.
5. Give every operation a stable ID, tags, summaries, and documented error responses. This turns the OpenAPI spec into the contract for generated frontend SDKs.
6. Treat the exported spec as a versioned artifact: commit it, diff it in CI, and fail pull requests that introduce breaking changes.

### Step 14: Internal communication between layers and modules
1. Modules talk to each other **only through service interfaces**, never by reaching into another module's repository or models.
2. Use **protocols (interfaces)** for anything you may swap, such as the repository, email sender, payment provider, or storage. The service depends on the interface, and the concrete class is wired in at the edge.
3. For side effects ("user registered, so send a welcome email"), emit **domain events** handled in the background rather than calling the effect inline. Start with a simple in-process dispatcher and only graduate to a message broker when you need one.

### Step 15: External communication
1. Wrap every third-party system in an **adapter** inside `integrations`, so the rest of the app sees your interface, not their SDK.
2. Use one shared async HTTP client with timeouts, bounded retries with backoff, and circuit breaking for flaky services.
3. Verify and deduplicate **incoming webhooks** (signatures, replay protection, idempotent handling).
4. Run slow or retryable work (emails, SMS, reports, imports) in a **background worker** through a queue backed by Redis, with retries and a dead-letter path. Keep request handlers fast.

### Step 16: Real-time and streaming (when needed)
Add WebSockets or streaming responses as their own router. Authenticate the connection, enforce size and rate limits, handle disconnects cleanly, and make sure proxies are configured not to buffer.

## Phase 5: Quality and operations

### Step 17: Testing strategy
1. **Unit tests** for services using fake repositories, which is fast and covers the business rules.
2. **Integration tests** for repositories and routes against a **real PostgreSQL** (a container, not SQLite), with each test wrapped in a rolled-back transaction.
3. **Contract tests** that the exported OpenAPI spec matches the committed one.
4. **Security tests**: unauthenticated access is rejected, one user cannot read another's data, and expired or tampered tokens fail.
5. Use factories for test data, dependency overrides for auth and time, and pytest markers to separate fast and slow suites.
6. Set a coverage floor, but focus first on auth, permissions, money, and state transitions.

### Step 18: Observability
1. **Structured JSON logs** with a request ID propagated across layers, workers, and outbound calls.
2. Health endpoints: a cheap liveness check and a readiness check that verifies the database and cache.
3. **Sentry** (or similar) for errors, **OpenTelemetry** for traces, and metrics for latency, error rate, queue depth, and database pool use.
4. Audit logs for sensitive business actions, stored separately from application logs.

### Step 19: Performance basics
Use async drivers and never block the event loop. If you must call blocking code, run it in a thread pool. Add eager loading, indexes, and pagination limits. Cache with Redis only after measuring, and use connection pooling with sensible limits.

### Step 20: Containerization and CI/CD
1. A **multi-stage Dockerfile** with a slim runtime image and a non-root user.
2. A compose file for local development: app, PostgreSQL, Redis, and worker.
3. Production runs multiple Uvicorn workers behind a reverse proxy, with graceful shutdown.
4. A CI pipeline that runs, in order: lint, types, security scan, tests, migration check (the database matches the models), spec diff, and image build.
5. Deploy with migrations as a separate, controlled step. Use backward-compatible changes (add before remove) so you can roll back.

## Design principles: where each one lives

| Principle | How the structure enforces it |
|---|---|
| **Separation of concerns** | Router, service, and repository each have one job |
| **Single responsibility** | One module per feature, one class per purpose |
| **Dependency inversion** | Services depend on protocols, and concrete classes are injected |
| **Open/closed** | New features are new modules, not edits to old ones |
| **Interface segregation** | Small protocols per capability, such as an email sender and a file store |
| **Don't repeat yourself** | Shared pieces live in `common`, but only after the third repetition |
| **Fail fast** | Config validated at startup, input validated at the edge |
| **Least privilege** | Default-deny permissions, minimal database and container rights |
| **Explicit over implicit** | One transaction boundary, one error format, one place for wiring |
| **12-factor** | Config in the environment, stateless processes, logs to stdout |

## Build order summary
1. Tooling, repository, and folder layout (Steps 1 to 3)
2. Config and app factory (Steps 4 and 5)
3. Database, Alembic, and transaction rules (Steps 6 and 7)
4. `users` module as the template, then errors (Steps 8 and 9)
5. Authentication and authorization (Steps 10 and 11)
6. Hardening checklist (Step 12)
7. API contract and communication patterns (Steps 13 to 16)
8. Tests, observability, performance, and CI/CD (Steps 17 to 20)
9. Only then clone the template for each new feature module

## Common mistakes to avoid
- Starting with microservices, CQRS, or event sourcing before you have a real need.
- Letting routers talk to the database directly "just this once".
- Returning ORM objects or accepting client-supplied IDs and roles.
- Skipping migrations, tests, or the error format "to move fast". These are the hardest things to add later.
- Adding abstractions before the second use case. Keep the layering, but don't invent interfaces nobody swaps.

When you're ready for code, I can scaffold the project step by step, starting with Steps 1 to 5 (tooling, config, and app factory), then the `users` module as the template. Tell me whether you want Postgres-only or a Docker Compose setup with Redis from the start.