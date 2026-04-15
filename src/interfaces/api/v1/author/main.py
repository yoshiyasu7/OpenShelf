from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, status

from src.application.dtos.author.main import (
    AuthorResponse,
    AuthorsListResponse,
    CreateAuthorRequest,
    UpdateAuthorRequest,
)
from src.application.dtos.main import QueryFilterParamsDep  # noqa: TC001
from src.dependencies import AdminUserDep, AuthorService, CurrentUserDep  # noqa: TC001

router = APIRouter(
    tags=["Authors"],
    prefix="/authors",
)


@router.post("/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    _admin: AdminUserDep,
    payload: CreateAuthorRequest,
    uc: AuthorService
) -> AuthorResponse:
    author = await uc.create_author(payload=payload)
    return AuthorResponse.model_validate(author)


@router.get("/", response_model=AuthorsListResponse)
async def get_authors_list(
    _current_user: CurrentUserDep,
    filters: QueryFilterParamsDep,
    uc: AuthorService
) -> AuthorsListResponse:
    authors_list = await uc.get_authors_list(filters=filters)
    return AuthorsListResponse.model_validate(authors_list)


@router.get("/{author_id}", response_model=AuthorResponse)
async def get_author(
    _current_user: CurrentUserDep,
    author_id: UUID,
    uc: AuthorService
) -> AuthorResponse:
    author = await uc.get_author(author_id=author_id)
    return AuthorResponse.model_validate(author)


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author(
    _admin: AdminUserDep,
    author_id: UUID,
    payload: UpdateAuthorRequest,
    uc: AuthorService
) -> AuthorResponse:
    author = await uc.update_author(author_id=author_id, payload=payload)
    return AuthorResponse.model_validate(author)


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_author(
    _admin: AdminUserDep,
    author_id: UUID,
    uc: AuthorService
) -> None:
    await uc.delete_author(author_id=author_id)
