import { useRef, useState } from "react";
import {
  createPayment,
  verifyPayment,
  failPayment,
  fetchReceipt,
  listPayments,
  refundPayment,
  type PaymentRow,
  type Receipt,
} from "../lib/api";
import { Input, Select } from "antd";
import { parseRial } from "../lib/money";
import { toDate } from "../lib/clock";

/**
 * Q6 — درگاه پرداخت (پذیرش).
 *
 * پیش از این `modules/payments/gateway.py` (Mock + زرین‌پال + امضای HMAC)
 * کامل نوشته شده بود ولی **هیچ مصرف‌کننده‌ای نداشت**: هیچ صفحه‌ای نمی‌توانست
 * تراکنش را در درگاه آغاز کند، پس پرداخت همیشه pending می‌ماند.
 *
 * جریان واقعی: ساخت تراکنش → start (authority از درگاه) → هدایت کاربر →
 * callback با امضای مبلغ. دکمهٔ «پرداخت شد» بدون authority کار نمی‌کند.
 *
 * قاعدهٔ بازنمایی: مبلغ هرگز از پاسخ callback گرفته نمی‌شود؛ مبلغ نمایش‌داده‌شده
 * همان مبلغ ثبت‌شده در DB است.
 */

const fmt = (n: number) => n.toLocaleString("fa-IR");

export function PaymentPanel() {
  const [memberId, setMemberId] = useState("");
  const [lookupId, setLookupId] = useState("");
  const [amount, setAmount] = useState("500000");
  // فاز ۳: فقط پرداخت حضوری؛ هیچ گزینهٔ درگاه اینترنتی نمی‌ماند.
  const [method, setMethod] = useState<"cash" | "card">("cash");
  const [coupon, setCoupon] = useState("");
  const [tx, setTx] = useState<PaymentRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);

  async function call<T>(fn: () => Promise<T>): Promise<T | null> {
    // Guard synchronously too: two clicks can arrive before React renders `busy`.
    if (busyRef.current) return null;
    busyRef.current = true;
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
      return null;
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  const clearSelection = () => {
    setTx(null);
    setReceipt(null);
  };

  const create = () =>
    call(async () => {
      const mid = Number(memberId);
      const amt = parseRial(amount);
      if (!Number.isInteger(mid) || mid <= 0) throw new Error("شناسهٔ عضو باید عدد صحیح مثبت باشد");
      if (amt === null || amt < 1000) throw new Error("مبلغ حداقل ۱۰۰۰ ریال و عدد صحیح است");
      const code = coupon.trim();
      const created = await createPayment({
        member_id: mid,
        amount_rial: amt,
        method,
        ...(code ? { coupon_code: code } : {}),
      });
      setTx(created);
    });

  const confirmManual = () =>
    call(async () => {
      if (!tx) throw new Error("اول تراکنش را بسازید");
      // پذیرش نقدی/کارت‌خوان: مرجع پیگیری دستی ثبت می‌شود، نه ادعای درگاه.
      const paid = await verifyPayment(tx.id, `manual-${tx.id}`);
      setTx(paid);
    });

  const markFailed = () =>
    call(async () => {
      if (!tx) throw new Error("تراکنشی نیست");
      const failed = await failPayment(tx.id);
      setTx(failed);
    });

  const loadReceipt = () =>
    call(async () => {
      if (!tx) throw new Error("تراکنشی نیست");
      setReceipt(await fetchReceipt(tx.id));
    });

  const lookup = () =>
    call(async () => {
      // An unsuccessful lookup must never leave a previously selected refund target.
      clearSelection();
      const id = Number(lookupId);
      if (!Number.isSafeInteger(id) || id <= 0) throw new Error("شناسهٔ پرداخت نامعتبر است");
      const payment = (await listPayments()).find((p) => p.id === id);
      if (!payment) throw new Error("پرداخت یافت نشد");
      setTx(payment);
      setReceipt(null);
    });

  const refund = () =>
    call(async () => {
      if (!tx) throw new Error("تراکنشی نیست");
      if (!window.confirm(`بازگشت ${fmt(tx.amount_rial)} ریال برای پرداخت #${tx.id}؟`)) return;
      const updated = await refundPayment(tx.id);
      setTx(updated);
      setReceipt(null);
    });

  const reset = () => {
    clearSelection();
    setError(null);
  };

  return (
    <section className="glass-card space-y-4 p-5">
      <div>
        <h2 className="text-sm font-bold">پرداخت حضوری</h2>
        <p className="text-xs text-ink-dim">
          پرداخت اینترنتی حذف شده است؛ نقدی یا کارت‌خوان در پذیرش ثبت و تأیید می‌شود.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-2 text-xs">
        <label className="text-ink-dim">
          شناسهٔ عضو
          <input
            value={memberId}
            onChange={(e) => setMemberId(e.target.value)}
            inputMode="numeric"
            className="focus-ring mt-1 block w-28 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <label className="text-ink-dim">
          مبلغ (ریال)
          <input
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            inputMode="numeric"
            className="focus-ring mt-1 block w-36 rounded-lg bg-surface/70 px-3 py-2 text-sm"
          />
        </label>
        <label className="text-ink-dim">
          کد تخفیف (اختیاری)
          <Input
            value={coupon}
            onChange={(e) => setCoupon(e.target.value)}
            className="mt-1 block w-36"
          />
        </label>
        <div className="text-ink-dim">
          <span>روش</span>
          <Select
            aria-label="روش پرداخت"
            className="mt-1 block w-44"
            options={[
              { value: "cash", label: "نقدی (پذیرش)" },
              { value: "card", label: "کارت‌خوان" },
            ]}
            value={method}
            onChange={(value) => setMethod(value as typeof method)}
          />
        </div>
        <button
          onClick={() => void create()}
          disabled={busy}
          className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
        >
          {busy ? "…" : "ساخت تراکنش"}
        </button>
      </div>

      <div className="flex items-end gap-2 text-xs">
        <label>شناسهٔ پرداخت موجود
          <input value={lookupId} onChange={(e) => {
            setLookupId(e.target.value);
            clearSelection();
            setError(null);
          }} inputMode="numeric" disabled={busy}
            className="focus-ring mt-1 block w-28 rounded-lg bg-surface/70 px-3 py-2 text-sm" />
        </label>
        <button onClick={() => void lookup()} disabled={busy} className="btn-primary px-4 py-2">
          بارگذاری پرداخت
        </button>
      </div>

      {error && (
        <p role="alert" className="text-xs text-rose-400">
          {error}
        </p>
      )}

      {tx && (
        <div className="space-y-2 rounded-lg bg-surface/60 p-3 text-xs">
          <p>
            تراکنش #{tx.id} — مبلغ <b>{fmt(tx.amount_rial)}</b> ریال · وضعیت:{" "}
            <b className={tx.status === "paid" ? "text-emerald-400" : "text-ink"}>{tx.status}</b>
          </p>
          {tx.reference_id && <p className="text-ink-dim">کد پیگیری: {tx.reference_id}</p>}

          {tx.status === "pending" && (
            <button
              onClick={() => void confirmManual()}
              disabled={busy}
              className="rounded-lg bg-primary px-4 py-2 text-xs text-bg transition-colors hover:bg-primary-light disabled:opacity-50"
            >
              تأیید دریافت نقدی/کارت‌خوان
            </button>
          )}

          {tx.status === "pending" && (
            <button
              onClick={() => void markFailed()}
              disabled={busy}
              className="rounded-lg border border-rose-500/40 px-3 py-1.5 text-rose-300 disabled:opacity-50"
            >
              ثبت شکست تراکنش
            </button>
          )}

          {tx.status === "paid" && tx.gateway_authority && (
            <button onClick={() => void refund()} disabled={busy}
              className="rounded-lg border border-rose-500/40 px-3 py-1.5 text-rose-300 disabled:opacity-50">
              بازگشت وجه
            </button>
          )}

          {(tx.status === "paid" || tx.status === "refunded") && (
            <button
              onClick={() => void loadReceipt()}
              disabled={busy}
              className="rounded-lg border border-emerald-500/40 px-3 py-1.5 text-emerald-300 disabled:opacity-50"
            >
              نمایش رسید
            </button>
          )}

          {receipt && (
            <div className="mt-2 rounded-lg border border-emerald-500/30 p-3 text-[11px] leading-6">
              <p className="font-bold">{receipt.status === "refunded" ? "رسید بازگشت وجه" : "رسید پرداخت"} #{receipt.payment_id}</p>
              <p>مبلغ: {fmt(receipt.amount_rial)} ریال</p>
              <p>کد پیگیری پرداخت: {receipt.reference_id}</p>
              {receipt.status === "refunded" && <p>مرجع بازگشت: {receipt.refund_reference || "ثبت نشده توسط درگاه"}</p>}
              {receipt.paid_at && <p>زمان: {toDate(receipt.paid_at).toLocaleString("fa-IR")}</p>}
            </div>
          )}

          <button onClick={reset} disabled={busy} className="text-ink-dim underline">
            پاک کردن
          </button>
        </div>
      )}
    </section>
  );
}
