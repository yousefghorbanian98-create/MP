"""لاگ ساختاریافته با structlog — JSON برای Grafana/Loki (لایهٔ ۱۳).

WP 2.1 / F‑03 (D‑13):
- پروسهٔ سرویس‌دهنده هرگز `rich` رندر نمی‌کند؛ حالت dev از `plain_traceback` استفاده می‌کند.
- نوشتن خروجی از event loop جداست: صف محدود + نخ نویسنده (الگوی QueueHandler/QueueListener).
  رندر JSON در نخ فراخواننده می‌ماند (هزینهٔ کم)؛ I/O کند نخ درخواست را نمی‌بندد.
- traceback با سقف ۵۰ فریم و بدون locals ثبت می‌شود.
"""

from __future__ import annotations

import logging
import queue
import sys
import threading
from typing import TextIO

import structlog
from asgi_correlation_id import correlation_id

_QUEUE_MAX = 10_000


class _State:
    """وضعیت سراسری نویسنده (یک شیء، بدون global)."""

    def __init__(self) -> None:
        self.queue: queue.Queue[str | None] = queue.Queue(maxsize=_QUEUE_MAX)
        self.sink: TextIO | None = None
        self.dropped = 0
        self.write_failures = 0
        self.writer: threading.Thread | None = None
        self.lock = threading.Lock()


_state = _State()


def _writer_loop(state: _State) -> None:
    while True:
        item = state.queue.get()
        try:
            if item is None:
                return
            target = state.sink if state.sink is not None else sys.stdout
            try:
                target.write(item)
                target.flush()
            except Exception:  # noqa: BLE001 - نویسنده نباید بمیرد؛ شمارش و ادامه
                state.write_failures += 1
        finally:
            state.queue.task_done()


def _ensure_writer(state: _State) -> None:
    with state.lock:
        if state.writer is None or not state.writer.is_alive():
            state.writer = threading.Thread(
                target=_writer_loop, args=(state,), name="mp-log-writer", daemon=True
            )
            state.writer.start()


class _QueuedStream:
    """شیٔ شبه‌فایل: `write` فقط در صف می‌گذارد و هرگز I/O نمی‌کند."""

    def __init__(self, state: _State) -> None:
        self._state = state

    def write(self, text: str) -> int:
        try:
            self._state.queue.put_nowait(text)
        except queue.Full:
            self._state.dropped += 1
        return len(text)

    def flush(self) -> None:
        return None


def flush_logs() -> None:
    """تا تخلیهٔ صف صبر کن (برای تست‌ها و خاموش‌شدن)."""
    writer = _state.writer
    if writer is not None and writer.is_alive():
        _state.queue.join()


def dropped_log_count() -> int:
    """تعداد خطوطی که به‌خاطر پر بودن صف حذف شدند."""
    return _state.dropped


def add_request_id(_logger, _method_name: str, event_dict: dict) -> dict:
    """Attach the OSS ASGI correlation middleware's ID to structured logs."""
    request_id = correlation_id.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(*, json_logs: bool = True, stream: TextIO | None = None) -> None:
    """پیکربندی structlog — در dev خوانا (بدون rich)، در production JSON.

    `stream` برای تست‌ها؛ پیش‌فرض stdout.
    """
    flush_logs()
    _state.sink = stream
    _ensure_writer(_state)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if json_logs:
        processors.append(
            structlog.processors.ExceptionRenderer(
                structlog.tracebacks.ExceptionDictTransformer(
                    show_locals=False,
                    max_frames=50,
                    use_rich=False,
                )
            )
        )
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=stream is None and sys.stdout.isatty(),
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(file=_QueuedStream(_state)),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
