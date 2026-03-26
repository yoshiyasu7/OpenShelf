from fastapi import APIRouter

from src.interfaces.api.v1.auth.main import router as auth_router


api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(auth_router)
