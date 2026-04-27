import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from skarner.core.tracing import get_trace_id

__all__ = ["get_logger", "setup_logging"]

_FORMAT = "%(asctime)s [%(levelname)s] [trace_id=%(trace_id)s] %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class _TraceIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


def setup_logging(
    level: int = logging.INFO,
    log_dir: str | Path | None = None,
    backup_days: int = 7,
) -> None:
    """Configure root logger with optional daily-rotating file output.

    Args:
        level: Logging level, e.g. logging.DEBUG.
        log_dir: Directory for log files. Console-only if None.
        backup_days: Number of daily log files to retain.
    """
    trace_filter = _TraceIDFilter()
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(trace_filter)
    handlers.append(stream_handler)

    if log_dir is not None:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=log_path / "app.log",
            when="midnight",
            interval=1,
            backupCount=backup_days,
            encoding="utf-8",
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(formatter)
        file_handler.addFilter(trace_filter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
