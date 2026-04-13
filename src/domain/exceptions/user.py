"""User Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError, status


class UserNotFoundError(DomainError):
    """Exception raised when user not found."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "USER_NOT_FOUND"
    message = "User was not found"


class UserAlreadyExistsError(DomainError):
    """Exception raised when user already exists with username/email."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this username or email already exists"


class InvalidCredentialsError(DomainError):
    """Exception raised when user's credentials invalid."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid username or password"
