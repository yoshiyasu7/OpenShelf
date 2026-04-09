"""User Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError


class UserNotFoundError(DomainError):
    """Exception raised when user not found."""
    pass

class UserAlreadyExistsError(DomainError):
    """Exception raised when user already exists with username/email."""
    pass

class InvalidCredentialsError(DomainError):
    """Exception raised when user's credentials invalid."""
    pass
