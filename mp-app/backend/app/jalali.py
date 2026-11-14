"""تبدیل تقویم میلادی ↔ جلالی — لایهٔ نمایش (تاریخ‌ها در API/ذخیره ISO می‌مانند).

الگوریتم: تبدیل مستقیم ریاضی (بدون وابستگی) — deterministic و تست‌شده.
"""

from __future__ import annotations

from datetime import date


def to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    """میلادی → جلالی (سال، ماه، روز)."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd


def to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """جلالی → میلادی (سال، ماه، روز)."""
    jy += 1595
    days = -355668 + (365 * jy) + ((jy // 33) * 8) + (((jy % 33) + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += ((jm - 7) * 30) + 186
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    months = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    for i in range(1, 13):
        if gd <= months[i]:
            gm = i
            break
        gd -= months[i]
    return gy, gm, gd


_JALALI_MONTHS = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)


def format_jalali(d: date, *, with_month_name: bool = True) -> str:
    """نمایش فارسی یک تاریخ میلادی به جلالی — فقط لایهٔ نمایش."""
    jy, jm, jd = to_jalali(d.year, d.month, d.day)
    if with_month_name:
        return f"{jd} {_JALALI_MONTHS[jm - 1]} {jy}"
    return f"{jy:04d}/{jm:02d}/{jd:02d}"
