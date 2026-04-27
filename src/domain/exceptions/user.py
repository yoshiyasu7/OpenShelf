"""User Domain-specific exceptions."""

from src.domain.exceptions.base import AuthenticationError, ConflictError, NotFoundError


class UserNotFoundError(NotFoundError):
    """Exception raised when user not found."""

    error_code = "USER_NOT_FOUND"
    message = "User was not found"


class UserAlreadyExistsError(ConflictError):
    """Exception raised when user already exists with username/email."""

    error_code = "USER_ALREADY_EXISTS"
    message = "User with this username or email already exists"


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when user's credentials invalid."""

    error_code = "INVALID_CREDENTIALS"
    message = "Invalid username or password"


class UsernameAlreadyTakenError(ConflictError):
    """Exception raised when the username is already taken."""

    error_code = "USERNAME_ALREADY_TAKEN"
    message = "This username is already taken"


class EmailAlreadyTakenError(ConflictError):
    """Exception raised when the email is already taken."""

    error_code = "EMAIL_ALREADY_TAKEN"
    message = "This email is already taken"
