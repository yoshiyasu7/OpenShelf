"""BookLoan Domain-specific exceptions."""

from src.domain.exceptions.base import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)


class LoanNotFoundError(NotFoundError):
    """Exception raised when book loan not found."""

    error_code = "LOAN_NOT_FOUND"
    message = "The book loan record was not found"


class LoanLimitExceededError(ValidationError):
    """Exception raised when book loan out of limit for user."""

    error_code = "LOAN_LIMIT_EXCEEDED"
    message = "You have reached the maximum number of books allowed for loan"


class NoAvailableInstancesError(ConflictError):
    """Exception raised when book has no available instances."""

    error_code = "NO_AVAILABLE_INSTANCES"
    message = "All copies of this book are currently on loan"


class AlreadyReturnedError(BadRequestError):
    """Exception raised when instance of book already returned."""

    error_code = "LOAN_ALREADY_RETURNED"
    message = "This book has already been returned"


class LoanOverdueError(PermissionDeniedError):
    """Exception raised when loan is overdue for user."""

    error_code = "LOAN_OVERDUE"
    message = "New loans are blocked due to overdue books"


class ConcurrencyConflictError(ConflictError):
    """Exception raised when the copies of the book have run out."""

    error_code = "CONCURRENCY_CONFLICT"
    message = "The book was just taken by another user. Please try again"


class AlreadyBorrowingBookError(ConflictError):
    """User already has an unreturned loan for this book."""

    error_code = "ALREADY_BORROWING_BOOK"
    message = "You already have a copy of this book on loan"
