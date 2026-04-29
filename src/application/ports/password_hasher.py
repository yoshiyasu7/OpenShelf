"""Password hasher port."""

from typing import Protocol


class PasswordHasher(Protocol):
    """Abstract password hasher contract used by use cases."""

    def hash(self, password: str) -> str: ...

    def verify(self, password: str, password_hash: str) -> bool: ...
