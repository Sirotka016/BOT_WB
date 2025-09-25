from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from loguru import logger as _logger

# Экспортируемый логгер
logger = _logger

_LOG_CONTEXT: ContextVar[dict[str, str]] = ContextVar("log_context", default={})


def _merge_context(extra: Any) -> dict[str, str]:
    context: dict[str, str] = dict(_LOG_CONTEXT.get({}) or {})
    if isinstance(extra, dict):
        for key, value in extra.items():
            if value is None:
                continue
            context[key] = str(value)
    return context


def _fmt_console(record: Any) -> str:
    """Форматер для консоли, совместим со всеми версиями loguru."""
    context = _merge_context(record.get("extra", {}))
    trace_id = context.get("trace_id", "-")
    user_id = context.get("user_id", "-")
    chat_id = context.get("chat_id", "-")
    time = record["time"].strftime("%H:%M:%S")
    level = f"{record['level'].name:<8}"
    where = f"{record['module']}:{record['function']}:{record['line']}"
    message = record["message"]
    return f"{time} | {level} | {where} | {trace_id} | {user_id} | {chat_id} | {message}"


def _fmt_file(record: Any) -> str:
    """Форматер для файла, совместим со всеми версиями loguru."""
    context = _merge_context(record.get("extra", {}))
    trace_id = context.get("trace_id", "-")
    user_id = context.get("user_id", "-")
    chat_id = context.get("chat_id", "-")
    time = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = f"{record['level'].name:<8}"
    where = f"{record['module']}:{record['function']}:{record['line']}"
    message = record["message"]
    return (
        f"{time} | {level} | {where} | "
        f"trace={trace_id} user={user_id} chat={chat_id} | {message}"
    )


def setup_logging(level: str = "INFO") -> None:
    """
    Инициализация логирования:
    - консольный sink
    - файловый sink с ротацией по дате
    Без использования 'patcher' и 'logger.patch' (совместимость с loguru 0.5+).
    """
    logger.remove()

    logs_dir = Path(os.getenv("BOT_WB_LOG_DIR", "data/logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_sink = logs_dir / "app_{time:YYYY-MM-DD}.log"

    lvl = (level or "INFO").upper()

    logger.add(
        sys.stdout,
        level=lvl,
        format=_fmt_console,  # Callable[[Any], str] — совместимо с ожидаемым Record
        backtrace=True,
        diagnose=False,
        enqueue=False,
    )

    logger.add(
        file_sink,
        level=lvl,
        format=_fmt_file,
        rotation="00:00",
        retention="7 days",
        compression=None,
        backtrace=False,
        diagnose=False,
        enqueue=True,
    )


def push_log_context(**values: Any) -> Token[dict[str, str]]:
    current = dict(_LOG_CONTEXT.get({}) or {})
    for key, value in values.items():
        if value is None:
            continue
        current[key] = str(value)
    return _LOG_CONTEXT.set(current)


def pop_log_context(token: Token[dict[str, str]]) -> None:
    _LOG_CONTEXT.reset(token)


@contextmanager
def log_context(**values: Any) -> Iterator[None]:
    token = push_log_context(**values)
    try:
        yield
    finally:
        pop_log_context(token)


__all__ = [
    "logger",
    "setup_logging",
    "push_log_context",
    "pop_log_context",
    "log_context",
]
