#!/usr/bin/env python3
"""M60 / R2 — گیتِ «هر مسیر یک guard دارد» (route-guard gate).

# چرا این فایل وجود دارد

`tests/integration/test_routes_artifact.py` فقط **فهرست** مسیرها را با یک
آرتیفکت مقایسه می‌کند: اگر کسی یک endpoint جدید اضافه کند، تست می‌شکند و
باید آرتیفکت را به‌روز کند. اما هیچ‌چیز نمی‌گوید مسیر جدید **guard** دارد یا نه.
یعنی یک مسیر تازهٔ بدون احراز هویت می‌توانست بی‌صدا وارد تولید شود.

این گیت همان شکاف را می‌بندد: هر مسیر باید یا در فهرست صریح `PUBLIC` باشد
(با دلیل) یا یک guard از جنس `require_permission`/`require_roles`/
`require_authenticated` روی خودش داشته باشد. هر مسیر ناشناختهٔ بدون guard ← تست شکست می‌خورد.

# چطور guard را می‌شناسیم

`app/deps.py` روی هر guard برچسب `__rbac__` می‌زند (`"permission"`,
`"roles"` یا `"authenticated"`). درخت وابستگی‌های هر route (`dependant`,
شامل guard سطح-router) پیمایش می‌شود. برچسب به‌جای مقایسهٔ نام تابع است
تا `functools.wraps`/بازنویسی آینده گیت را نشکند.

# نکتهٔ FastAPI 0.163

در این نسخه `app.include_router(...)` دیگر routeها را بازنویسی نمی‌کند؛
یک `_IncludedRouter` با `include_context.included_router` و `prefix` باقی
می‌ماند. پس `app.routes` به‌تنهایی فقط ۷ آیتم دارد و پیمایش بازگشتی لازم است.
این را با شمارش مسیرها می‌سنجیم (۱۲۸ مسیر با prefix واقعی).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# مسیرهای عمومی — هر ورودی باید دلیل داشته باشد. افزودن مسیر عمومیِ بی‌دلیل
# همان چیزی است که این گیت باید جلویش را بگیرد، پس فهرست کوچک می‌ماند.
PUBLIC: dict[tuple[str, str], str] = {
    ("POST", "/api/v1/auth/otp/request"): "ورود: هنوز توکنی ندارد (سقف نرخ دارد)",
    ("POST", "/api/v1/auth/otp/verify"): "ورود: تولید توکن (سقف نرخ دارد)",
    ("POST", "/api/v1/auth/refresh"): "تعویض refresh token — اعتبار با خود توکن است",
    ("POST", "/api/v1/auth/logout"): "ابطال refresh token — اعتبار با خود توکن است",
    ("GET", "/api/v1/updates/manifest"): "کلاینت پیش از ورود نسخه را می‌پرسد",
    ("GET", "/api/v1/health/ready"): "probe زیرساخت",
    ("GET", "/api/v1/metrics"): "scrape پرومتئوس",
    ("GET", "/health"): "probe زیرساخت",
}

# مسیرهایی که *عمداً* عمومی‌اند ولی در آینده باید بسته شوند — جدا نگه می‌داریم
# تا در گزارش به‌عنوان بدهی فنی دیده شوند، نه اینکه با بقیه قاطی شوند.
KNOWN_DEBT: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/metrics"): "متریک‌ها بدون احراز هویت — باید در شبکهٔ داخلی محدود شود",
}


def _walk(routes, prefix: str = ""):
    from fastapi.routing import APIRoute

    for r in routes:
        if isinstance(r, APIRoute):
            yield prefix, r
            continue
        ctx = getattr(r, "include_context", None)
        sub = getattr(r, "original_router", None) or getattr(ctx, "included_router", None)
        if sub is not None:
            yield from _walk(sub.routes, prefix + (getattr(ctx, "prefix", "") or ""))


def _guard_kinds(dependant, out: set[str] | None = None) -> set[str]:
    out = out if out is not None else set()
    kind = getattr(dependant.call, "__rbac__", None)
    if kind:
        out.add(kind)
    for d in dependant.dependencies:
        _guard_kinds(d, out)
    return out


def collect_routes(app) -> list[tuple[str, str, set[str]]]:
    rows = []
    for prefix, r in _walk(app.routes):
        kinds: set[str] = set()
        _guard_kinds(r.dependant, kinds)
        for method in sorted(r.methods):
            rows.append((method, prefix + r.path, kinds))
    return rows


def evaluate(rows: list[tuple[str, str, set[str]]]) -> tuple[list[str], list[str]]:
    """قواعد جدا از main تا تست بتواند آن‌ها را روی یک اپ ساختگی بسنجد."""
    problems = [
        f"بدون guard: {m} {p}" for m, p, kinds in rows if not kinds and (m, p) not in PUBLIC
    ]
    stale = [
        f"{m} {p} حالا guard دارد ({','.join(sorted(kinds))})"
        for m, p, kinds in rows
        if kinds and (m, p) in PUBLIC
    ]
    return problems, stale


def main() -> int:
    # اسکریپت از `scripts/` اجرا می‌شود؛ ریشهٔ بک‌اند باید روی sys.path باشد
    # وگرنه `import engine` (پکیج هم‌سطح) پیدا نمی‌شود.
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("MP_DATABASE_URL", "sqlite:////tmp/route-guard-gate.db")
    from app.main import create_app

    rows = collect_routes(create_app())
    # قواعد در `evaluate` است: هم هر مسیر ناشناختهٔ بدون guard را می‌گیرد،
    # هم برعکسش — اگر مسیری از PUBLIC حالا guard پیدا کند، فهرست PUBLIC
    # «مرده» شده و باید پاک شود (وگرنه به‌تدریج دروغ می‌گوید).
    problems, stale = evaluate(rows)

    print(
        f"مسیرها: {len(rows)} | دارای guard: {sum(1 for r in rows if r[2])} | عمومی: {len(PUBLIC)}"
    )
    if problems or stale:
        for p in problems + stale:
            print("✗", p)
        return 1
    print("✓ همهٔ مسیرها guard دارند یا عمومیِ مستند هستند")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
