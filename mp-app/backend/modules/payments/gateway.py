"""adapter پرداخت (M16، بازنویسی فاز ۳) — بانک صندباکس محلی + Mock.

درگاه اینترنتی (زرین‌پال/آیدی‌پی) از ۲۰۲۶-۱۱-۱۹ حذف شد: روش پرداخت محصول
نقدی، کارت‌خوان و کارت‌به‌کارت با رسید است. آداپتر صندباکس فقط به‌عنوان
ابزار آزمایش محلی می‌ماند و در production قابل انتخاب نیست.

G8-مالی: مبلغ/وضعیت فقط از DB و پاسخ امضاشدهٔ درگاه — هرگز از ورودی کاربر پس از آغاز تراکنش.
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import secrets
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


@dataclass
class GatewayRefundResult:
    """نتیجهٔ بازگشت وجه — M110. `already` یعنی بانک قبلاً همین تراکنش را برگردانده."""

    ok: bool
    reference_id: str = ""
    already: bool = False


class GatewayAdapter(Protocol):
    def start(
        self, amount_rial: int, description: str, callback_url: str
    ) -> GatewayStartResult: ...

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult: ...


# ── M110: بانک صندباکسِ محلی (devtools/sandbox_bank.py) ────────────────────────────
# چرا یک adapter و نه یک mockِ درون‌پروسه‌ای: MockGateway هرگز «هدایت به بانک»، «امضای
# callback»، «مهلتِ انقضای authority» و «تأخیر/خطای HTTP شبکه» را نمی‌بیند. این مسیر
# قرارداد درگاه‌های واقعی را محلی تقلید می‌کند، پس جابه‌جایی به درگاه واقعی فقط عوض‌کردن
# `MP_PAYMENT_GATEWAY` است — نه بازنویسی جریان.
_SANDBOX_OK_VERIFY = {100: "ok", 101: "already_verified"}
_SANDBOX_OK_REFUND = {255: "ok", 254: "already_refunded"}
_SANDBOX_MESSAGES = {
    102: "amount_mismatch",
    103: "not_paid_at_bank",
    -1: "authority_not_found",
}


class SandboxBankAdapter:
    """هم‌خوانی HTTP با بانک صندباکس — شروع، تأیید، بازگشت وجه (M110)."""

    def __init__(
        self,
        base_url: str,
        merchant_id: str = "SANDBOX-MERCHANT",
        timeout: float = 5.0,
        http_client=None,
    ):
        """`http_client` فقط برای آزمون: با `TestClient(بانک)` همان سرویس درون‌پروسه
        اجرا می‌شود تا suite به پورت/شبکه نیاز نداشته باشد — و مسیر HTTP (فرم،
        redirect، کد وضعیت، بدنهٔ JSON) همان مسیری است که production می‌رود."""
        self.base_url = base_url.rstrip("/")
        self.merchant_id = merchant_id
        self.timeout = timeout
        self._http_client = http_client

    @contextlib.contextmanager
    def _client(self):
        if self._http_client is not None:
            yield self._http_client
            return
        import httpx

        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"X-Sandbox-Bank": "1"},
        ) as client:
            yield client

    @staticmethod
    def _status(payload: dict) -> int:
        try:
            return int((payload or {}).get("result", {}).get("status", -1))
        except (TypeError, ValueError):
            return -1

    def start(self, amount_rial: int, description: str, callback_url: str) -> GatewayStartResult:
        import httpx

        try:
            with self._client() as client:
                resp = client.post(
                    "/api/v1/purchase",
                    json={
                        "merchant_id": self.merchant_id,
                        "amount": amount_rial,
                        "description": description,
                        "callback_url": callback_url,
                    },
                )
                resp.raise_for_status()
                payload = resp.json()
        except (httpx.HTTPError, OSError, ValueError) as exc:  # شبکه = نامعلوم، نه «ناموفق»
            raise PaymentGatewayError(
                "بانک صندباکس در دسترس نیست", code="gateway_unreachable"
            ) from exc
        authority = (payload.get("data") or {}).get("authority") or ""
        if not authority:
            raise PaymentGatewayError("آغاز پرداخت ناموفق بود", code="start_failed")
        return GatewayStartResult(
            authority=authority, redirect_url=f"{self.base_url}/pay/{authority}"
        )

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult:
        status, data = self._post_verify("/api/v1/verify", authority, amount_rial)
        if status in _SANDBOX_OK_VERIFY:
            return GatewayVerifyResult(
                ok=True,
                reference_id=str(data.get("ref_id", "")),
                card_pan=str(data.get("card_pan", "")),
            )
        code = _SANDBOX_MESSAGES.get(status, f"verify_{status}")
        reason = (data.get("message") or "") if isinstance(data, dict) else ""
        raise PaymentGatewayError(reason or "تأیید درگاه ناموفق بود", code=code)

    def refund(self, authority: str, amount_rial: int) -> GatewayRefundResult:
        status, data = self._post_verify("/api/v1/refund", authority, amount_rial)
        if status == 255:
            return GatewayRefundResult(ok=True, reference_id=str(data.get("ref_id", "")))
        if status == 254:
            return GatewayRefundResult(
                ok=False, already=True, reference_id=str(data.get("ref_id", ""))
            )
        code = _SANDBOX_MESSAGES.get(status, f"refund_{status}")
        raise PaymentGatewayError(str(data.get("message") or "بازگشت وجه ناموفق بود"), code=code)

    def _post_verify(self, path: str, authority: str, amount_rial: int) -> tuple[int, dict]:
        import httpx

        try:
            with self._client() as client:
                resp = client.post(
                    path,
                    json={
                        "merchant_id": self.merchant_id,
                        "authority": authority,
                        "amount": amount_rial,
                    },
                )
                if resp.status_code >= 500:
                    # ۵۰x یعنی بانک لحظه‌ای خراب است؛ «نامعتبر» نیست. تفاوت همین‌جا
                    # تعیین می‌کند پرداخت pending بماند و بعداً تأیید شود.
                    raise PaymentGatewayError(
                        "بانک صندباکس خطای سرویس داد", code="gateway_unavailable"
                    )
                payload = resp.json() if resp.content else {}
        except (httpx.HTTPError, OSError, ValueError) as exc:
            raise PaymentGatewayError(
                "ارتباط با بانک صندباکس قطع شد", code="gateway_unreachable"
            ) from exc
        if not isinstance(payload, dict):
            raise PaymentGatewayError("پاسخ بانک نامفهوم است", code="gateway_bad_response")
        data = payload.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("message", str((payload.get("result") or {}).get("message", "")))
        return self._status(payload), data


class MockGateway:
    """درگاه تست — deterministic برای dev/e2e (D-008).

    نکتهٔ مهم (باگ تولیدی): نسخهٔ قبلی authorityها را در یک دیکشنری
    **درون‌حافظه** نگه می‌داشت. با uvicorn `--workers 4` هر درخواست در
    پروسهٔ دیگری اجرا می‌شود، پس `start` در worker A و `verify` در worker B
    ⇒ «تراکنش یافت نشد» با وجود پرداخت کاملاً معتبر. همان اتفاق با هر
    کِش محلی در production هم می‌افتد.

    حالا اعتبار authority از **خودِ authority** می‌آید: شناسه شامل مبلغ و
    امضای HMAC با کلید سرور است، پس verify آماری/بی‌اثر است و به حافظهٔ
    پروسه وابسته نیست.
    """

    def _sign(self, authority: str, amount_rial: int) -> str:
        return hmac.new(
            settings.secret_key.encode(),
            f"{authority}:{amount_rial}".encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

    def start(self, amount_rial: int, description: str, callback_url: str) -> GatewayStartResult:
        unique = secrets.token_hex(4)
        authority = f"MOCK-{amount_rial:x}-{unique}"
        return GatewayStartResult(
            authority=authority, redirect_url=f"mock://gateway/pay/{authority}"
        )

    def verify(self, authority: str, amount_rial: int) -> GatewayVerifyResult:
        # قالب: MOCK-<hex amount>-<8 hex>
        try:
            prefix, amount_hex, _unique = authority.split("-")
            issued_amount = int(amount_hex, 16)
        except (ValueError, AttributeError) as exc:
            raise PaymentGatewayError("authority نامعتبر", code="authority_not_found") from exc
        if prefix != "MOCK" or issued_amount != amount_rial:
            raise PaymentGatewayError("مبلغ ناسازگار", code="amount_mismatch")
        return GatewayVerifyResult(
            ok=True,
            reference_id=f"MOCKREF-{self._sign(authority, amount_rial)}",
            card_pan="6037-**-**-1234",
        )


def signed_token(payment_id: int, amount_rial: int) -> str:
    """امضای HMAC برای callback — جلوگیری از جعل مبلغ (G8-مالی)."""
    msg = f"{payment_id}:{amount_rial}".encode()
    return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()[:32]


def verify_token(payment_id: int, amount_rial: int, token: str) -> bool:
    return hmac.compare_digest(signed_token(payment_id, amount_rial), token)


_mock = MockGateway()


def get_gateway() -> GatewayAdapter:
    """Select the configured gateway; never downgrade a bad config to MockGateway."""
    if settings.payment_gateway == "mock":
        if settings.environment == "production":
            raise PaymentGatewayError(
                "درگاه آزمایشی در production غیرفعال است", code="gateway_not_configured"
            )
        return _mock
    if settings.payment_gateway == "sandbox":
        if settings.environment == "production":
            raise PaymentGatewayError(
                "بانک صندباکس در production غیرفعال است", code="gateway_not_configured"
            )
        if not settings.sandbox_bank_url:
            raise PaymentGatewayError(
                "نشانی بانک صندباکس تنظیم نشده (MP_SANDBOX_BANK_URL)", code="gateway_not_configured"
            )
        return SandboxBankAdapter(settings.sandbox_bank_url, settings.sandbox_bank_merchant_id)
    if settings.payment_gateway == "manual":
        # تصمیم مالک ۲۰۲۶-۱۱-۱۹: درگاه اینترنتی حذف شد. این خط مرز است: هیچ
        # مسیری نباید بی‌صدا به درگاه آنلاین برگردد.
        raise PaymentGatewayError(
            "درگاه پرداخت اینترنتی حذف شده است؛ پرداخت حضوری و کارت‌به‌کارت با رسید",
            code="online_gateway_removed",
        )
    raise PaymentGatewayError("حالت پرداخت پشتیبانی نمی‌شود", code="gateway_not_configured")
