# Findr — Data Explorer

A web app for working with tabular data stored in files. Open CSV, TSV, or Excel files directly in the browser, browse and edit data with confidence, and save changes back to the original file without losing data or introducing corruption.

**Status:** MVP v0.1 - Foundation Setup Complete

## Quick Start

### Requirements

- Python 3.12+
- Node.js 20 LTS+
- Docker & Docker Compose (for PostgreSQL)

### Setup (5 minutes)

```bash
# Clone repository
git clone <repo-url>
cd findr

# Backend: Install dependencies
cd backend && make install && cd ..

# Frontend: Install dependencies
cd frontend && npm install && cd ..

# Start services (PostgreSQL + API)
docker compose up -d

# Run backend (terminal 1)
cd backend && make run

# Run frontend (terminal 2)
cd frontend && npm run dev
```

Visit:
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Stop Services

```bash
docker compose down
```

## Commands

### Backend

```bash
cd backend

make install          # Install dependencies with uv
make run             # Start FastAPI server (localhost:8000)
make lint            # Run ruff linter and formatter
make type-check      # Run mypy type checker
make test            # Run pytest test suite
make migrate         # Run Alembic database migrations
make clean           # Remove cache and build artifacts
```

### Frontend

```bash
cd frontend

npm run dev          # Start dev server (localhost:3000)
npm run build        # Build for production
npm run lint         # Lint and format
npm run type-check   # TypeScript type checking
```

### Docker

```bash
docker compose up -d     # Start services
docker compose down      # Stop services
docker compose logs -f   # View service logs
```

## Architecture

### Project Structure

```
findr/                          ← Project root
├── backend/                     ← FastAPI backend
│   ├── src/app/                (application code)
│   ├── tests/                  (test suite)
│   ├── migrations/             (Alembic migrations)
│   ├── pyproject.toml
│   ├── Makefile
│   ├── Dockerfile
│   ├── .env.example
│   └── .pre-commit-config.yaml
├── frontend/                    ← Nuxt frontend
│   ├── pages/                  (routes)
│   ├── stores/                 (Pinia state)
│   ├── composables/            (Vue composables)
│   ├── assets/                 (CSS tokens, images)
│   ├── package.json
│   ├── nuxt.config.ts
│   └── tsconfig.json
├── docker-compose.yml          ← Local dev environment
├── .github/workflows/          ← CI/CD pipelines
├── docs/                       ← Architecture docs
├── specs/                      ← Product & tech specs
└── README.md                   ← This file
```

### Key Technologies

**Backend:**
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- asyncpg for PostgreSQL
- Pydantic for validation
- Alembic for migrations

**Frontend:**
- Nuxt 4 (Vue 3 + TypeScript)
- Pinia for state management
- CSS design tokens (no UI framework)

**Infrastructure:**
- PostgreSQL 15
- Docker & Docker Compose
- GitHub Actions (CI/CD)

### Architecture Decisions

See `docs/decisions.md` for:
- Why async end-to-end (FastAPI + asyncpg)
- One transaction per request pattern
- Modular monolith over microservices
- Custom components over UI libraries

## Development Workflow

1. **Create a feature branch:** `git checkout -b feature/your-feature`
2. **Make changes:** Edit code in `src/app/` or `frontend/`
3. **Test locally:** `make test` (backend) or `npm run type-check` (frontend)
4. **Lint:** `make lint` (backend) or `npm run lint` (frontend)
5. **Commit:** `git commit -m "feat: your feature"`
6. **Push:** `git push origin feature/your-feature`
7. **Open PR:** CI runs automatically; all checks must pass

## Testing

### Backend

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_health.py -v

# Run with coverage
make test
# View HTML report: open htmlcov/index.html
```

### Frontend

```bash
cd frontend
npm run type-check    # TypeScript checks
npm run lint          # ESLint and Prettier
```

## Deployment

### Local Docker

```bash
make docker-up        # Starts PostgreSQL + API
```

### Production (Future)

See `docs/deployment.md` for cloud deployment (AWS/GCP/Azure).

## Contributing

- Follow the architecture in `docs/decisions.md`
- Write tests for new features
- Keep commits focused and descriptive
- Ensure all CI checks pass before merging

## Support

For issues or questions, open a GitHub issue or contact the team.

## License

MIT
