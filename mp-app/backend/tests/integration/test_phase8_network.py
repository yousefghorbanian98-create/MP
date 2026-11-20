"""فاز ۸ لوپ ۴ — پروکسی معتمد، کلید rate-limit و افشای IP (QF-26).

# قرارداد

| مورد | قاعده |
|---|---|
| پیش‌فرض | `X-Forwarded-For` نادیده گرفته می‌شود؛ آدرس واقعی = peer |
| پروکسی معتمد | فقط اگر peer در `MP_TRUSTED_PROXIES` باشد، زنجیره خوانده می‌شود |
| زنجیره | از راست به چپ، پروکسی‌های معتمد رد می‌شوند؛ اولین غیرمعتمد = کلاینت |
| خرابی | هدر نامعتبر/خالی هرگز باعث عبور نمی‌شود (fail-closed به peer) |
| rate limit | کلید محدودیت همان IP محاسبه‌شده است، پس هدر جعلی سهمیهٔ تازه نمی‌سازد |

# چرا این تست

بدون این لایه، هر کسی با `X-Forwarded-For: 1.2.3.4` می‌توانست هویت IP خود را
جعل کند: هم لاگ/ممیزی گمراه می‌شد و هم محدودیت نرخ با تغییر هدر دور زده
می‌شد. اما «همیشه به XFF اعتماد کن» هم بد است؛ پس فقط peer معتمد.

# آنچه تست نمی‌کند
- TLS واقعی و پیکربندی nginx/Cloudflare (`BLOCKED`: محیط استقرار نیست).
- توزیع محدودیت نرخ بین چند worker با Valkey (نیازمند سرویس بیرونی).
"""

from __future__ import annotations

from starlette.requests import Request

from app.security.proxy import client_ip, parse_trusted, rate_limit_key


def _request(peer: str, forwarded: str | None = None) -> Request:
    headers = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode()))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "client": (peer, 12345),
        }
    )


def test_forwarded_header_is_ignored_without_trusted_proxies() -> None:
    req = _request("198.51.100.7", "1.2.3.4")
    assert client_ip(req, frozenset()) == "198.51.100.7"
    assert rate_limit_key(req, frozenset()) == "198.51.100.7"


def test_forwarded_header_is_ignored_when_peer_is_not_trusted() -> None:
    trusted = parse_trusted("10.0.0.5")
    spoofed = _request("203.0.113.50", "10.0.0.5, 1.2.3.4")
    assert client_ip(spoofed, trusted) == "203.0.113.50"


def test_trusted_peer_uses_rightmost_untrusted_hop() -> None:
    trusted = parse_trusted("10.0.0.5, 10.0.0.6")
    req = _request("10.0.0.5", "1.1.1.1, 203.0.113.9, 10.0.0.6")
    assert client_ip(req, trusted) == "203.0.113.9"


def test_malformed_or_empty_chain_falls_back_to_peer() -> None:
    trusted = parse_trusted("10.0.0.5")
    assert client_ip(_request("10.0.0.5", ""), trusted) == "10.0.0.5"
    assert client_ip(_request("10.0.0.5", "not-an-ip"), trusted) == "10.0.0.5"
    assert client_ip(_request("10.0.0.5", "   ,  "), trusted) == "10.0.0.5"


def test_spoofed_header_does_not_start_a_new_rate_limit_bucket() -> None:
    trusted = parse_trusted("10.0.0.5")
    a = _request("203.0.113.50", "1.2.3.4")
    b = _request("203.0.113.50", "5.6.7.8")
    assert rate_limit_key(a, trusted) == rate_limit_key(b, trusted) == "203.0.113.50"


def test_parse_trusted_normalizes_and_skips_blanks() -> None:
    assert parse_trusted("") == frozenset()
    assert parse_trusted(" 10.0.0.5 , ,10.0.0.6 ") == frozenset({"10.0.0.5", "10.0.0.6"})
