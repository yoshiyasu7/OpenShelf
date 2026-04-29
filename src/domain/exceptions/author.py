"""Author Domain-specific exceptions."""

from src.domain.exceptions.base import ConflictError, NotFoundError


class AuthorNotFoundError(NotFoundError):
    """Exception raised when author not found."""

    error_code = "AUTHOR_NOT_FOUND"
    message = "The requested author was not found"


class AuthorAlreadyExistsError(ConflictError):
    """Exception raised when author already exists with name."""

    error_code = "AUTHOR_ALREADY_EXISTS"
    message = "An author with this name already exists"
