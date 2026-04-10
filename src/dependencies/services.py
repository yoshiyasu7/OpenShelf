"""Service (Use Cases) layer dependencies."""

from typing import Annotated

from fastapi import Depends

from src.application.use_cases.auth_use_cases import AuthUseCases, ValidateAccessTokenUseCase
from src.dependencies.infrastructure import JWTDep, RefreshStoreDep, UserRepoDep  # noqa: TC001


def get_auth_service(
    jwt: JWTDep,
    user_repo: UserRepoDep,
    refresh_store: RefreshStoreDep,
) -> AuthUseCases:
    return AuthUseCases(
        user_repository=user_repo,
        jwt=jwt,
        refresh_store=refresh_store,
    )


def get_validate_token_service(
    jwt: JWTDep,
    user_repo: UserRepoDep,
) -> ValidateAccessTokenUseCase:
    return ValidateAccessTokenUseCase(jwt=jwt, user_repository=user_repo)


# --- PUBLIC TYPE ALIASES ---

AuthService = Annotated[AuthUseCases, Depends(get_auth_service)]
ValidateTokenService = Annotated[ValidateAccessTokenUseCase, Depends(get_validate_token_service)]
