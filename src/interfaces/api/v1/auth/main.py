from fastapi import APIRouter, status

from src.application.dtos.auth.main import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from src.application.dtos.user.main import UserPublic
from src.dependencies import AuthService  # noqa: TC001

router = APIRouter(
    tags=["Authentication"],
    prefix="/auth",
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: RegisterRequest,
    uc: AuthService,
) -> RegisterResponse:
    user = await uc.register(username=payload.username, email=payload.email, password=payload.password)
    return RegisterResponse(user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    uc: AuthService,
) -> TokenResponse:
    result = await uc.login(identifier=payload.identifier, password=payload.password)
    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        user=UserPublic.model_validate(result.user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    uc: AuthService,
) -> TokenResponse:
    result = await uc.refresh(refresh_token=payload.refresh_token)
    return TokenResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        user=UserPublic.model_validate(result.user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    uc: AuthService,
) -> None:
    await uc.logout(refresh_token=payload.refresh_token)
