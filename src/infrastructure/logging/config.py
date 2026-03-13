import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Literal

import structlog

# --- public types & logger name prefixes ---

EnvType = Literal["dev", "prod", "test"]

API_LOGGER_NAME = "openshelf.api"
WORKER_LOGGER_NAME = "openshelf.worker"
SQL_LOGGER_NAME = "openshelf.sql"


def get_env() -> EnvType:
    """
    Detect the current application environment from APP_ENV.

    Supported values: dev | prod | test.
    Any unknown value falls back to "dev".
    """
    env = os.getenv("APP_ENV", "dev").lower()
    if env not in {"dev", "prod", "test"}:
        return "dev"
    return env  # type: ignore[return-value]


def _get_log_level() -> int:
    """
    Determine the base log level.

    Priority:
    1. LOG_LEVEL env var (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    2. Environment defaults:
       - dev: DEBUG
       - test: WARNING
       - prod: INFO
    """
    level_name = os.getenv("LOG_LEVEL")
    if level_name:
        return getattr(logging, level_name.upper(), logging.INFO)

    env = get_env()
    if env == "dev":
        return logging.DEBUG
    if env == "test":
        return logging.WARNING
    return logging.INFO


def _build_stdlib_handlers() -> dict[str, logging.Handler]:
    """
    Build stdlib handlers:
    - console (shared),
    - api.log (API layer),
    - worker.log (background tasks),
    - sql.log (SQL/DB).
    """
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)

    def _make_rotating_handler(filename: str) -> TimedRotatingFileHandler:
        return TimedRotatingFileHandler(
            filename=os.path.join(log_dir, filename),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
            delay=True,
        )

    handlers: dict[str, logging.Handler] = {}

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_get_log_level())
    handlers["console"] = console_handler

    api_file = _make_rotating_handler("api.log")
    api_file.setLevel(_get_log_level())
    handlers["api_file"] = api_file

    worker_file = _make_rotating_handler("worker.log")
    worker_file.setLevel(_get_log_level())
    handlers["worker_file"] = worker_file

    sql_file = _make_rotating_handler("sql.log")
    sql_file.setLevel(logging.INFO)
    handlers["sql_file"] = sql_file

    return handlers


def configure_logging() -> None:
    """
    Main logging configuration entry point.

    Call this once at application startup.
    """
    # --- environment & base settings ---
    env = get_env()
    level = _get_log_level()
    handlers = _build_stdlib_handlers()

    # --- structlog processors & renderer ---
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.CallsiteParameterAdder(
            parameters=(
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            )
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if env == "dev":
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    # --- stdlib formatter bridging to structlog ---
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    # --- root logger: console only ---
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # Root outputs only to console. Domain-specific loggers handle file writes.
    console_handler = handlers["console"]
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- API logger: console + api.log ---
    api_logger = logging.getLogger(API_LOGGER_NAME)
    api_logger.setLevel(level)
    api_logger.propagate = False
    for handler_name in ("console", "api_file"):
        handler = handlers[handler_name]
        handler.setFormatter(formatter)
        api_logger.addHandler(handler)

    # --- worker logger: console + worker.log ---
    worker_logger = logging.getLogger(WORKER_LOGGER_NAME)
    worker_logger.setLevel(level)
    worker_logger.propagate = False
    for handler_name in ("console", "worker_file"):
        handler = handlers[handler_name]
        handler.setFormatter(formatter)
        worker_logger.addHandler(handler)

    # --- SQL logger: sql.log only ---
    sql_logger = logging.getLogger(SQL_LOGGER_NAME)
    sql_logger.setLevel(logging.INFO)
    sql_logger.propagate = False
    sql_handler = handlers["sql_file"]
    sql_handler.setFormatter(formatter)
    sql_logger.addHandler(sql_handler)

    # --- third-party loggers & warnings ---
    logging.captureWarnings(True)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Convenience factory for obtaining a structlog logger.

    Typical usage:
    - get_logger(__name__) for module-level loggers;
    - get_logger("openshelf.api.books") for API logs (api.log + console);
    - get_logger("openshelf.worker.email") for worker logs (worker.log + console).
    """
    if name is None:
        name = __name__
    return structlog.get_logger(name)