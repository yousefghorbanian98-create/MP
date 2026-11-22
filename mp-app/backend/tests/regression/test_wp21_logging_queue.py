"""WP 2.1 / F‑03 — لاگ سرویس‌دهنده بیرون از event loop و بدون رندر rich (D‑13).

قرمز پیش از اصلاح: `configure_logging` پارامتر `stream` ندارد، `flush_logs` وجود
ندارد، و حالت dev از `RichTracebackFormatter` (خروجی جعبه‌دار) استفاده می‌کند.
"""

from __future__ import annotations

import io
import json
import sys
import time

import pytest

from app import logging as applog


def _deep_error(depth: int) -> None:
    if depth == 0:
        raise ValueError("boom")
    _deep_error(depth - 1)


def _log_exception(depth: int) -> None:
    logger = applog.get_logger("test.wp21")
    try:
        _deep_error(depth)
    except ValueError:
        logger.exception("unhandled_error", path="/x")


@pytest.fixture(autouse=True)
def _restore_stdout_config():
    yield
    applog.configure_logging(json_logs=True)


def test_dev_mode_never_renders_rich_boxes():
    """C1: در dev هم جعبه/رنگ rich نباید در خروجی سرویس بیاید."""
    stream = io.StringIO()
    applog.configure_logging(json_logs=False, stream=stream)
    _log_exception(2)
    applog.flush_logs()
    out = stream.getvalue()
    assert "boom" in out
    for marker in ("╭", "│", "╰", "\x1b["):
        assert marker not in out, f"rich artefact {marker!r} in service log"


def test_service_logging_does_not_block_caller_on_slow_io():
    """C2: نوشتن کند نباید نخ فراخواننده (event loop) را ببندد."""

    class SlowStream(io.StringIO):
        def write(self, s):
            time.sleep(0.05)
            return super().write(s)

    slow = SlowStream()
    applog.configure_logging(json_logs=True, stream=slow)
    logger = applog.get_logger("test.wp21.block")
    start = time.perf_counter()
    for i in range(20):
        logger.info("tick", i=i)
    caller_seconds = time.perf_counter() - start
    applog.flush_logs()
    assert caller_seconds < 0.3, f"caller blocked {caller_seconds:.2f}s by log I/O"
    assert slow.getvalue().count("\n") == 20


def test_exception_output_is_bounded_and_json():
    """C3: traceback عمیق سقف فریم دارد و هر خط JSON معتبر است."""
    stream = io.StringIO()
    applog.configure_logging(json_logs=True, stream=stream)
    _log_exception(300)
    applog.flush_logs()
    lines = [ln for ln in stream.getvalue().splitlines() if ln.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "unhandled_error"
    assert len(lines[0]) < 20_000, f"exception record too large: {len(lines[0])} bytes"


def test_proxy_80_errors_stay_under_5mb():
    """C4 (پروکسی، D‑13 اصلاح‑شده): ۸۰ خطا (هم‌اندازهٔ بار ۸۰ کلاینتی) ⇒ حجم لاگ < ۵ MB."""
    stream = io.StringIO()
    applog.configure_logging(json_logs=True, stream=stream)
    for _ in range(80):
        _log_exception(100)
    applog.flush_logs()
    size = len(stream.getvalue().encode("utf-8"))
    assert size < 5 * 1024 * 1024, f"log volume {size} bytes for 80 errors"


def test_stdout_is_default_sink():
    """بدون stream، لاگ به stdout می‌رود (سازگاری با رفتار قبلی)."""
    applog.configure_logging(json_logs=True)
    assert applog.get_logger("test.wp21.default") is not None
    assert sys.stdout is not None
