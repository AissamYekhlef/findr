"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.app.core import (
    async_session_maker,
    close_db,
    get_session,
    init_db,
    settings,
)
from src.app.core.exceptions import (
    ConflictError,
    DomainException,
    NotFoundError,
    PermissionDenied,
    RateLimited,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage app lifecycle: startup and shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        None during app runtime.
    """
    # Startup
    print(f"Starting {settings.app_name} in {settings.environment} mode")
    await init_db()
    yield
    # Shutdown
    print("Shutting down database connections")
    await close_db()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        description="Data explorer for CSV, Excel, and database sources",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=404,
            content={
                "code": "NOT_FOUND",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=409,
            content={
                "code": "CONFLICT",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    @app.exception_handler(PermissionDenied)
    async def permission_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=403,
            content={
                "code": "PERMISSION_DENIED",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    @app.exception_handler(RateLimited)
    async def rate_limited_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=429,
            content={
                "code": "RATE_LIMITED",
                "message": str(exc),
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request, exc):  # type: ignore
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    # Health check endpoints
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        """Liveness check: app is running."""
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict:
        """Readiness check: app is ready to handle requests."""
        # Check database connection
        try:
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Database not ready: {str(e)}",
            )
        return {"status": "ready"}

    # Include routers
    from src.app.modules.sources.router import router as sources_router
    app.include_router(sources_router, prefix="/api/v1")

    return app


# Create app instance for uvicorn
app = create_app()
