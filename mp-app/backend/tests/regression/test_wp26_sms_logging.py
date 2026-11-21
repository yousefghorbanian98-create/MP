"""WP 2.6 (F-29، الحاقیهٔ A1) — خطاهای ارسال پیامک باید traceback داشته باشند.

قبل از اصلاح: هر شش شاخهٔ `except` در `app/sms.py` با `log.error` ثبت می‌شد و
`exc_info` خالی بود ⇒ علت واقعی خطای فراهم‌کننده در لاگ نبود (TRY400).
بعد از اصلاح: `log.exception` در همان شش شاخه؛ ارسال به URL غیر https همچنان
بدون درخواست شبکه رد می‌شود؛ کلید API هیچ‌وقت در لاگ نمی‌آید.
"""

from __future__ import annotations

import logging
import socket
import urllib.error
import urllib.request

import pytest

from app import sms
from app.config import settings

SECRET_KEY = "SECRET-KEY-WP26-DO-NOT-LOG"  # مقدار تست، نه رمز واقعی؛ فقط برای بررسی نشت در لاگ
SECRET_PASS = "SECRET-PASS-WP26-DO-NOT-LOG"  # مقدار تست، نه رمز واقعی؛ فقط برای بررسی نشت در لاگ
HTTPS_URL = "https://sms.example.invalid/api"


@pytest.fixture
def https_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "sms_api_url", HTTPS_URL)
    monkeypatch.setattr(settings, "sms_api_key", SECRET_KEY)
    monkeypatch.setattr(settings, "sms_password", SECRET_PASS)
    monkeypatch.setattr(settings, "sms_username", "u")
    monkeypatch.setattr(settings, "sms_originator", "10001")


def _raise(exc: BaseException):
    def _fake(*_args, **_kwargs):
        raise exc

    return _fake


FAILURES = [
    ("webmagfa", sms.WebMagfaProvider, urllib.error.HTTPError(HTTPS_URL, 500, "boom", None, None)),
    ("webmagfa", sms.WebMagfaProvider, urllib.error.URLError(socket.gaierror("dns"))),
    ("webmagfa", sms.WebMagfaProvider, TimeoutError("slow")),
    (
        "kavenegar",
        sms.KavenegarProvider,
        urllib.error.HTTPError(HTTPS_URL, 503, "busy", None, None),
    ),
    ("kavenegar", sms.KavenegarProvider, urllib.error.URLError(socket.gaierror("dns"))),
    ("kavenegar", sms.KavenegarProvider, TimeoutError("slow")),
]


@pytest.mark.parametrize(
    ("name", "cls", "exc"), FAILURES, ids=lambda v: getattr(v, "__name__", str(v))
)
def test_failure_branch_logs_traceback(
    name: str, cls: type, exc: BaseException, https_settings, monkeypatch, caplog
) -> None:
    """هر شاخهٔ except باید ERROR با exc_info ثبت کند (نه فقط پیام)."""
    monkeypatch.setattr(urllib.request, "urlopen", _raise(exc))
    caplog.set_level(logging.DEBUG, logger="mp.sms")

    assert cls().send("09120000000", "کد: 1234") is False

    errors = [r for r in caplog.records if r.name == "mp.sms" and r.levelno == logging.ERROR]
    assert errors, "هیچ خطای لاگ‌شده‌ای ثبت نشد"
    assert all(r.exc_info is not None for r in errors), "traceback در لاگ نیست (F-29)"


@pytest.mark.parametrize(
    ("cls", "exc"), [(c, e) for _n, c, e in FAILURES], ids=lambda v: getattr(v, "__name__", "exc")
)
def test_secrets_never_reach_log_output(
    cls: type, exc: BaseException, https_settings, monkeypatch, caplog
) -> None:
    """کلید و رمز API در متن لاگ یا traceback نباید ظاهر شوند."""
    monkeypatch.setattr(urllib.request, "urlopen", _raise(exc))
    caplog.set_level(logging.DEBUG)

    cls().send("09120000000", "کد: 1234")

    rendered = "\n".join(caplog.text.splitlines()) + "".join(
        str(r.exc_info[1]) for r in caplog.records if r.exc_info
    )
    assert SECRET_KEY not in rendered
    assert SECRET_PASS not in rendered


@pytest.mark.parametrize("cls", [sms.WebMagfaProvider, sms.KavenegarProvider])
def test_non_https_is_rejected_before_any_request(cls: type, monkeypatch) -> None:
    """URL غیر https ⇒ False و بدون فراخوانی urlopen (S310 با اجبار scheme)."""
    monkeypatch.setattr(settings, "sms_api_url", "http://sms.example.invalid/api")
    called = []
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: called.append(1))

    assert cls().send("09120000000", "کد: 1234") is False
    assert called == []
