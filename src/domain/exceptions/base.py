"""Domain-specific exceptions."""


class DomainError(Exception):
    """Base exception for domain-related errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ValidationError(DomainError):
    pass
