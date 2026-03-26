from __future__ import annotations

from passlib.context import CryptContext


class PasswordHasher:
    """
    Password hashing/verification facade.

    Uses bcrypt via passlib to provide:
    - adaptive hashing,
    - safe verification,
    - future algorithm upgrades.
    """

    def __init__(self) -> None:
        self._ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._ctx.verify(password, password_hash)

