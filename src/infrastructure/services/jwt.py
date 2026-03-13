"""JWT token service for authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from src.infrastructure.settings.main import JWTSettings


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenDecodeError(Exception):
    """JWT decoding or cryptographic verification failed."""


class TokenValidationError(Exception):
    """JWT payload validation failed."""


class TokenPayload(BaseModel):
    """JWT payload model."""

    sub: UUID
    type: TokenType
    exp: int
    iat: int


class JWTService:
    """Service for creating and verifying JWT tokens."""

    def __init__(self, settings: JWTSettings) -> None:
        self.settings = settings

    # --- Public API ---

    def create_access_token(self, subject: UUID) -> str:
        """Create access token for the given subject (user_id as UUID)."""
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        return self._create_token(
            subject=subject,
            token_type=TokenType.ACCESS,
            expires_delta=expires_delta,
        )

    def create_refresh_token(self, subject: UUID) -> str:
        """Create refresh token for the given subject (user_id as UUID)."""
        expires_delta = timedelta(days=self.settings.refresh_token_expire_days)
        return self._create_token(
            subject=subject,
            token_type=TokenType.REFRESH,
            expires_delta=expires_delta,
        )

    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify access token and return validated payload."""
        return self._verify_token(token, expected_type=TokenType.ACCESS)

    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify refresh token and return validated payload."""
        return self._verify_token(token, expected_type=TokenType.REFRESH)

    # --- Internal methods ---

    def _create_token(
        self,
        *,
        subject: UUID,
        token_type: TokenType,
        expires_delta: timedelta,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload: Dict[str, Any] = {
            "sub": str(subject),
            "type": token_type.value,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        token = jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.algorithm,
        )
        return token

    def _decode_raw(self, token: str) -> Dict[str, Any]:
        """Decode JWT without business-level validation."""
        try:
            decoded = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
            )
        except JWTError as exc:
            raise TokenDecodeError("Failed to decode or verify JWT.") from exc
        return decoded

    def _verify_token(self, token: str, *, expected_type: TokenType) -> TokenPayload:
        """Decode, validate and type-check a JWT token."""
        decoded = self._decode_raw(token)

        try:
            payload = TokenPayload.model_validate(decoded)
        except ValidationError as exc:
            raise TokenValidationError("Invalid JWT payload structure.") from exc

        if payload.type is not expected_type:
            raise TokenValidationError(
                f"Unexpected token type: {payload.type}, expected: {expected_type}."
            )

        return payload