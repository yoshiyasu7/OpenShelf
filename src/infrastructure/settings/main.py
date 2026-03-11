from functools import lru_cache
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


@dataclass
class APISettings:
    """API server settings."""

    title: str = field(
        default_factory=lambda: os.getenv("API_TITLE", "OpenShelf API")
    )
    version: str = field(
        default_factory=lambda: os.getenv("API_VERSION", "1.0.0")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("API_DEBUG", "False").lower() == "true"
    )
    host: str = field(
        default_factory=lambda: os.getenv("API_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("API_PORT", "8000"))
    )


@dataclass
class DatabaseSettings:
    """Database connection settings."""

    debug: bool = field(
        default_factory=lambda: os.getenv("DB_DEBUG", "False").lower() == "true"
    )
    url: str = field(
        default_factory=lambda: _get_required_env("DB_URL")
    )
    pool_size: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10"))
    )
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )
    pool_timeout: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30"))
    )
    pool_recycle: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600"))
    )


@dataclass
class Settings:
    """All application settings."""
    
    api: APISettings = field(default_factory=APISettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings with caching for efficiency.
    Returns a singleton instance of Settings.
    """
    return Settings()