from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.auth_use_cases import AuthUseCases
from src.application.dtos.auth.main import (
    RegisterRequest, LoginRequest,
    RefreshRequest, RegisterResponse, TokenResponse,
)
from src.application.mappers.user import user_to_public_dto
from src.domain.exceptions.user import InvalidCredentials, UserAlreadyExists, UserNotFound
from src.interfaces.api.dependencies import get_auth_use_cases

router = APIRouter(tags=["Authentication"])


@router.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: RegisterRequest,
    uc: AuthUseCases = Depends(get_auth_use_cases),
) -> RegisterResponse:
    try:
        user = await uc.register(username=payload.username, email=payload.email, password=payload.password)
        return RegisterResponse(user=user_to_public_dto(user))
    except UserAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/auth/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    uc: AuthUseCases = Depends(get_auth_use_cases),
) -> TokenResponse:
    try:
        result = await uc.login(identifier=payload.identifier, password=payload.password)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=user_to_public_dto(result.user),
        )
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    uc: AuthUseCases = Depends(get_auth_use_cases),
) -> TokenResponse:
    try:
        result = await uc.refresh(refresh_token=payload.refresh_token)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=user_to_public_dto(result.user),
        )
    except (InvalidCredentials, UserNotFound) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    uc: AuthUseCases = Depends(get_auth_use_cases),
) -> None:
    try:
        await uc.logout(refresh_token=payload.refresh_token)
    except InvalidCredentials as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
