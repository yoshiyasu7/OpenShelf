from fastapi import APIRouter

from src.interfaces.api.v1.auth.main import router as auth_router
from src.interfaces.api.v1.author.main import router as author_router
from src.interfaces.api.v1.book.main import router as book_router
from src.interfaces.api.v1.user.main import router as user_router

api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(author_router)
api_v1_router.include_router(book_router)
