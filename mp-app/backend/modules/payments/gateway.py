"""adapter درگاه پرداخت (M16) — الگوی Gateway + Zarinpal (سند اجرا) + Mock.

G8-مالی: مبلغ/وضعیت فقط از DB و پاسخ امضاشدهٔ درگاه — هرگز از ورودی کاربر پس از آغاز تراکنش.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol

from app.config import settings


class PaymentGatewayError(Exception):
    """خطای درگاه — پیام برای کاربر عمومی نگه داشته می‌شود."""

    def __init__(self, message: str = "پرداخت درگاه ناموفق بود", code: str = "gateway_error"):
        super().__init__(message)
        self.code = code


@dataclass
class GatewayStartResult:
    authority: str  # شناسهٔ تراکنش درگاه
    redirect_url: str  # آدرس درگاه برای هدایت کاربر


@dataclass
class GatewayVerifyResult:
    ok: bool
    reference_id: str  # کد پیگیری بانک
    card_pan: str = ""  # ماسک‌شده


class GatewayAdapter(Protocol):
    def start(
        self, amount_rial: int, description: str, callback_url: str
    ) -> GatewayStartResult: ...

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult: ...


class MockGateway:
    """درگاه تست — deterministic برای dev/e2e (D-008)."""

    def __init__(self):
        self._issued: dict[str, int] = {}  # authority → amount

    def start(self, amount_rial: int, description: str, callback_url: str) -> GatewayStartResult:
        authority = (
            f"MOCK-{hashlib.sha256(f'{amount_rial}:{description}'.encode()).hexdigest()[:12]}"
        )
        self._issued[authority] = amount_rial
        return GatewayStartResult(
            authority=authority, redirect_url=f"mock://gateway/pay/{authority}"
        )

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult:
        if authority not in self._issued:
            raise PaymentGatewayError("تراکنش یافت نشد", code="authority_not_found")
        if self._issued[authority] != amount_rial:
            raise PaymentGatewayError("مبلغ ناسازگار", code="amount_mismatch")
        del self._issued[authority]
        return GatewayVerifyResult(
            ok=True, reference_id=f"MOCKREF-{authority[5:]}", card_pan="6037-**-**-1234"
        )


class ZarinpalAdapter:
    """درگاه زرین‌پال — REST (سند اجرا؛ در production با تنظیمات واقعی اجرا می‌شود)."""

    BASE = "https://api.zarinpal.com/pg/v4"

    def __init__(self, merchant_id: str, sandbox: bool = True):
        self.merchant_id = merchant_id
        if sandbox:
            self.BASE = "https://sandbox.zarinpal.com/pg/v4"

    def start(self, amount_rial: int, description: str, callback_url: str) -> GatewayStartResult:
        import httpx

        resp = httpx.post(
            f"{self.BASE}/payment/request.json",
            json={
                "merchant_id": self.merchant_id,
                "amount": amount_rial,  # ریال
                "description": description,
                "callback_url": callback_url,
            },
            timeout=10,
        )
        data = resp.json().get("data", {})
        authority = data.get("authority")
        if not authority:
            raise PaymentGatewayError("آغاز پرداخت ناموفق بود", code="start_failed")
        return GatewayStartResult(
            authority=authority,
            redirect_url=f"https://sandbox.zarinpal.com/pg/StartPay/{authority}",
        )

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult:
        import httpx

        resp = httpx.post(
            f"{self.BASE}/payment/verify.json",
            json={"merchant_id": self.merchant_id, "amount": amount_rial, "authority": authority},
            timeout=10,
        )
        data = resp.json().get("data", {})
        code = data.get("code")
        if code not in (100, 101):  # 100=OK, 101=قبلاً تأیید شده
            raise PaymentGatewayError("تأیید درگاه ناموفق بود", code=f"verify_{code}")
        return GatewayVerifyResult(
            ok=True,
            reference_id=str(data.get("ref_id", "")),
            card_pan=str(data.get("card_pan", "")),
        )


def signed_token(payment_id: int, amount_rial: int) -> str:
    """امضای HMAC برای callback — جلوگیری از جعل مبلغ (G8-مالی)."""
    msg = f"{payment_id}:{amount_rial}".encode()
    return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()[:32]


def verify_token(payment_id: int, amount_rial: int, token: str) -> bool:
    return hmac.compare_digest(signed_token(payment_id, amount_rial), token)


_mock = MockGateway()


def get_gateway() -> GatewayAdapter:
    """انتخاب درگاه از تنظیمات — پیش‌فرض: mock در dev."""
    if settings.payment_gateway == "zarinpal" and settings.zarinpal_merchant_id:
        return ZarinpalAdapter(settings.zarinpal_merchant_id, sandbox=settings.payment_sandbox)
    return _mock
