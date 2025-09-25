from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any, Dict

from loguru import logger as _base_logger

_LOG_CONTEXT: ContextVar[dict[str, str]] = ContextVar("log_context", default={})


def _patch_record(record: Dict[str, Any]) -> None:
    context = _LOG_CONTEXT.get({})
    if not context:
        return
    record.setdefault("extra", {})
    for key, value in context.items():
        record["extra"].setdefault(key, value)


# Экспортируемый логгер (будем его настраивать в setup_logging)
logger = _base_logger.patch(_patch_record)


# === Безопасные форматтеры (работают на любых версиях loguru) ===
def _fmt_console(record: Dict[str, Any]) -> str:
    extra = record.get("extra", {})
    trace_id = extra.get("trace_id", "-")
    user_id = extra.get("user_id", "-")
    chat_id = extra.get("chat_id", "-")
    time = record["time"].strftime("%H:%M:%S")
    level = f"{record['level'].name:<8}"
    where = f"{record['module']}:{record['function']}:{record['line']}"
    message = record["message"]
    return f"{time} | {level} | {where} | {trace_id} | {user_id} | {chat_id} | {message}"


def _fmt_file(record: Dict[str, Any]) -> str:
    extra = record.get("extra", {})
    trace_id = extra.get("trace_id", "-")
    user_id = extra.get("user_id", "-")
    chat_id = extra.get("chat_id", "-")
    time = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    level = f"{record['level'].name:<8}"
    where = f"{record['module']}:{record['function']}:{record['line']}"
    message = record["message"]
    return f"{time} | {level} | {where} | trace={trace_id} user={user_id} chat={chat_id} | {message}"


def setup_logging(level: str = "INFO") -> None:
    """
    Инициализация логирования:
    - консольный sink (читаемый для PyCharm)
    - файловый sink с ротацией по дате
    Без использования 'patcher', чтобы не зависеть от версии loguru.
    """
    # Очистить все ранее добавленные sink-и
    _base_logger.remove()

    # Директория логов: env-переменная имеет приоритет, иначе data/logs
    logs_dir = Path(os.getenv("BOT_WB_LOG_DIR", "data/logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    file_sink = logs_dir / "app_{time:YYYY-MM-DD}.log"

    # Уровень
    lvl = (level or "INFO").upper()

    # Консоль
    _base_logger.add(
        sys.stdout,
        level=lvl,
        format=_fmt_console,  # функция-форматтер вместо patcher
        backtrace=True,
        diagnose=False,
        enqueue=False,
    )

    # Файл
    _base_logger.add(
        file_sink,
        level=lvl,
        format=_fmt_file,  # функция-форматтер вместо patcher
        rotation="00:00",
        retention="7 days",
        compression=None,
        backtrace=False,
        diagnose=False,
        enqueue=True,
    )

    # Экспортируем настроенный логгер
    globals()["logger"] = _base_logger.patch(_patch_record)


def push_log_context(**values: Any) -> Token[dict[str, str]]:
    current = dict(_LOG_CONTEXT.get({}))
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
