"""Base Domain-specific exception."""

import typing as t


class DomainException(Exception):
    """Base exception for domain-related errors."""

    def __init__(self, message: str, error_code: t.Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class ValidationError(DomainException):
    pass