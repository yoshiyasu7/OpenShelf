"""Service (Use Cases) layer dependencies."""

from typing import Annotated

from fastapi import Depends

from src.application.use_cases.auth_use_cases import AuthUseCases, ValidateAccessTokenUseCase
from src.application.use_cases.author_use_cases import AuthorUseCases
from src.application.use_cases.book_use_cases import BookUseCases
from src.application.use_cases.user_use_cases import UserUseCases
from src.dependencies.infrastructure import (  # noqa: TC001
    AuthorRepoDep,
    BookRepoDep,
    JWTDep,
    RefreshStoreDep,
    UserRepoDep,
)


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


def get_author_service(author_repo: AuthorRepoDep) -> AuthorUseCases:
    return AuthorUseCases(author_repository=author_repo)


def get_user_service(user_repo: UserRepoDep) -> UserUseCases:
    return UserUseCases(user_repository=user_repo)


def get_book_service(
    book_repo: BookRepoDep,
    user_repo: UserRepoDep,
    author_repo: AuthorRepoDep,
) -> BookUseCases:
    return BookUseCases(
        book_repository=book_repo,
        user_repository=user_repo,
        author_repository=author_repo,
    )


def get_validate_token_service(
    jwt: JWTDep,
    user_repo: UserRepoDep,
) -> ValidateAccessTokenUseCase:
    return ValidateAccessTokenUseCase(jwt=jwt, user_repository=user_repo)


# --- PUBLIC TYPE ALIASES ---

AuthService = Annotated[AuthUseCases, Depends(get_auth_service)]
AuthorService = Annotated[AuthorUseCases, Depends(get_author_service)]
BookService = Annotated[BookUseCases, Depends(get_book_service)]
UserService = Annotated[UserUseCases, Depends(get_user_service)]
ValidateTokenService = Annotated[ValidateAccessTokenUseCase, Depends(get_validate_token_service)]
