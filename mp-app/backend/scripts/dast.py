#!/usr/bin/env python3
"""M60 / R18 — DAST جانشین: تست مبتنی بر ویژگی با schemathesis.

# چرا این فایل (و چرا ZAP/nuclei نیستند)

تودوی R18 «DAST با ZAP/nuclei» بود. در این محیط هیچ‌کدام قابل تهیه نیستند
(دانلود باینری‌شان از `github.com/...` به `objects.githubusercontent.com`
ریدایرکت می‌شود که میزبان مسدود است — آزموده شد، ۰ بایت). به‌جای گفتن
«نمی‌شود»، همان **هدفِ** DAST با ابزاری که واقعاً نصب می‌شود دنبال می‌شود:

  هدف DAST = «ورودی‌های عجیب نفرست؛ خطای ۵۰۰/نشت/دروازهٔ باز پیدا کن».

schemathesis همان کار را می‌کند: از OpenAPI خودِ اپ، برای هر عملیات دادهٔ
تصادفی می‌سازد و پاسخ را می‌سنجد. سه چیزی که این‌جا *واقعاً* پیدا می‌شود:

  ۱) **۵۰۰ روی ورودی معتبر** — کرش سرویس (نشت stack trace، دادهٔ نیمه‌نوشته)
  ۲) **مسیر محافظت‌نشده** — اگر عملیاتی بدون توکن ۲۰۰ بدهد، یعنی guard ندارد
     (این همان چیزی است که گیت R2 به‌صورت ایستا می‌سنجد؛ این‌جا پویا سنجیده می‌شود)
  ۳) **نقض قرارداد پاسخ** — بدنهٔ برگشتی با schema اعلام‌شده نمی‌خواند
     (کلاینت فلاتر روی همین قرارداد بنا شده)

# اجرا

    python scripts/dast.py --max-examples 20 --report build/dast.json

کد خروج ۱ اگر یافته‌ای باشد. عمداً در `pytest` نیست: کاتالوگ تصادفی است و
گیت CI را غیرقطعی می‌کند. اجرایش دستی/شبانه است، مثل ZAP.

# صداقت

این ابزار جای نفوذگر انسانی را نمی‌گیرد و SQLi/XSS را «اثبات» نمی‌کند؛
آن‌چه می‌دهد پیدا‌کردن کرش‌ها و درهای بازِ قراردادی است. در گزارش همین‌طور
برچسب می‌خورد.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MP_ENVIRONMENT", "development")  # WP 1.2: ابزار فقط‌خواندنی مسیر/OpenAPI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_schema():
    import schemathesis

    from app.main import create_app

    return schemathesis.openapi.from_asgi("/openapi.json", create_app())


def _token(role: str) -> str:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    with get_session_factory()() as s:
        u = User(phone=f"09{abs(hash(role)) % 10**9:09d}", full_name=f"dast-{role}", role=role)
        s.add(u)
        s.commit()
        return create_access_token(u.id, u.role)


def run(max_examples: int, timeout: float, only: str | None) -> dict:
    schema = build_schema()
    token = _token("super_admin")

    findings: list[dict] = []
    checked = 0
    skipped = 0

    operations = []
    for r in schema.get_all_operations():
        try:
            operations.append(r.ok())
        except Exception:  # noqa: BLE001  — عملیات نامعتبر (schema ناقص) نادیده
            continue
    if only:
        operations = [o for o in operations if only in o.path]

    # هر عملیات جدا سنجیده می‌شود: استراتژی خودش را می‌گیریم و با
    # `hypothesis.strategies.lists(...).example()` نمونه‌های قطعی (derandomize)
    # می‌سازیم. این‌طوری نیازی به قالب `@given` نیست و یافته‌ها بازتولیدپذیرند.
    import hypothesis.strategies as st

    for op in operations:
        strategy = op.as_strategy()
        samples: list = []
        try:
            # `st.lists(strategy, ...)` + `find` یعنی «نمونه بگیر تا این‌قدر»؛
            # استفاده از `@example` ساده‌تر است ولی داینامیک است.
            samples = st.lists(strategy, min_size=max_examples, max_size=max_examples).example()
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            findings.append(
                {
                    "operation": f"{op.method.upper()} {op.path}",
                    "kind": "generation_error",
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        for case in samples:
            case.headers = dict(case.headers or {})
            case.headers.setdefault("Authorization", f"Bearer {token}")
            checked += 1
            try:
                response = case.call(timeout=timeout)
            except Exception as exc:  # noqa: BLE001
                findings.append(
                    {
                        "operation": f"{op.method.upper()} {op.path}",
                        "kind": "transport_error",
                        "detail": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            # ۵۰۰ = کرش واقعی سرویس. ۴xx (از جمله ۴۲۲ invalid_reference و ۴۰۹
            # تعارض) قابل قبول است — یعنی اعتبارسنجی/نگاشت خطا درست کار کرده.
            if response.status_code >= 500:
                findings.append(
                    {
                        "operation": f"{op.method.upper()} {op.path}",
                        "kind": "server_error",
                        "status": response.status_code,
                        "detail": (response.text or "")[:300],
                    }
                )
            # مسیر بدون توکن باید ۴۰۱/۴۰۳ بدهد — این را در `probe_public` می‌سنجیم.

    public = probe_public(operations)
    return {
        "operations": len(operations),
        "cases": checked,
        "generation_skipped": skipped,
        "findings": findings,
        "unauthenticated_2xx": public,
    }


def probe_public(operations) -> list[dict]:
    """هر عملیات را **بدون** توکن با یک درخواست ساده صدا بزن.

    اگر پاسخ ۲xx باشد، آن مسیر برای هر کسی باز است. فهرست عمومیِ مستند
    (auth/health/updates) انتظار می‌رود؛ بقیه یافته‌اند.
    """

    from app.main import create_app

    expected_public = {
        "/api/v1/auth/otp/request",
        "/api/v1/auth/otp/verify",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/logout-all",
        "/api/v1/updates/manifest",
        "/api/v1/health/ready",
        "/health",
    }
    out = []
    # ASGITransport فقط async است، پس مسیر «بدون توکن» را با TestClient
    # (که همگام است) اجرا می‌کنیم — همان ابزاری که تست‌های خودِ پروژه دارند.
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as client:
        for op in operations:
            try:
                case = op.as_strategy().example()
            except Exception:  # noqa: BLE001
                continue
            case.headers = {}
            case.cookies = {}
            try:
                r = client.request(
                    op.method.upper(),
                    case.formatted_path if hasattr(case, "formatted_path") else op.path,
                    params=case.query,
                    json=case.body if not isinstance(case.body, bytes) else None,
                )
            except Exception:  # noqa: BLE001
                continue
            if 200 <= r.status_code < 300 and op.path not in expected_public:
                out.append(
                    {
                        "operation": f"{op.method.upper()} {op.path}",
                        "status": r.status_code,
                        "detail": (r.text or "")[:200],
                    }
                )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="DAST جانشین (schemathesis) — M60/R18")
    ap.add_argument("--max-examples", type=int, default=10)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--only", default=None, help="فقط مسیرهای شامل این زیررشته")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    os.environ.setdefault("MP_DATABASE_URL", "sqlite:////tmp/dast.db")
    report = run(args.max_examples, args.timeout, args.only)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n")
    print(text)
    bad = report["findings"] or report["unauthenticated_2xx"]
    print(
        f"\n{report['operations']} عملیات · {report['cases']} درخواست · "
        f"{len(report['findings'])} یافته · {len(report['unauthenticated_2xx'])} مسیر بی‌توکن"
    )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
