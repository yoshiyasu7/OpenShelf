"""Book Domain-specific exceptions."""

from src.domain.exceptions.base import ConflictError, NotFoundError, ValidationError


class BookNotFoundError(NotFoundError):
    """Exception raised when book is not found."""

    error_code = "BOOK_NOT_FOUND"
    message = "The requested book was not found"


class BookAlreadyExistsError(ConflictError):
    """Exception raised when book already exists with title."""

    error_code = "BOOK_ALREADY_EXISTS"
    message = "A book with this title already exists"


class InvalidPublicationDateError(ValidationError):
    """Exception raised when book has invalid publication date."""

    error_code = "INVALID_BOOK_PUBLICATION_DATE"
    message = "The publication date cannot be in the future or earlier than 1440"
