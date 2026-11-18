"""شبیه‌ساز درگاه پرداخت — «بانک صندباکس» (M110).

چرا این فایل وجود دارد
----------------------
تا پیش از این، دو راه برای آزمودن پرداخت داشتی: `MockGateway` که همه‌چیز را در همان
پروسهٔ خودمان می‌سازد (پس هرگز «هدایت به بانک»، «امضای callback» و «تأخیر شبکه» را
نمی‌بیند)، یا درگاه واقعی با شناسهٔ پذیرندهٔ واقعی (که پول واقعی است). این فایل
راه سوم را می‌دهد: یک سرویس HTTP مستقل، رایگان، آفلاین، با همان **قرارداد** درگاه‌های
ایرانی — درخواست → `authority` → هدایت کاربر → بازگشت با `Authority` و امضا → `verify`
یک‌بارمصرف → `refund`. همان چیزی که بعداً با یک درگاه واقعی جابه‌جا می‌شود، این‌جا
محلی آزموده می‌شود؛ نه با بدلِ درون‌پروسه‌ای.

اجرا (دو پنجره، بدون هیچ حسابی):

    cd mp-app/backend
    uvicorn devtools.sandbox_bank:app --port 8088                 # بانک
    MP_PAYMENT_GATEWAY=sandbox MP_SANDBOX_BANK_URL=http://127.0.0.1:8088 \\
      uvicorn app.main:app --port 8000                            # اپ ما

بعد در مرورگر: مسیر `redirect_url` که `/payments/{id}/start` برمی‌گرداند را باز کن،
دکمهٔ «پرداخت» را بزن، و ببین callback می‌آید و وضعیت `paid` می‌شود.

قرارداد (عمداً شبیه زرین‌پالِ v4 نوشته شده تا جابه‌جایی مکانیکی باشد)
--------------------------------------------------------------------
- `POST /api/v1/purchase` → `{"data":{"authority": "...", "valid_for": 600}}`
- `GET  /pay/{authority}` → صفحهٔ RTL قابل‌کلیک (موفق / انصراف / موجودی ناکافی)
- `POST /api/v1/verify`  → `code` ۱۰۰ بار اول، ۱۰۱ بار دوم (یک‌بارمصرف)، ۱۰۲ مبلغ
  ناسازگار، ۱۰۳ پرداخت‌نشده، `-۱` نامعتبر/منقضی
- `POST /api/v1/refund`  → ۲۵۵ بازگشت انجام‌شد، ۲۵۴ قبلاً برگشت خورده
- بازگشت به تاجر با `?Authority=…&Amount=…&Sign=…` که `Sign` امضای HMAC است؛ اگر
  امضا نخورد، پرداخت تأیید نمی‌شود (همان درسی که G8-مالی گرفته است).

این شبیه‌ساز **عمداً** هیچ داده‌ای از کاربر واقعی نمی‌خواهد و هیچ مقدار حساسی در
کدش نیست؛ کلید پیش‌فرضش یک رشتهٔ بی‌معنی است که باید با متغیر محیطی عوض شود تا
امضای callback هم معنی «آزمون» بدهد، نه «تصادفی».
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass, field
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# ۳۰۲ نه ۳۰۷: بانک‌های واقعی کاربر را با GET برمی‌گردانند؛ ۳۰۷ بودنهٔ متدِ POST
# است و فرمِ نتیجه را به merchant دوباره POST می‌کند — هیچ درگاهی این‌طور کار نمی‌کند.
from pydantic import BaseModel, Field

BANK_SECRET = os.environ.get("SANDBOX_BANK_SECRET", "sandbox-shared-secret-not-a-real-key")
BANK_MERCHANT_ID = os.environ.get("SANDBOX_MERCHANT_ID", "SANDBOX-MERCHANT")
DEFAULT_TTL_SECONDS = int(os.environ.get("SANDBOX_BANK_TTL", "600"))
MASKED_PAN = "603799**" + "****1234"

app = FastAPI(
    title="MP Sandbox Bank",
    version="1.0",
    description="شبیه‌ساز محلی درگاه پرداخت — فقط برای توسعه و آزمون (M110).",
    docs_url="/docs",
)


def _sign(authority: str, amount_rial: int) -> str:
    """امضای بازگشت به تاجر — همان کاری که بانک واقعی با `Authority`+`Amount` می‌کند."""
    return hmac.new(
        BANK_SECRET.encode(), f"{authority}:{amount_rial}".encode(), hashlib.sha256
    ).hexdigest()[:32]


def _check_sign(authority: str, amount_rial: int, sign: str) -> bool:
    return hmac.compare_digest(_sign(authority, amount_rial), sign or "")


@dataclass
class Txn:
    authority: str
    amount_rial: int
    description: str
    callback_url: str
    created_at: float
    ttl_seconds: int
    delay_seconds: float = 0.0
    http_error: int = 0
    state: str = "opened"  # opened | paid | failed | cancelled
    verified: bool = False
    refund_id: str = ""
    ref_id: str = field(default="")

    @property
    def expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds


_LEDGER: dict[str, Txn] = {}


def _reset() -> None:  # pragma: no cover - helper برای آزمون‌ها
    _LEDGER.clear()


class PurchaseIn(BaseModel):
    merchant_id: str = Field(default=BANK_MERCHANT_ID, max_length=64)
    amount: int = Field(gt=0, le=10_000_000_000, description="مبلغ به ریال")
    description: str = Field(default="", max_length=200)
    callback_url: str = Field(default="", max_length=500)
    ttl_seconds: int = Field(default=DEFAULT_TTL_SECONDS, ge=0, le=3600)
    # دو اهرم برای آزمودن مسیر خطای سمت ما — در بانک واقعی وجود ندارند
    delay_seconds: float = Field(default=0.0, ge=0, le=2.0)
    http_error: int = Field(default=0, ge=0, le=1)


class AuthorityIn(BaseModel):
    merchant_id: str = Field(default=BANK_MERCHANT_ID, max_length=64)
    authority: str = Field(min_length=4, max_length=64)
    amount: int = Field(gt=0, le=10_000_000_000)


@app.get("/", response_class=HTMLResponse, summary="فهرست تراکنش‌ها (میزبانِ آزمون)")
def index() -> str:
    rows = (
        "".join(
            f"<tr><td><code>{t.authority}</code></td><td>{t.amount_rial}</td>"
            f"<td>{t.state}{'/verified' if t.verified else ''}{'/refunded' if t.refund_id else ''}</td>"
            f"<td>{'منقضی' if t.expired else 'زنده'}</td>"
            f"<td><a href='/pay/{t.authority}'>باز کردن صفحهٔ پرداخت</a></td></tr>"
            for t in reversed(list(_LEDGER.values()))
        )
        or "<tr><td colspan=5>هنوز تراکنشی ساخته نشده.</td></tr>"
    )
    return (
        "<!doctype html><html dir=rtl lang=fa><meta charset=utf-8>"
        "<style>body{font-family:system-ui;max-width:920px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:.5rem;text-align:right}"
        "</style><h1>بانک صندباکس — تراکنش‌ها</h1>"
        "<table><tr><th>authority</th><th>مبلغ (ریال)</th><th>وضعیت</th><th>مهلت</th><th></th></tr>"
        f"{rows}</table><p><a href='/docs'>API docs</a></p></html>"
    )


@app.get("/healthz", summary="سلامتی")
def healthz() -> dict:
    return {"ok": True, "merchant_id": BANK_MERCHANT_ID, "txns": len(_LEDGER)}


@app.post("/api/v1/purchase", summary="ساخت authority")
def purchase(payload: PurchaseIn) -> dict:
    if payload.merchant_id != BANK_MERCHANT_ID:
        raise HTTPException(status_code=401, detail="شناسهٔ پذیرندهٔ ناشناخته")
    authority = secrets.token_hex(8)
    _LEDGER[authority] = Txn(
        authority=authority,
        amount_rial=payload.amount,
        description=payload.description,
        callback_url=payload.callback_url,
        created_at=time.time(),
        ttl_seconds=payload.ttl_seconds,
        delay_seconds=payload.delay_seconds,
        http_error=payload.http_error,
    )
    return {
        "result": {"status": 100},
        "data": {"authority": authority, "valid_for": payload.ttl_seconds},
    }


def _page(txn: Txn) -> str:
    buttons = "".join(
        f"<form method=post action='/pay/{txn.authority}'><button name=outcome value='{v}'>{label}</button></form>"
        for v, label in (
            ("success", "پرداخت موفق"),
            ("cancel", "انصراف کاربر"),
            ("insufficient", "موجودی ناکافی"),
        )
    )
    note = (
        "<p style='color:#b00020'>این `authority` منقضی شده است؛ بانک دیگر اجازهٔ پرداخت نمی‌دهد.</p>"
        if txn.expired
        else ""
    )
    return (
        "<!doctype html><html dir=rtl lang=fa><meta charset=utf-8>"
        "<style>body{font-family:system-ui;max-width:520px;margin:3rem auto;padding:0 1rem}"
        "button{width:100%;padding:.9rem;margin:.4rem 0;border-radius:12px;border:1px solid #bbb;background:#fff;font-size:1rem}"
        "code{background:#f4f4f4;padding:.1rem .3rem;border-radius:4px}</style>"
        f"<h1>درگاه پرداخت (آزمایشی)</h1><p>مبلغ: <b>{txn.amount_rial:,}</b> ریال</p>"
        f"<p>شرح: {txn.description or '—'}</p><p>authority: <code>{txn.authority}</code></p>{note}"
        f"{buttons}</html>"
    )


@app.get("/pay/{authority}", response_class=HTMLResponse, summary="صفحهٔ پرداخت برای کلیک انسان")
def pay_page(authority: str) -> str:
    txn = _LEDGER.get(authority)
    if txn is None:
        raise HTTPException(status_code=404, detail="authority نامعتبر")
    return _page(txn)


@app.post("/pay/{authority}", summary="ثبت نتیجهٔ پرداخت از صفحهٔ بانک")
def pay_action(authority: str, outcome: str = Form("success")) -> RedirectResponse:
    txn = _LEDGER.get(authority)
    if txn is None:
        raise HTTPException(status_code=404, detail="authority نامعتبر")
    if txn.expired:
        txn.state = "failed"
        return RedirectResponse(url=_callback_url(txn, signed=False), status_code=302)
    if outcome == "success":
        txn.state = "paid"
        return RedirectResponse(url=_callback_url(txn, signed=True), status_code=302)
    txn.state = "cancelled" if outcome == "cancel" else "failed"
    # بانک واقعی هم در انصراف برمی‌گردد، ولی چیزی را امضا نمی‌کند که تأییدشده نباشد
    return RedirectResponse(url=_callback_url(txn, signed=False), status_code=302)


def _callback_url(txn: Txn, *, signed: bool) -> str:
    base = txn.callback_url or "/api/v1/no-callback"
    query = {"Authority": txn.authority, "Amount": str(txn.amount_rial)}
    if signed:
        query["Sign"] = _sign(txn.authority, txn.amount_rial)
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}{urlencode(query)}"


@app.post("/api/v1/verify", summary="تأیید تراکنش (یک‌بارمصرف)")
def verify(payload: AuthorityIn) -> JSONResponse:
    txn = _LEDGER.get(payload.authority)
    if txn is None or txn.expired:
        return JSONResponse({"result": {"status": -1, "message": "authority نامعتبر یا منقضی"}})
    if txn.http_error:  # اهرم آزمون خطای شبکه/سرور
        return JSONResponse(
            {"result": {"status": -1, "message": "خطای درون‌ساز بانک"}}, status_code=503
        )
    if txn.delay_seconds:
        time.sleep(txn.delay_seconds)
    if txn.amount_rial != payload.amount:
        return JSONResponse({"result": {"status": 102, "message": "مبلغ با authority هم‌خوان نیست"}})
    if txn.state != "paid":
        return JSONResponse(
            {"result": {"status": 103, "message": "تراکنش در بانک پرداخت نشده است"}}
        )
    if txn.verified:
        return JSONResponse(
            {
                "result": {"status": 101, "message": "قبلاً تأیید شده"},
                "data": {"ref_id": txn.ref_id, "card_pan": MASKED_PAN},
            }
        )
    txn.verified = True
    txn.ref_id = f"SBXREF-{secrets.token_hex(5)}"
    return JSONResponse(
        {
            "result": {"status": 100},
            "data": {"ref_id": txn.ref_id, "card_pan": MASKED_PAN, "amount": txn.amount_rial},
        }
    )


@app.post("/api/v1/refund", summary="بازگشت وجه")
def refund(payload: AuthorityIn) -> JSONResponse:
    txn = _LEDGER.get(payload.authority)
    if txn is None or txn.expired:
        return JSONResponse({"result": {"status": -1, "message": "authority نامعتبر یا منقضی"}})
    if txn.amount_rial != payload.amount:
        return JSONResponse({"result": {"status": 102, "message": "مبلغ با authority هم‌خوان نیست"}})
    if not txn.verified:
        return JSONResponse(
            {"result": {"status": 103, "message": "تراکنش تأیید نشده را نمی‌توان برگرداند"}}
        )
    if txn.refund_id:
        return JSONResponse(
            {
                "result": {"status": 254, "message": "قبلاً برگشت خورده است"},
                "data": {"ref_id": txn.refund_id},
            }
        )
    txn.refund_id = f"SBXRFD-{secrets.token_hex(5)}"
    txn.state = "refunded"
    return JSONResponse(
        {"result": {"status": 255}, "data": {"ref_id": txn.refund_id, "amount": txn.amount_rial}}
    )


@app.get("/api/v1/status/{authority}", summary="وضعیت — برای دیدنِ دست‌ساز")
def status(authority: str) -> dict:
    txn = _LEDGER.get(authority)
    if txn is None:
        raise HTTPException(status_code=404, detail="authority نامعتبر")
    return {
        "authority": txn.authority,
        "amount": txn.amount_rial,
        "state": txn.state,
        "verified": txn.verified,
        "refunded": bool(txn.refund_id),
        "expired": txn.expired,
    }


__all__ = ["app", "BANK_MERCHANT_ID", "BANK_SECRET", "_reset", "Txn"]
