"""ثبت معادلات ترکیب بدن — E07/D-012: هیچ معادله‌ای بدون مرجع مستقلِ تأییدشده اجرا نمی‌شود.

قاعدهٔ سخت: ضرایب از حافظهٔ مدل تولید/اجرا نمی‌شوند. برای فعال‌سازی، یک رکورد در
`APPROVED_EQUATIONS` با شناسهٔ مرجع مستقل + دامنهٔ جمعیتی + حقوق ثبت و تأیید شود.
هم‌اکنون: **ثبتیهٔ خالی** — همهٔ محاسبات قفل‌اند (D-012).
"""

from __future__ import annotations

from app.errors import ApiError

# ساختار موردنیاز هر رکورد تأییدشده (الان هیچ رکوردی نیست):
# "jp7-siri-v1": {
#     "source": "مرجع مستقل + صفحه/ویرایش",
#     "population": "بزرگسال سالم ...",
#     "rights": "وضعیت حقوق",
#     "approved_by": "کاربر/متخصص",
#     "approved_at": "تاریخ",
# }
APPROVED_EQUATIONS: dict[str, dict[str, str]] = {}

LOCKED_VERSION = "LOCKED:pending-independent-reference"


def jp7_body_fat(
    skinfolds_mm: dict[str, float],
    age: int,
    gender: str,
    *,
    equation_id: str,
) -> float:
    """محاسبهٔ درصد چربی — فقط با `equation_id` تأییدشده در ثبتیه؛ وگرنه قفل."""
    if equation_id not in APPROVED_EQUATIONS:
        raise ApiError(
            "محاسبهٔ درصد چربی قفل است — معادله/ضرایب تا ثبت مرجع مستقل تأیید نمی‌شود (E07/D-012)",
            code="equation_locked",
        )
    raise ApiError("پیاده‌سازی معادلهٔ تأییدشده هنوز وارد نشده", code="equation_not_implemented")


def validate_jp7_raw(skinfolds_mm: dict[str, float], gender: str) -> dict[str, float]:
    """اعتبارسنجی دادهٔ خام (مستقل از معادله) — ورودی نامعتبر هرگز ذخیره/محاسبه نمی‌شود."""
    sites = ("chest", "triceps", "subscapular", "suprailiac", "abdomen", "thigh", "calf")
    try:
        clean = {site: float(skinfolds_mm[site]) for site in sites}
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(f"چین‌های پوستی ناقص‌اند — نیاز به {sites}", code="invalid_skinfolds") from exc
    if any(v < 0 or v > 100 for v in clean.values()):
        raise ApiError("قرائت mm باید در بازهٔ ۰ تا ۱۰۰ باشد", code="invalid_skinfolds")
    if sum(clean.values()) <= 0:
        raise ApiError("مجموع چین‌ها باید مثبت باشد", code="invalid_skinfolds")
    if gender not in ("male", "female"):
        raise ApiError("برای JP7 باید جنسیت male یا female باشد", code="invalid_gender")
    return clean
