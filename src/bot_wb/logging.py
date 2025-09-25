from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOG_CONTEXT: ContextVar[dict[str, str]] = ContextVar("log_context", default={})


def _patch_record(record: dict[str, Any]) -> None:
    context = _LOG_CONTEXT.get({})
    record.setdefault("extra", {})
    for key, value in context.items():
        record["extra"].setdefault(key, value)


def _format_record(record: dict[str, Any]) -> str:
    extra = record.get("extra", {})
    context_bits = []
    for key in ("tg_id", "chat_id", "handler"):
        val = extra.get(key)
        if val:
            context_bits.append(f"{key}={val}")
    context_str = " ".join(context_bits) if context_bits else "-"
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "{name}:{function}:{line} | "
        f"{context_str} | "
        "<level>{message}</level>"
    )


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    logger.add(
        sys.stdout,  # type: ignore[arg-type]
        level=level,
        colorize=True,
        enqueue=True,
        format=_format_record,  # type: ignore[arg-type]
        backtrace=False,
        diagnose=False,
        patcher=_patch_record,
    )
    logger.add(
        LOG_DIR / "bot.log",
        level="INFO",
        rotation="20 MB",
        retention="14 days",
        enqueue=True,
        format=_format_record,  # type: ignore[arg-type]
        backtrace=True,
        diagnose=True,
        patcher=_patch_record,
    )
    logger.add(
        LOG_DIR / "errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
        format=_format_record,  # type: ignore[arg-type]
        backtrace=True,
        diagnose=True,
        patcher=_patch_record,
    )


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
