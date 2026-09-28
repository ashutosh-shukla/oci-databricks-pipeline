"""src/common/oci_logger.py - PipelineLogger: one logging class for the whole pipeline."""

import logging
from logging.handlers import RotatingFileHandler

from config.settings import Settings, PROJECT_ROOT


class PipelineLogger:
    """
    Wraps a standard logger and configures it from Settings.

    Usage in any module:
        log = PipelineLogger(__name__)
        log.info("message")
        Settings can be injected (useful for tests): PipelineLogger(name, settings=my_settings)
    """

    _FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, name: str, settings: Settings = None):
        self._settings = settings or Settings.load()
        self._logger = logging.getLogger(name)
        self._configure()

    def _configure(self) -> None:
        level = self._settings.get("logging", "level", default="INFO")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Guard: creating many PipelineLogger objects for one name must not stack handlers.
        if self._logger.handlers:
            return

        formatter = logging.Formatter(self._FORMAT, datefmt=self._DATE_FORMAT)
        self._logger.addHandler(self._build_file_handler(formatter))
        if self._settings.get("logging", "console_output", default=True):
            self._logger.addHandler(self._build_console_handler(formatter))
            self._logger.propagate = False

    def _build_file_handler(self, formatter) -> logging.Handler:
        log_dir = PROJECT_ROOT / self._settings.get(
            "logging", "log_dir", default="logs"
        )
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self._settings.get("logging", "log_file", default="pipeline.log")
        handler = RotatingFileHandler(
            log_dir / log_file, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(formatter)
        return handler

    @staticmethod
    def _build_console_handler(formatter) -> logging.Handler:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        return handler

    def debug(self, msg, *args):
        self._logger.debug(msg, *args)

    def info(self, msg, *args):
        self._logger.info(msg, *args)

    def warning(self, msg, *args):
        self._logger.warning(msg, *args)

    def error(self, msg, *args):
        self._logger.error(msg, *args)

    def exception(self, msg, *args):
        self._logger.exception(msg, *args)  # includes traceback


if __name__ == "__main__":
    log = PipelineLogger("logger_smoke_test")
    log.debug("debug message")
    log.info("info message")
    log.warning("warning message")
    log.error("error message")
    PipelineLogger("logger_smoke_test").info("second object, same name - prints ONCE")
