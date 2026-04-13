"""Author Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError, status


class AuthorNotFoundError(DomainError):
    """Exception raised when author not found."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "AUTHOR_NOT_FOUND"
    message = "The requested author was not found"


class AuthorAlreadyExistsError(DomainError):
    """Exception raised when author already exists with name."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "AUTHOR_ALREADY_EXISTS"
    message = "An author with this name already exists"
