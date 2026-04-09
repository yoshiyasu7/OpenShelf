"""Author Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError


class AuthorNotFoundError(DomainError):
    """Exception raised when author not found."""
    pass

class AuthorAlreadyExistsError(DomainError):
    """Exception raised when author already exists with name."""
    pass
