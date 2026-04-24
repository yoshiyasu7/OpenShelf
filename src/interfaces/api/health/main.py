import os
import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.infrastructure.database.provider import get_db_manager

APP_STARTED_AT = time.monotonic()

router = APIRouter(tags=["Health"], prefix="/health")


class AppLoad(BaseModel):
    status: str = "up"
    uptime_seconds: float = Field(..., ge=0)
    cpu_count: int = Field(..., ge=1)
    load_avg_1m: float | None = Field(default=None, ge=0)
    load_avg_5m: float | None = Field(default=None, ge=0)
    load_avg_15m: float | None = Field(default=None, ge=0)


class HealthResponse(BaseModel):
    status: str
    app: AppLoad
    db: dict[str, Any]


def _collect_app_load() -> AppLoad:
    load_averages: tuple[float, float, float] | None
    try:
        load_averages = os.getloadavg()
    except (AttributeError, OSError):
        load_averages = None

    return AppLoad(
        uptime_seconds=round(time.monotonic() - APP_STARTED_AT, 3),
        cpu_count=os.cpu_count() or 1,
        load_avg_1m=load_averages[0] if load_averages else None,
        load_avg_5m=load_averages[1] if load_averages else None,
        load_avg_15m=load_averages[2] if load_averages else None,
    )


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    db_health = await get_db_manager().health_check()
    app_health = _collect_app_load()

    return HealthResponse(
        status="up" if db_health.get("available") else "degraded",
        app=app_health,
        db=db_health,
    )


@router.get("/db", response_model=dict[str, Any])
async def db_health() -> dict[str, Any]:
    return await get_db_manager().health_check()
