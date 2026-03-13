from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.logging.middleware import RequestContextMiddleware
from src.infrastructure.logging.config import configure_logging
from src.infrastructure.settings.main import get_settings
from src.infrastructure.database.database_manager import DatabaseManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    - On startup: initialize core infrastructure (database, queues, etc.).
    - On shutdown: gracefully release all external resources.
    """
    settings = get_settings()

    # Initialize database manager once for the whole application lifetime.
    db_manager = DatabaseManager(
        database_url=settings.db.url,
        debug=settings.db.debug,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
        pool_recycle=settings.db.pool_recycle,
    )
    await db_manager.initialize()

    # Expose the manager to dependency functions.
    app.state.db_manager = db_manager

    try:
        yield
    finally:
        # Gracefully shut down infrastructure.
        await db_manager.shutdown()
        app.state.db_manager = None


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

    # Global middleware (CORS, logging, etc.).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # app.include_router(api_router, prefix="/api")

    return app