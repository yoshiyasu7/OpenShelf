"""Refresh session store port."""

from datetime import datetime  # noqa: TC003
from typing import Protocol
from uuid import UUID  # noqa: TC003


class RefreshSessionStore(Protocol):
    """Abstract refresh session store used by use cases."""

    async def create(
        self,
        *,
        user_id: UUID,
        refresh_token: str,
        expires_at: datetime,
    ) -> None: ...

    async def rotate(
        self,
        *,
        user_id: UUID,
        old_refresh_token: str,
        new_refresh_token: str,
        new_expires_at: datetime,
        now: datetime,
    ) -> None: ...

    async def revoke(self, *, refresh_token: str, now: datetime) -> None: ...
