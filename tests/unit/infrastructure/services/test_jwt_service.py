from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from src.infrastructure.services.jwt import JWTService, TokenDecodeError, TokenType, TokenValidationError
from src.infrastructure.settings.main import JWTSettings


def make_service() -> JWTService:
    return JWTService(
        settings=JWTSettings(
            secret_key="secret",
            algorithm="HS256",
            access_token_expire_minutes=15,
            refresh_token_expire_days=7,
        )
    )


def test_create_and_verify_access_token() -> None:
    service = make_service()
    user_id = uuid4()

    token = service.create_access_token(user_id)
    payload = service.verify_access_token(token)

    assert payload.sub == user_id
    assert payload.type is TokenType.ACCESS


def test_create_and_verify_refresh_token() -> None:
    service = make_service()
    user_id = uuid4()

    token = service.create_refresh_token(user_id)
    payload = service.verify_refresh_token(token)

    assert payload.sub == user_id
    assert payload.type is TokenType.REFRESH


def test_verify_raises_decode_error_for_invalid_token() -> None:
    service = make_service()

    with pytest.raises(TokenDecodeError):
        service.verify_access_token("not-a-jwt")


def test_verify_raises_validation_error_for_invalid_payload() -> None:
    service = make_service()
    now = datetime.now(UTC)
    bad_token = jwt.encode(
        {
            "sub": "not-uuid",
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        service.settings.secret_key,
        algorithm=service.settings.algorithm,
    )

    with pytest.raises(TokenValidationError):
        service.verify_access_token(bad_token)


def test_verify_raises_validation_error_for_wrong_token_type() -> None:
    service = make_service()
    token = service.create_refresh_token(uuid4())

    with pytest.raises(TokenValidationError):
        service.verify_access_token(token)
