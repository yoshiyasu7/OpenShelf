from fastapi import APIRouter, HTTPException, status

from src.application.dtos.auth.main import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.application.dtos.user.main import UserPublic
from src.dependencies import AuthService  # noqa: TC001
from src.domain.exceptions.user import InvalidCredentialsError, UserNotFoundError

router = APIRouter(tags=["Authentication"])


@router.post(
    "/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: RegisterRequest,
    uc: AuthService,
) -> RegisterResponse:
    user = await uc.register(username=payload.username, email=payload.email, password=payload.password)
    return RegisterResponse(user=UserPublic.model_validate(user))


@router.post("/auth/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    uc: AuthService,
) -> TokenResponse:
    try:
        result = await uc.login(identifier=payload.identifier, password=payload.password)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=UserPublic.model_validate(result.user),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    uc: AuthService,
) -> TokenResponse:
    try:
        result = await uc.refresh(refresh_token=payload.refresh_token)
        return TokenResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            user=UserPublic.model_validate(result.user),
        )
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    uc: AuthService,
) -> None:
    try:
        await uc.logout(refresh_token=payload.refresh_token)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
