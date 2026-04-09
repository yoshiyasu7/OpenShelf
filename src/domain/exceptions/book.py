"""Book Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError


class BookNotFoundError(DomainError):
    """Exception raised when book is not found."""
    pass

class BookAlreadyExistsError(DomainError):
    """Exception raised when book already exists with title."""
    pass

class InvalidPublicationDateError(DomainError):
    """Exception raised when book has invalid publication date."""
    pass
