import logging
from types import SimpleNamespace

import pytest

from src.infrastructure.logging import config


def _set_settings(
    monkeypatch: pytest.MonkeyPatch, *, env: str, level: str, log_to_file: bool | None, db_debug: bool
) -> None:
    monkeypatch.setattr(
        config,
        "settings",
        SimpleNamespace(
            app=SimpleNamespace(app_env=env, log_level=level, log_to_file=log_to_file),
            db=SimpleNamespace(debug=db_debug),
        ),
    )


def test_env_and_level_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_settings(monkeypatch, env="dev", level="DEBUG", log_to_file=None, db_debug=False)
    assert config.get_env() == "dev"
    assert config._get_log_level() == logging.DEBUG
    assert config._should_log_to_file("dev") is True
    assert config._sql_level() == logging.WARNING

    _set_settings(monkeypatch, env="invalid", level="", log_to_file=True, db_debug=True)
    assert config.get_env() == "dev"
    assert config._get_log_level() == logging.DEBUG
    assert config._should_log_to_file("prod") is True
    assert config._sql_level() == logging.INFO


def test_error_location_and_scrub_processors() -> None:
    event = {"event": "request_completed", "filename": "a.py", "lineno": 1, "func_name": "f", "exc_info": None}
    assert config.drop_none_values(None, "info", event) == {
        "event": "request_completed",
        "filename": "a.py",
        "lineno": 1,
        "func_name": "f",
    }

    stripped = config.strip_callsite_for_events(None, "info", dict(event))
    assert "filename" not in stripped

    pii = {"password": "secret", "nested": {"token": "abc", "safe": "ok"}}
    scrubbed = config.scrub_pii(None, "info", pii)
    assert scrubbed["password"] == "***"
    assert scrubbed["nested"]["token"] == "***"

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        enriched = config.add_error_location(
            None, "error", {"exc_info": True, "filename": "x.py", "lineno": 2, "func_name": "g"}
        )
    assert enriched["error_type"] == "RuntimeError"
    assert "exc_info" not in enriched
    assert "filename" not in enriched


def test_sqlalchemy_params_filter_and_handlers(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _set_settings(monkeypatch, env="dev", level="INFO", log_to_file=None, db_debug=False)
    filter_ = config._SQLAlchemyParamsFilter()
    assert filter_.filter(logging.makeLogRecord({"msg": "[generated in 0.0s] ('a',)"})) is False
    assert filter_.filter(logging.makeLogRecord({"msg": "SELECT 1"})) is True

    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    handlers = config._build_stdlib_handlers(with_files=True)
    assert {"console", "api_file", "worker_file", "sql_file"}.issubset(handlers.keys())

    handlers_without_files = config._build_stdlib_handlers(with_files=False)
    assert list(handlers_without_files.keys()) == ["console"]


def test_configure_logging_for_dev_and_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_settings(monkeypatch, env="dev", level="INFO", log_to_file=True, db_debug=False)
    monkeypatch.setattr(
        config,
        "_build_stdlib_handlers",
        lambda *, with_files: {
            "console": logging.StreamHandler(),
            "api_file": logging.StreamHandler(),
            "worker_file": logging.StreamHandler(),
            "sql_file": logging.StreamHandler(),
        },
    )
    config.configure_logging()

    _set_settings(monkeypatch, env="prod", level="INFO", log_to_file=False, db_debug=True)
    monkeypatch.setattr(config, "_build_stdlib_handlers", lambda *, with_files: {"console": logging.StreamHandler()})
    config.configure_logging()


def test_get_logger_returns_named_logger() -> None:
    logger = config.get_logger("openshelf.api.test")
    default_logger = config.get_logger()

    assert logger is not None
    assert default_logger is not None


def test_remaining_branches_in_config_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_settings(monkeypatch, env="test", level="", log_to_file=None, db_debug=False)
    assert config._get_log_level() == logging.WARNING

    _set_settings(monkeypatch, env="prod", level="", log_to_file=None, db_debug=False)
    assert config._get_log_level() == logging.INFO

    by_exc = config.add_error_location(None, "error", {"exc_info": ValueError("boom")})
    assert by_exc["error_type"] == "ValueError"

    tuple_exc = config.add_error_location(None, "error", {"exc_info": (ValueError, ValueError("boom"), None)})
    assert tuple_exc["error_type"] == "ValueError"

    unknown_exc = config.add_error_location(None, "error", {"exc_info": "unsupported"})
    assert unknown_exc == {}

    def inner() -> None:
        raise RuntimeError("stack")

    def outer() -> None:
        inner()

    try:
        outer()
    except RuntimeError:
        with_tb = config.add_error_location(None, "error", {"exc_info": True})
    assert with_tb["error_line"] > 0

    assert config._scrub_value("value", 0) == "value"
    assert isinstance(config._scrub_value([{"token": "x"}], 2), list)
    assert isinstance(config._scrub_value(({"token": "x"},), 2), tuple)
