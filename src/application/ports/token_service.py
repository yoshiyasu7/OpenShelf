"""Token service port (abstraction over JWT/provider-specific implementation)."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID


class TokenDecodeError(Exception):
    """Token decoding or cryptographic verification failed."""


class TokenValidationError(Exception):
    """Token payload validation failed."""


class AccessTokenPayload(Protocol):
    """Minimal access-token payload contract consumed by use cases."""

    sub: UUID


class TokenService(Protocol):
    """Abstract token service contract used by use cases."""

    def create_access_token(self, subject: UUID) -> str: ...

    def create_refresh_token(self, subject: UUID) -> str: ...

    def verify_access_token(self, token: str) -> AccessTokenPayload: ...

    def verify_refresh_token(self, token: str) -> AccessTokenPayload: ...
