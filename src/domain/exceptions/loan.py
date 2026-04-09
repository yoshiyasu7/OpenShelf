"""BookLoan Domain-specific exceptions."""

from src.domain.exceptions.base import DomainError


class LoanNotFoundError(DomainError):
    """Exception raised when book loan not found."""
    pass

class LoanLimitExceededError(DomainError):
    """Exception raised when book loan out of limit for user."""
    pass

class NoAvailableInstancesError(DomainError):
    """Exception raised when book has no available instances."""
    pass

class AlreadyReturnedError(DomainError):
    """Exception raised when instance of book already returned."""
    pass

class LoanOverdueError(DomainError):
    """Exception raised when loan is overdue for user."""
    pass

class ConcurrencyConflictError(DomainError):
    """Exception raised when the copies of the book have run outid."""
    pass
