from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, status

from src.application.dtos.book.main import (
    BookLoanResponse,
    BookResponse,
    BooksListResponse,
    CreateBookRequest,
    IssueBookResponse,
    ReturnBookResponse,
    UpdateBookRequest,
)
from src.application.dtos.main import QueryFilterParamsDep  # noqa: TC001
from src.dependencies import AdminUserDep, BookService, CurrentUserDep  # noqa: TC001

router = APIRouter(
    tags=["Books"],
    prefix="/books",
)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    _admin: AdminUserDep,
    payload: CreateBookRequest,
    uc: BookService
) -> BookResponse:
    book = await uc.create_book(payload=payload)
    return BookResponse.model_validate(book)


@router.get("/", response_model=BooksListResponse)
async def get_books_list(
    _current_user: CurrentUserDep,
    filters: QueryFilterParamsDep,
    uc: BookService
) -> BooksListResponse:
    books_list = await uc.get_books_list(filters=filters)
    return BooksListResponse.model_validate(books_list)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    _current_user: CurrentUserDep,
    book_id: UUID,
    uc: BookService
) -> BookResponse:
    book = await uc.get_book(book_id=book_id)
    return BookResponse.model_validate(book)


@router.post("/{book_id}/issue", response_model=IssueBookResponse, status_code=status.HTTP_201_CREATED)
async def issue_book(
    current_user: CurrentUserDep,
    book_id: UUID,
    uc: BookService
) -> IssueBookResponse:
    loan, available_instances = await uc.issue_book(user_id=current_user.id, book_id=book_id)
    return IssueBookResponse(
        loan=BookLoanResponse.model_validate(loan),
        available_instances=available_instances,
    )


@router.post("/loans/{loan_id}/return", response_model=ReturnBookResponse)
async def return_book(
    _current_user: CurrentUserDep,
    loan_id: UUID,
    uc: BookService
) -> ReturnBookResponse:
    loan, available_instances = await uc.return_book(loan_id=loan_id)
    return ReturnBookResponse(
        loan=BookLoanResponse.model_validate(loan),
        available_instances=available_instances,
    )


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    _admin: AdminUserDep,
    book_id: UUID,
    payload: UpdateBookRequest,
    uc: BookService
) -> BookResponse:
    book = await uc.update_book(book_id=book_id, payload=payload)
    return BookResponse.model_validate(book)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_book(
    _admin: AdminUserDep,
    book_id: UUID,
    uc: BookService
) -> None:
    await uc.delete_book(book_id=book_id)
