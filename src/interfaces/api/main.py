from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.infrastructure.database.provider import init_db_manager
from src.infrastructure.logging.config import configure_logging
from src.infrastructure.logging.middleware import (
    RequestContextMiddleware,
    exception_handler,
)
from src.infrastructure.settings.main import get_settings
from src.interfaces.api.v1.main import api_v1_router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """
    Application lifespan handler.

    - On startup: initialize core infrastructure.
    - On shutdown: gracefully release all external resources.
    """
    settings = get_settings()

    db_manager = init_db_manager(settings)
    await db_manager.initialize()

    yield

    await db_manager.shutdown()


def create_api_app() -> FastAPI:
    """
    FastAPI application factory.

    Allows:
    - easier testing (create independent app instances),
    - different configuration per environment (dev/stage/prod).
    """
    configure_logging()

    settings = get_settings()

    app = FastAPI(
        title=settings.api.title,
        version=settings.api.version,
        debug=settings.api.debug,
        lifespan=lifespan,
    )

    # Logging / request context middleware (request_id, user_id, etc.)
    app.add_middleware(RequestContextMiddleware)

    # Handle unexpected and custom errors
    app.add_exception_handler(Exception, exception_handler)

    # Global middleware (CORS, logging, etc.).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix="/api")

    # Project root is four levels above this file: src/interfaces/api/main.py
    static_dir = Path(__file__).resolve().parent.parent.parent.parent / "static"
    if static_dir.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=static_dir, html=True),
            name="static",
        )

    return app
