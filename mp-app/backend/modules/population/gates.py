"""گیت جمعیتی (E05/D-016) — مسیر فاقد پشتوانه آشکارا غیرقابل تولید خودکار می‌ماند.

قاعدهٔ بسته: «مسیر فاقد پشتوانه، با هشدار متنی روی برنامهٔ عمومی پوشانده نشود» —
تولید باید **متوقف** شود، نه «عمومی + هشدار».
"""

from __future__ import annotations

from app.errors import ApiError

# وضعیت‌ها: supported_with_protocol | gated_no_auto_generation | needs_professional_review
POPULATION_PATHS: dict[str, dict[str, str]] = {
    "adult": {
        "name_fa": "بزرگسال (۱۸+)",
        "status": "supported_with_protocol",
        "reason": "پشتیبانی فاز اول (D-016) — قواعد rules-1.0",
    },
    "senior_healthy": {
        "name_fa": "سالمند سالم",
        "status": "supported_with_protocol",
        "reason": "پشتیبانی با پروتکل ایمنی ساده (D-016): بار کمتر، بدون تست بیشینه، معیار توقف",
    },
    "youth": {
        "name_fa": "کودک/نوجوان",
        "status": "gated_no_auto_generation",
        "reason": "شواهد/قواعد معتبر مسیر ثبت نشده — تولید خودکار متوقف (E05)؛ برنامهٔ کودک نسخهٔ کوچک‌شدهٔ بزرگسال نیست",
    },
    "pregnancy_postpartum": {
        "name_fa": "بارداری/پس از زایمان",
        "status": "gated_no_auto_generation",
        "reason": "نیازمند قواعد/نظارت حرفه‌ای — تولید خودکار متوقف (E05)",
    },
    "disability": {
        "name_fa": "معلولیت",
        "status": "gated_no_auto_generation",
        "reason": "نیازمند پروتکل تطبیقی معتبر — تولید خودکار متوقف (E05)",
    },
    "disease": {
        "name_fa": "بیماری",
        "status": "needs_professional_review",
        "reason": "فقط با تأیید/نظارت متخصص — خودکار ممنوع (E04/E05)",
    },
    "return_from_injury": {
        "name_fa": "بازگشت از آسیب",
        "status": "needs_professional_review",
        "reason": "فقط با مجوز/نظارت حرفه‌ای — خودکار ممنوع",
    },
    "elite": {
        "name_fa": "ورزش نخبه",
        "status": "gated_no_auto_generation",
        "reason": "نیازمند تقویم مسابقه/periodization تخصصی — خودکار متوقف",
    },
}


def assert_generation_allowed(path: str) -> dict:
    """گیت صریح: مسیر غیرفعال ← ApiError با توضیح — نه برنامهٔ عمومی + هشدار."""
    info = POPULATION_PATHS.get(path)
    if info is None:
        raise ApiError(f"مسیر جمعیتی ناشناخته: {path}", code="unknown_population_path")
    if info["status"] != "supported_with_protocol":
        raise ApiError(
            f"تولید خودکار برنامه برای «{info['name_fa']}» متوقف است — {info['reason']}",
            code="population_path_gated",
        )
    return info
