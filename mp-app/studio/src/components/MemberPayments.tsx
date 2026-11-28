/**
 * MEM-12 / PWA-3B — پرداخت دستی (کارت‌به‌کارت) و ارسال فیش، فقط از سمت عضو.
 *
 * معیار پذیرش TODO (`TODO-PWA-RELEASE-2026-11-23.fa.md:240`): «فقط جریان
 * کارت‌به‌کارت مصوب؛ رسید خصوصی با محدودیت اندازه/نوع و دسترسی محدود، وضعیت
 * `pending`، خطا/تکرار و audit. آپلود رسید ≠ تأیید بانک.»
 *
 * قرارداد واقعی (با `grep -n`):
 * - `modules/payments/receipts.py:85-152` → `submit_receipt` فقط برای نقش member،
 *   با `ensure_record_scope` (مالکیت)، `method == "card_to_card"`،
 *   `status == "pending"`، و پاسخ `status="in_review"` + `expires_at`.
 * - `receipts.py:31` → قالب‌های مجاز JPEG/PNG/WebP؛ `app/config.py:58` →
 *   سقف `receipt_max_bytes = 5 * 1024 * 1024`.
 * - `receipts.py:49-82` → سرور محتوای فایل را هم می‌سنجد و کدهای
 *   `receipt_too_large` / `unsupported_receipt_type` / `invalid_receipt_image` /
 *   `receipt_type_mismatch` برمی‌گرداند؛ `:104` → `already_processed`.
 * - `service.py:414-427` → `GET /payments` برای نقش member به عضو خودش محدود می‌شود.
 *
 * قاعده‌ها:
 * - تأیید/رد فیش در این صفحه وجود ندارد؛ آن مسیر `finance.write` است و تصمیمش
 *   با فرد مجاز/مالی است (BLOCKED، نه اختراع).
 * - «آپلود شد» هرگز به «پرداخت شد» یا «اشتراک فعال شد» ترجمه نمی‌شود.
 * - هیچ مبلغی در کلاینت محاسبه نمی‌شود؛ مبلغ‌ها همان `amount_rial` سرور با واحد ریال.
 * - بررسی نوع/حجم در کلاینت فقط پیش‌فیلتر است؛ سرور هم می‌سنجد و خطایش نمایش داده می‌شود.
 */
import { UploadOutlined } from "@ant-design/icons";
import { Upload } from "antd";
import { useEffect, useState } from "react";
import { toDate } from "../lib/clock";
import {
  ApiError,
  ForbiddenError,
  ReceiptUploadError,
  fetchMyPayments,
  uploadPaymentReceipt,
  type PaymentRow,
  type ReceiptUploadResult,
} from "../lib/api";

const SOURCE = "منبع: GET /api/v1/payments";

/** `receipts.py:31` — همان سه قالبی که سرور می‌پذیرد. */
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
/** `app/config.py:58` — سقف سرور؛ کلاینت فقط پیش‌فیلتر می‌کند. */
const MAX_BYTES = 5 * 1024 * 1024;

const methodLabels: Record<string, string> = {
  card_to_card: "کارت‌به‌کارت",
  cash: "نقدی",
  pos: "کارت‌خوان",
  gateway: "درگاه",
  wallet: "کیف پول",
};

const statusLabels: Record<string, string> = {
  pending: "در انتظار پرداخت",
  in_review: "فیش در صف بازبینی",
  paid: "پرداخت‌شده",
  failed: "ناموفق",
  refunded: "بازگشت‌خورده",
};

type Load =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; rows: PaymentRow[] };

function rial(value: number): string {
  return `${value.toLocaleString("fa-IR")} ریال`;
}

function stamp(iso: string | null): string {
  if (!iso) return "زمان ثبت نشده";
  const date = toDate(iso);
  if (Number.isNaN(date.getTime())) return "زمان نامعتبر";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function megabytes(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toLocaleString("fa-IR", { maximumFractionDigits: 1 })} مگابایت`;
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError)
    return "دسترسی به پرداخت‌های این عضو مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "فهرست پرداخت‌ها از سرور دریافت نشد";
}

/** کدهای سرور ⇒ جملهٔ فارسی؛ کد ناشناخته با پیام خود سرور و کد خام نمایش داده می‌شود. */
function uploadErrorText(error: ReceiptUploadError): string {
  switch (error.code) {
    case "receipt_too_large":
      return `حجم فیش بیش از سقف ${megabytes(MAX_BYTES)} است؛ فایل کوچک‌تری انتخاب کنید.`;
    case "unsupported_receipt_type":
    case "invalid_receipt_image":
      return "فایل انتخاب‌شده تصویر معتبر JPEG/PNG/WebP نیست.";
    case "receipt_type_mismatch":
      return "نوع اعلام‌شدهٔ فایل با محتوای واقعی آن نمی‌خواند؛ فایل را دوباره ذخیره کنید.";
    case "already_processed":
      return "این پرداخت قبلاً پردازش شده است؛ فیش تازه‌ای لازم نیست.";
    case "receipt_not_applicable":
      return "این پرداخت مسیر فیش ندارد (فقط کارت‌به‌کارت فیش می‌پذیرد).";
    case "review_expired":
      return "مهلت بازبینی فیش قبلی گذشته است؛ فیش تازه بفرستید.";
    default:
      return error.code
        ? `${error.message} (کد سرور: ${error.code})`
        : error.message;
  }
}

function PaymentCard({
  row,
  onUploaded,
}: {
  row: PaymentRow;
  onUploaded: (result: ReceiptUploadResult) => void;
}) {
  const [status, setStatus] = useState(row.status);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [review, setReview] = useState<ReceiptUploadResult | null>(null);
  const uploadable = row.method === "card_to_card" && status === "pending";

  async function submit(file: File) {
    setMessage(null);
    setReview(null);
    if (!ALLOWED_TYPES.includes(file.type)) {
      setMessage("فقط تصویر JPEG/PNG/WebP پذیرفته می‌شود.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setMessage(`حجم فیش بیش از سقف ${megabytes(MAX_BYTES)} است؛ فایل کوچک‌تری انتخاب کنید.`);
      return;
    }
    setBusy(true);
    try {
      const result = await uploadPaymentReceipt(row.id, file);
      setReview(result);
      setStatus(result.status);
      onUploaded(result);
    } catch (error: unknown) {
      if (error instanceof ForbiddenError) {
        setMessage("اجازهٔ ارسال فیش برای این پرداخت به حساب شما داده نشده است.");
      } else if (error instanceof ReceiptUploadError) {
        setMessage(uploadErrorText(error));
      } else {
        setMessage("ارسال فیش انجام نشد؛ دوباره تلاش کنید.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <li
      className="space-y-2 rounded-lg border border-primary/10 px-3 py-2 text-xs"
      data-payment-id={row.id}
      data-payment-status={status}
      data-payment-method={row.method}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">{rial(row.amount_rial)}</span>
        <span className="text-ink-dim">
          {methodLabels[row.method] ?? row.method} · {statusLabels[status] ?? status}
        </span>
      </div>
      <p className="text-ink-dim">
        ثبت: {stamp(row.paid_at)} · شناسهٔ پرداخت #{row.id.toLocaleString("fa-IR")}
        {row.description ? ` · ${row.description}` : ""}
      </p>

      {uploadable ? (
        <div className="space-y-1" data-upload-enabled="yes">
          <p className="text-ink-dim">
            ارسال فیش کارت‌به‌کارت (JPEG/PNG/WebP · حداکثر {megabytes(MAX_BYTES)})
          </p>
          {/*
            Upload کتابخانه‌ای (antd) — قاعدهٔ Q11: کنترل تعاملی از صفر نوشته نمی‌شود.
            `beforeUpload` با بازگشت false جلوی آپلود خودکار antd را می‌گیرد؛ ارسال با
            همان تابع `uploadPaymentReceipt` (که فیش را به مسیر سرور می‌فرستد) انجام می‌شود.
          */}
          <Upload
            accept="image/jpeg,image/png,image/webp"
            multiple={false}
            showUploadList={false}
            disabled={busy}
            beforeUpload={(file) => {
              void submit(file as File);
              return false;
            }}
          >
            <button type="button" className="btn-ghost rounded-lg px-3 py-1 text-xs" disabled={busy}>
              <UploadOutlined /> انتخاب تصویر فیش
            </button>
          </Upload>
          {busy ? (
            <p role="status" className="text-[11px] text-ink-dim">
              در حال ارسال فیش به سرور…
            </p>
          ) : null}
        </div>
      ) : (
        <p className="text-[11px] text-ink-dim" data-upload-enabled="no">
          {row.method === "card_to_card"
            ? `ارسال فیش برای این ردیف باز نیست؛ وضعیت «${statusLabels[status] ?? status}» است.`
            : "فقط پرداخت کارت‌به‌کارت فیش می‌پذیرد."}
        </p>
      )}

      {message ? (
        <p role="alert" className="text-[11px] text-danger" data-upload-error>
          {message}
        </p>
      ) : null}

      {review ? (
        <div className="space-y-1 rounded-lg bg-surface/60 px-2 py-1" data-receipt-status={review.status}>
          <p>
            فیش دریافت شد و در صف بازبینی است (کد پیگیری:{" "}
            <span data-review-id>{review.review_id}</span>).
          </p>
          <p className="text-ink-dim">
            مهلت بازبینی: {stamp(review.expires_at)} · حجم {megabytes(review.size_bytes)} · {review.mime}
          </p>
          <p className="text-ink-dim">
            این «پرداخت‌شده» نیست: آپلود فیش ≠ تأیید بانک، و اشتراک تا تأیید فرد مجاز فعال نمی‌شود.
          </p>
        </div>
      ) : null}
    </li>
  );
}

export function MemberPayments() {
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [reloadKey, setReloadKey] = useState(0);
  const [uploaded, setUploaded] = useState<ReceiptUploadResult | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoad({ kind: "loading" });
    fetchMyPayments(undefined, controller.signal)
      .then((rows) => setLoad({ kind: "ready", rows }))
      .catch((error: unknown) => setLoad({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [reloadKey]);

  if (load.kind === "error") {
    return (
      <section aria-labelledby="member-payments-title" className="space-y-3">
        <h3 id="member-payments-title" className="text-base font-semibold">
          پرداخت‌های من
        </h3>
        <p role="alert" className="text-sm text-danger">
          {load.message}
        </p>
      </section>
    );
  }

  if (load.kind === "loading") {
    return (
      <section aria-labelledby="member-payments-title" className="space-y-3">
        <h3 id="member-payments-title" className="text-base font-semibold">
          پرداخت‌های من
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت پرداخت‌ها از سرور…
        </p>
      </section>
    );
  }

  const rows = load.rows;

  return (
    <section aria-labelledby="member-payments-title" className="space-y-4">
      <div>
        <h3 id="member-payments-title" className="text-base font-semibold">
          پرداخت‌های من
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          مبلغ‌ها همان مبلغ ثبت‌شدهٔ سرور است (عدد صحیح ریال)؛ کلاینت چیزی محاسبه نمی‌کند.
        </p>
        <p className="text-[11px] text-ink-dim">{SOURCE}</p>
      </div>

      <p className="rounded-xl border border-primary/20 bg-surface/60 px-3 py-2 text-xs">
        آپلود فیش ≠ تأیید بانک. فیش شما خصوصی است، در صف بازبینی می‌ماند و پرداخت فقط پس از بررسی
        توسط فرد مجاز تأیید می‌شود؛ تا آن زمان اشتراک فعال نمی‌شود.
      </p>

      {uploaded ? (
        <p role="status" className="text-[11px] text-ink-dim" data-last-upload={uploaded.payment_id}>
          آخرین ارسال: پرداخت #{uploaded.payment_id.toLocaleString("fa-IR")} · وضعیت سرور:{" "}
          {statusLabels[uploaded.status] ?? uploaded.status}
        </p>
      ) : null}

      {rows.length === 0 ? (
        <p role="status" className="text-sm text-ink-dim">
          سرور هیچ پرداختی برای این حساب برنگرداند. این «پرداخت صفر» نیست؛ یعنی ردیفی ثبت نشده است.
        </p>
      ) : (
        <ul className="space-y-2">
          {rows.map((row) => (
            <PaymentCard key={row.id} row={row} onUploaded={setUploaded} />
          ))}
        </ul>
      )}

      <button
        type="button"
        className="rounded-lg border border-primary/30 px-3 py-1 text-xs"
        onClick={() => setReloadKey((value) => value + 1)}
      >
        بازخوانی از سرور
      </button>

      <p className="text-[11px] text-ink-dim">
        تأیید یا رد فیش در این صفحه نیست: آن کار به مجوز مالی (`finance.write`) و بررسی مستند بانکی
        نیاز دارد و خارج از دسترس حساب عضو است.
      </p>
    </section>
  );
}
