"""FastAPI router for authentication."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_session
from src.app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# Bearer token security scheme so Swagger/OpenAPI docs surface an "Authorize"
# button and show a lock icon on protected endpoints.
bearer_scheme = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User profile response."""
    id: UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


async def get_auth_service(session: Annotated[AsyncSession, Depends(get_session)]) -> AuthService:
    """Dependency for AuthService."""
    return AuthService(session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user account."""
    user = await service.register(email=body.email, password=body.password)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate user and return JWT access token."""
    token = await service.authenticate(email=body.email, password=body.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[str | None, Depends(bearer_scheme)],
) -> UserResponse:
    """Get currently authenticated user profile."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await service.get_user_by_token(credentials.credentials)
    return UserResponse.model_validate(user)
