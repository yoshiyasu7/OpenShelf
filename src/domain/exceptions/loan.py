"""BookLoan Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError, status


class LoanNotFoundError(DomainError):
    """Exception raised when book loan not found."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "LOAN_NOT_FOUND"
    message = "The book loan record was not found"


class LoanLimitExceededError(DomainError):
    """Exception raised when book loan out of limit for user."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "LOAN_LIMIT_EXCEEDED"
    message = "You have reached the maximum number of books allowed for loan"


class NoAvailableInstancesError(DomainError):
    """Exception raised when book has no available instances."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "NO_AVAILABLE_INSTANCES"
    message = "All copies of this book are currently on loan"


class AlreadyReturnedError(DomainError):
    """Exception raised when instance of book already returned."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "LOAN_ALREADY_RETURNED"
    message = "This book has already been returned"


class LoanOverdueError(DomainError):
    """Exception raised when loan is overdue for user."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "LOAN_OVERDUE"
    message = "New loans are blocked due to overdue books"


class ConcurrencyConflictError(DomainError):
    """Exception raised when the copies of the book have run outid."""
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONCURRENCY_CONFLICT"
    message = "The book was just taken by another user. Please try again"
