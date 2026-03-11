"""Author Domain-specific exceptions."""

from src.domain.exceptions.base import DomainException


class AuthorNotFound(DomainException):
    """Exception raised when author not found."""
    pass

class AuthorAlreadyExists(DomainException):
    """Exception raised when author already exists with name."""
    pass
