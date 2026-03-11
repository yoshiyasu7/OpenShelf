"""BookLoan Domain-specific exceptions."""

from src.domain.exceptions.base import DomainException


class LoanNotFound(DomainException):
    """Exception raised when book loan not found."""
    pass

class LoanLimitExceeded(DomainException):
    """Exception raised when book loan out of limit for user."""
    pass

class NoAvailableInstances(DomainException):
    """Exception raised when book has no available instances."""
    pass

class AlreadyReturned(DomainException):
    """Exception raised when instance of book already returned."""
    pass

class LoanOverdue(DomainException):
    """Exception raised when loan is overdue for user."""
    pass

class ConcurrencyConflict(DomainException):
    """Exception raised when the copies of the book have run outid."""
    pass