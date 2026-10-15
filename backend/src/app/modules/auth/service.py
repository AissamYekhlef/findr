"""Simplified authentication service."""

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.exceptions import ConflictError, NotFoundError, ValidationError as DomainValidationError
from src.app.modules.auth.models import UserModel


class AuthService:
    """Service handling user registration, authentication, and JWT tokens."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async database session."""
        self.session = session
        self.ph = PasswordHasher()

    async def register(self, email: str, password: str) -> dict[str, Any]:
        """Register a new user."""
        email = email.strip().lower()

        # Check if user already exists
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError(f"User with email '{email}' already exists")

        # Hash password using Argon2id
        try:
            password_hash = self.ph.hash(password)
        except Exception as e:
            raise DomainValidationError(f"Password hashing failed: {e}")

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        user = UserModel(
            id=user_id,
            email=email,
            password_hash=password_hash,
            created_at=now,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
        }

    async def authenticate(self, email: str, password: str) -> str:
        """Authenticate user credentials and return a signed JWT access token."""
        email = email.strip().lower()

        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        # print("authenticate", user.password_hash)
        if not user:
            raise NotFoundError("Invalid email or password")

        try:
            self.ph.verify(user.password_hash, password)
        except VerifyMismatchError:
            raise NotFoundError("Invalid email or password")

        # Create JWT access token
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
        }
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt

    async def get_user_by_token(self, token: str) -> dict[str, Any]:
        """Decode token and retrieve user details."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id_str: str = payload.get("sub")
            if not user_id_str:
                raise NotFoundError("Invalid authentication credentials")
            user_id = UUID(user_id_str)
        except (JWTError, ValueError):
            raise NotFoundError("Could not validate credentials")

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at,
            "user": user
        }
