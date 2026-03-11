"""User Domain-specific exceptions."""

from src.domain.exceptions.base import DomainException


class AuthorizationException(DomainException):
    """Exception raised when authorization fails."""
    pass

class UserNotFound(DomainException):
    """Exception raised when user not found."""
    pass

class UserAlreadyExists(DomainException):
    """Exception raised when user already exists with username/email."""
    pass

class InvalidCredentials(DomainException):
    """Exception raised when user's credentials invalid."""
    pass
