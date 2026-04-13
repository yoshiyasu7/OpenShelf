"""Book Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError, status


class BookNotFoundError(DomainError):
    """Exception raised when book is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "BOOK_NOT_FOUND"
    message = "The requested book was not found"


class BookAlreadyExistsError(DomainError):
    """Exception raised when book already exists with title."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "BOOK_ALREADY_EXISTS"
    message = "A book with this title already exists"


class InvalidPublicationDateError(DomainError):
    """Exception raised when book has invalid publication date."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "INVALID_BOOK_PUBLICATION_DATE"
    message = "The publication date cannot be in the future or earlier than 1440"
