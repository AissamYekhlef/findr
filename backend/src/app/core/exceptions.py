"""Domain exceptions for Findr application."""


class DomainException(Exception):
    """Base exception for all domain errors."""

    pass


class NotFoundError(DomainException):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(DomainException):
    """Raised when input validation fails."""

    pass


class ConflictError(DomainException):
    """Raised when an operation conflicts with existing data."""

    pass


class PermissionDenied(DomainException):
    """Raised when user lacks permission for an operation."""

    pass


class RateLimited(DomainException):
    """Raised when rate limit is exceeded."""

    pass
