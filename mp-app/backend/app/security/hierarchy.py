"""سلسله‌مراتب نقش‌ها — منبع یگانهٔ «چه کسی از چه کسی بالاتر است».

چرا این ماژول لازم شد (یافتهٔ ۲۰۲۶-۱۱-۱۵):

    casbin برای `admin` و `super_admin` هر دو `("/*", "*")` داشت. یعنی
    «مدیر» و «مالک» از نظر ماشین **یکی** بودند: هر ادمینی می‌توانست قیمت
    بگذارد، درگاه اضافه کند و — بدتر — با `ASSIGNABLE_ROLES` شامل
    `super_admin`، **مالک جدید بسازد**. سلسله‌مراتب فقط در متن کد بود،
    در سیاست نه.

این ماژول فقط «رتبه» را می‌داند؛ تصمیم دسترسی همچنان در `rbac` و
`require_rank` گرفته می‌شود. رتبهٔ بالاتر هرگز از رتبهٔ پایین‌تر قابل
دسترس نیست (قاعدهٔ کاربر: «هیچ سطحی به سطح بالاتر نمی‌رسد»).
"""

from __future__ import annotations

from app.errors import ForbiddenError

# رتبه = عدد بزرگ‌تر، اختیار بیشتر. این ترتیب *قرارداد* است، نه ترجیح.
ROLE_RANK: dict[str, int] = {
    "member": 10,
    "reception": 20,
    "coach": 30,
    "manager": 40,
    "admin": 50,
    "super_admin": 100,
}

# نقش‌هایی که کادر محسوب می‌شوند (پشت میز / پنل).
STAFF_ROLES = frozenset({"reception", "coach", "manager", "admin", "super_admin"})

# مجموعه‌ای که فقط مالک سیستم می‌تواند اعطا کند — `super_admin` عمداً **نیست**
# (اعطای مالکیت دوم باید خارج از API و با تصمیم انسانی باشد، وگرنه یک
# حساب هک‌شده یعنی دو مالک).
OWNER_ASSIGNABLE_ROLES = frozenset({"member", "reception", "coach", "manager", "admin"})

# نقش‌ها با اختیار اقتصادی: قیمت‌گذاری، ساخت محصول، درگاه، شمارهٔ کارت.
COMMERCE_ROLES = frozenset({"super_admin"})


def rank_of(role: str | None) -> int:
    """رتبهٔ نقش؛ نقش ناشناخته = ۰ (پایین‌تر از همه، نه خطا — fail-closed)."""
    return ROLE_RANK.get(role or "", 0)


def outranks(actor_role: str | None, target_role: str | None) -> bool:
    """آیا `actor` بالاتر از `target` است؟ برابر بودن = خیر."""
    return rank_of(actor_role) > rank_of(target_role)


def ensure_can_manage(actor_role: str | None, target_role: str | None) -> None:
    """قاعدهٔ یک‌طرفه: پایین‌تر هرگز بالاتر را مدیریت نمی‌کند."""
    if not outranks(actor_role, target_role):
        raise ForbiddenError(f"سطح «{actor_role}» اجازهٔ مدیریت سطح «{target_role}» را ندارد")


def ensure_owner(actor_role: str | None, what: str = "این عملیات") -> None:
    """عملیات اقتصادی/زیرساختی — فقط مالک سیستم."""
    if (actor_role or "") not in COMMERCE_ROLES:
        raise ForbiddenError(f"{what} فقط با تأیید مالک سیستم (super_admin) انجام می‌شود")
