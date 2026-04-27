"""Domain-specific exceptions."""

from fastapi import status


class DomainError(Exception):
    """Base exception for domain-related errors."""
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "DOMAIN_ERROR"
    message: str = "An unexpected domain error occurred"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class ValidationError(DomainError):
    pass
