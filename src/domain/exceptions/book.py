"""Book Domain-specific exceptions."""

from src.domain.exceptions.base import DomainException


class BookNotFound(DomainException):
    """Exception raised when book is not found."""
    pass

class BookAlreadyExists(DomainException):
    """Exception raised when book already exists with title."""
    pass

class InvalidPublicationDate(DomainException):
    """Exception raised when book has invalid publication date."""
    pass
