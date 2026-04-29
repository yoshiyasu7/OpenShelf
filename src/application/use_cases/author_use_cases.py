from typing import TYPE_CHECKING

from src.application.dtos.main import PaginatedResult
from src.domain.exceptions.author import AuthorAlreadyExistsError, AuthorNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.dtos.author.main import CreateAuthorRequest, UpdateAuthorRequest
    from src.application.dtos.main import QueryFilterParams
    from src.domain.entities import Author
    from src.domain.repositories.author.main import AuthorRepository


class AuthorUseCases:
    """
    Core logic for managing authors.

    Notes:
    - Performs explicit conflict checks by normalized author name.
    - Uses paginated reads to keep list endpoints scalable.
    """

    def __init__(self, *, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def create_author(self, *, payload: CreateAuthorRequest) -> Author:
        create_data = payload.model_dump()
        if await self._author_repository.exists_by_name(name=create_data["name"]):
            raise AuthorAlreadyExistsError()
        return await self._author_repository.create(data=create_data)

    async def get_author(self, *, author_id: UUID) -> Author:
        author = await self._author_repository.get_by_id(author_id=author_id)
        if not author:
            raise AuthorNotFoundError(f"Author with id {author_id} not found")
        return author

    async def get_authors_list(self, *, filters: QueryFilterParams) -> PaginatedResult[Author]:
        items, total = await self._author_repository.list_paginated(
            limit=filters.limit,
            offset=filters.offset,
            name_query=filters.name_query,
        )
        return PaginatedResult(items=items, total=total, limit=filters.limit, offset=filters.offset)

    async def update_author(self, *, author_id: UUID, payload: UpdateAuthorRequest) -> Author:
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get_author(author_id=author_id)

        new_name = update_data.get("name")
        if new_name and await self._author_repository.exists_by_name(name=new_name, exclude_author_id=author_id):
            raise AuthorAlreadyExistsError()

        author = await self._author_repository.update(author_id=author_id, data=update_data)
        if not author:
            raise AuthorNotFoundError(f"Author with id {author_id} not found")
        return author

    async def delete_author(self, *, author_id: UUID) -> None:
        deleted = await self._author_repository.delete(author_id=author_id)
        if not deleted:
            raise AuthorNotFoundError(f"Author with id {author_id} not found")
