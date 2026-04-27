import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import TYPE_CHECKING, Any, Literal, cast, override

import structlog

from src.infrastructure.settings.main import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from types import TracebackType

settings: Settings = get_settings()

# --- public types & logger name prefixes ---

EnvType = Literal["dev", "prod", "test"]

API_LOGGER_NAME = "openshelf.api"
WORKER_LOGGER_NAME = "openshelf.worker"
SQL_LOGGER_NAME = "openshelf.sql"

# --- processor config ---

_CALLSITE_FIELDS = ("filename", "lineno", "func_name")

# Events whose callsite is always the same emitting line and therefore noise.
_CALLSITE_STRIP_EVENTS: frozenset[str] = frozenset({"request_completed"})

# Sensitive key denylist (Sentry defaults + project-specific).
# Case-insensitive substring match: "password" catches "user_password", etc.
_PII_DENYLIST: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credentials",
    "privatekey",
    "private_key",
    "token",
    "jwt",
    "session",
    "csrf",
    "csrftoken",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-csrftoken",
    "x-forwarded-for",
    "remote_addr",
    "ip_address",
    "access_token",
    "refresh_token",
    "token_hash",
    "password_hash",
)

_PII_REDACTED_VALUE = "***"
_PII_MAX_DEPTH = 6

# SQLAlchemy emits separate records for parameter values (e.g. "[generated in
# 0.0s] ('user', 'secret')"). They leak PII and are dropped by the filter;
# the SQL template line with placeholders is kept.
_SQL_PARAM_LOG_PREFIXES = (
    "[generated in",
    "[cached since",
    "[raw sql]",
    "[no key",
)


# --- environment & level resolution ---


def get_env() -> EnvType:
    """Detect application environment (dev | prod | test), defaulting to dev."""
    env = settings.app.app_env
    if env in {"dev", "prod", "test"}:
        return cast("EnvType", env)
    return "dev"


def _get_log_level() -> int:
    """Resolve log level from LOG_LEVEL, falling back to env-based defaults."""
    level_name = settings.app.log_level
    if level_name:
        return getattr(logging, level_name, logging.INFO)

    env = get_env()
    if env == "dev":
        return logging.DEBUG
    if env == "test":
        return logging.WARNING
    return logging.INFO


def _should_log_to_file(env: EnvType) -> bool:
    """Decide file logging: explicit LOG_TO_FILE wins; else dev=on, prod/test=off."""
    # 12-factor: prod streams to stdout, orchestrator persists. Files are a
    # dev convenience for `tail -f`.
    explicit = settings.app.log_to_file
    if explicit is not None:
        return explicit
    return env == "dev"


def _sql_level() -> int:
    """SQLAlchemy verbosity: INFO when DB_DEBUG=true, else WARNING."""
    return logging.INFO if settings.db.debug else logging.WARNING


# --- structlog processors ---


def add_error_location(
    _logger: object,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Replace `exc_info` with flat fields pointing at the exception's innermost frame."""
    # Keeps logs clean across dev/prod: no multi-line tracebacks, just the
    # file/line/func where `raise` happened plus type and message.
    exc_info: Any = event_dict.get("exc_info")
    if not exc_info:
        return event_dict

    exc_triple: tuple[type[BaseException], BaseException, TracebackType | None] | None = None

    if exc_info is True:
        exc_type_live, exc_value_live, exc_tb_live = sys.exc_info()
        if exc_type_live is not None and exc_value_live is not None:
            exc_triple = (exc_type_live, exc_value_live, exc_tb_live)
    elif isinstance(exc_info, BaseException):
        exc_triple = (type(exc_info), exc_info, exc_info.__traceback__)
    elif isinstance(exc_info, tuple) and len(exc_info) == 3 and exc_info[0] is not None:
        exc_triple = cast("tuple[type[BaseException], BaseException, TracebackType | None]", exc_info)

    if exc_triple is None:
        event_dict.pop("exc_info", None)
        return event_dict

    exc_type, exc_value, tb = exc_triple

    if tb is not None:
        while tb.tb_next is not None:
            tb = tb.tb_next
        event_dict["error_file"] = os.path.basename(tb.tb_frame.f_code.co_filename)
        event_dict["error_line"] = tb.tb_lineno
        event_dict["error_func"] = tb.tb_frame.f_code.co_name

    event_dict["error_type"] = exc_type.__name__
    event_dict["error_message"] = str(exc_value)

    event_dict.pop("exc_info", None)

    for key in _CALLSITE_FIELDS:
        event_dict.pop(key, None)

    return event_dict


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(needle in lowered for needle in _PII_DENYLIST)


def _scrub_value(value: object, depth: int) -> object:
    if depth <= 0:
        return value

    if isinstance(value, dict):
        scrubbed: dict[object, object] = {}
        for k, v in cast("dict[object, object]", value).items():
            if isinstance(k, str) and _is_sensitive_key(k):
                scrubbed[k] = _PII_REDACTED_VALUE
            else:
                scrubbed[k] = _scrub_value(v, depth - 1)
        return scrubbed
    if isinstance(value, list):
        return [_scrub_value(item, depth - 1) for item in cast("list[object]", value)]
    if isinstance(value, tuple):
        return tuple(_scrub_value(item, depth - 1) for item in cast("tuple[object, ...]", value))
    return value


def drop_none_values(
    _logger: object,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Remove keys whose value is None to keep events compact."""
    for key in list(event_dict.keys()):
        if event_dict[key] is None:
            del event_dict[key]
    return event_dict


def strip_callsite_for_events(
    _logger: object,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Drop callsite fields for events in _CALLSITE_STRIP_EVENTS."""
    event_name = event_dict.get("event")
    if isinstance(event_name, str) and event_name in _CALLSITE_STRIP_EVENTS:
        for key in _CALLSITE_FIELDS:
            event_dict.pop(key, None)
    return event_dict


def scrub_pii(
    _logger: object,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Recursively mask values under sensitive keys with '***'."""
    for key in list(event_dict.keys()):
        if _is_sensitive_key(key):
            event_dict[key] = _PII_REDACTED_VALUE
        else:
            event_dict[key] = _scrub_value(event_dict[key], _PII_MAX_DEPTH)
    return event_dict


# --- SQL params filter ---


class _SQLAlchemyParamsFilter(logging.Filter):
    """Drop SQLAlchemy records that contain raw bind-parameter values."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg) if record.msg else ""
        return not msg.startswith(_SQL_PARAM_LOG_PREFIXES)


# --- handler construction ---


def _build_stdlib_handlers(*, with_files: bool) -> dict[str, logging.Handler]:
    """Build console handler plus (optionally) rotating file handlers."""
    handlers: dict[str, logging.Handler] = {}

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_get_log_level())
    handlers["console"] = console_handler

    if not with_files:
        return handlers

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

    api_file = _make_rotating_handler("api.log")
    api_file.setLevel(_get_log_level())
    handlers["api_file"] = api_file

    worker_file = _make_rotating_handler("worker.log")
    worker_file.setLevel(_get_log_level())
    handlers["worker_file"] = worker_file

    sql_file = _make_rotating_handler("sql.log")
    sql_file.setLevel(_sql_level())
    handlers["sql_file"] = sql_file

    return handlers


# --- main entry point ---


def configure_logging() -> None:
    """Configure structlog + stdlib logging. Call once at application startup."""
    env = get_env()
    level = _get_log_level()
    with_files = _should_log_to_file(env)
    handlers = _build_stdlib_handlers(with_files=with_files)

    # Processors for structlog-native events (our code).
    # Callsite is included — points at our own log call site.
    native_processors: list[structlog.types.Processor] = [
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
        add_error_location,
        strip_callsite_for_events,
        scrub_pii,
        drop_none_values,
    ]

    # Processors for foreign records (sqlalchemy, uvicorn, etc.).
    # No callsite — it would point into library internals.
    foreign_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        add_error_location,
        scrub_pii,
        drop_none_values,
    ]

    if env == "dev":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *native_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=foreign_processors,
    )

    for handler in handlers.values():
        handler.setFormatter(formatter)

    # --- root logger: console only ---
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handlers["console"])

    # --- API logger: console (+ api.log when files enabled) ---
    api_logger = logging.getLogger(API_LOGGER_NAME)
    api_logger.setLevel(level)
    api_logger.propagate = False
    api_logger.handlers.clear()
    api_handler_names = ["console"] + (["api_file"] if with_files else [])
    for handler_name in api_handler_names:
        api_logger.addHandler(handlers[handler_name])

    # --- worker logger: console (+ worker.log when files enabled) ---
    worker_logger = logging.getLogger(WORKER_LOGGER_NAME)
    worker_logger.setLevel(level)
    worker_logger.propagate = False
    worker_logger.handlers.clear()
    worker_handler_names = ["console"] + (["worker_file"] if with_files else [])
    for handler_name in worker_handler_names:
        worker_logger.addHandler(handlers[handler_name])

    # --- SQL loggers: sqlalchemy + openshelf.sql → dedicated channel ---
    sql_filter = _SQLAlchemyParamsFilter()
    if with_files:
        sql_target_handler: logging.Handler = handlers["sql_file"]
    else:
        sql_target_handler = logging.StreamHandler()
        sql_target_handler.setLevel(_sql_level())
        sql_target_handler.setFormatter(formatter)
    sql_target_handler.addFilter(sql_filter)

    for sql_logger_name in (SQL_LOGGER_NAME, "sqlalchemy.engine", "sqlalchemy.pool"):
        lg = logging.getLogger(sql_logger_name)
        lg.setLevel(_sql_level())
        lg.propagate = False
        lg.handlers.clear()
        lg.addHandler(sql_target_handler)

    # --- third-party loggers & warnings ---
    logging.captureWarnings(True)
    logging.getLogger("py.warnings").setLevel(logging.ERROR)
    logging.getLogger("passlib").setLevel(logging.ERROR)
    logging.getLogger("bcrypt").setLevel(logging.ERROR)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # Replaced by our own `request_completed` event from RequestContextMiddleware.
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.propagate = False
    uvicorn_access.disabled = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger; use "openshelf.api.*" / "openshelf.worker.*" for routing."""
    if name is None:
        name = __name__
    return structlog.get_logger(name)
