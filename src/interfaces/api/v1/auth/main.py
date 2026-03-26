from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.auth_use_cases import AuthUseCases
from src.domain.exceptions.user import InvalidCredentials, UserAlreadyExists, UserNotFound
from src.infrastructure.services.jwt import JWTService
from src.application.dtos.user import (
    UserPublic, RegisterRequest, LoginRequest,
    RefreshRequest, RegisterResponse, TokenResponse,
)
from src.interfaces.api.dependencies import (
    get_jwt_service,
    get_transactional_session,
)


router = APIRouter(tags=["auth"])


def _public_user(u) -> UserPublic:
    return UserPublic(id=u.id, username=u.username, email=u.email, is_admin=u.is_admin)


@router.post(
    "/users/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_transactional_session),
    jwt: JWTService = Depends(get_jwt_service),
) -> RegisterResponse:
    try:
        uc = AuthUseCases(session=session, jwt=jwt)
        user = await uc.register(username=payload.username, email=payload.email, password=payload.password)
        return RegisterResponse(user=_public_user(user))
    except UserAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/users/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_transactional_session),
    jwt: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    try:
        uc = AuthUseCases(session=session, jwt=jwt)
        result = await uc.login(identifier=payload.identifier, password=payload.password)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=_public_user(result.user),
        )
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc


@router.post("/users/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_transactional_session),
    jwt: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    try:
        uc = AuthUseCases(session=session, jwt=jwt)
        result = await uc.refresh(refresh_token=payload.refresh_token)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=_public_user(result.user),
        )
    except (InvalidCredentials, UserNotFound) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc


@router.post("/users/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_transactional_session),
    jwt: JWTService = Depends(get_jwt_service),
) -> None:
    uc = AuthUseCases(session=session, jwt=jwt)
    await uc.logout(refresh_token=payload.refresh_token)
    return None

