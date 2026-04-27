from typing import TYPE_CHECKING

from src.infrastructure.database.database_manager import DatabaseManager

if TYPE_CHECKING:
    from src.infrastructure.settings.main import Settings

_db_manager: DatabaseManager | None = None


def init_db_manager(settings: Settings) -> DatabaseManager:
    global _db_manager
    _db_manager = DatabaseManager(
        database_url=settings.db.url,
        debug=settings.db.debug,
        pool_size=settings.db.pool_size,
        max_overflow=settings.db.max_overflow,
        pool_recycle=settings.db.pool_recycle,
    )
    return _db_manager


def get_db_manager() -> DatabaseManager:
    if _db_manager is None:
        raise RuntimeError("DB Manager is not initialized")
    return _db_manager
