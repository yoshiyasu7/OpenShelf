"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for domain-related errors."""

    error_code: str = "DOMAIN_ERROR"
    message: str = "An unexpected domain error occurred"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        super().__init__(self.message)


class ValidationError(DomainError):
    """Raised when domain input does not satisfy business rules."""


class NotFoundError(DomainError):
    """Raised when a domain resource does not exist."""


class ConflictError(DomainError):
    """Raised when the requested change conflicts with current state."""


class AuthenticationError(DomainError):
    """Raised when credentials or authentication tokens are invalid."""


class PermissionDeniedError(DomainError):
    """Raised when a domain policy forbids the action."""


class BadRequestError(DomainError):
    """Raised when the requested domain operation is malformed."""
