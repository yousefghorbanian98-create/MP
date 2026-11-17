import { useState } from "react";
import {
  createPayment,
  startPayment,
  confirmGatewayCallback,
  failPayment,
  fetchReceipt,
  type PaymentStart,
  type PaymentRow,
  type Receipt,
} from "../lib/api";
import { fa } from "../lib/useApi";

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
  const [amount, setAmount] = useState("500000");
  const [method, setMethod] = useState<"zarinpal" | "cash" | "card">("zarinpal");
  const [tx, setTx] = useState<PaymentRow | null>(null);
  const [started, setStarted] = useState<PaymentStart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [busy, setBusy] = useState(false);

  async function call<T>(fn: () => Promise<T>): Promise<T | null> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
      return null;
    } finally {
      setBusy(false);
    }
  }

  const create = () =>
    call(async () => {
      const mid = Number(memberId);
      const amt = Number(amount);
      if (!Number.isInteger(mid) || mid <= 0) throw new Error("شناسهٔ عضو باید عدد صحیح مثبت باشد");
      if (!Number.isInteger(amt) || amt < 1000) throw new Error("مبلغ حداقل ۱۰۰۰ ریال است");
      const created = await createPayment({ member_id: mid, amount_rial: amt, method });
      setTx(created);
      setStarted(null);
    });

  const start = () =>
    call(async () => {
      if (!tx) throw new Error("اول تراکنش را بسازید");
      const s = await startPayment(tx.id, `${window.location.origin}/finance`);
      setStarted(s);
    });

  const confirm = () =>
    call(async () => {
      if (!tx || !started) throw new Error("اول پرداخت را در درگاه آغاز کنید");
      const paid = await confirmGatewayCallback(
        tx.id,
        started.authority,
        started.callback_token,
      );
      setTx(paid);
      setStarted(null);
    });

  const markFailed = () =>
    call(async () => {
      if (!tx) throw new Error("تراکنشی نیست");
      const failed = await failPayment(tx.id);
      setTx(failed);
      setStarted(null);
    });

  const loadReceipt = () =>
    call(async () => {
      if (!tx) throw new Error("تراکنشی نیست");
      setReceipt(await fetchReceipt(tx.id));
    });

  const reset = () => {
    setTx(null);
    setStarted(null);
    setReceipt(null);
    setError(null);
  };

  return (
    <section className="glass-card space-y-4 p-5">
      <div>
        <h2 className="text-sm font-bold">پرداخت از درگاه</h2>
        <p className="text-xs text-ink-dim">
          آغاز در درگاه ← بازگشت با authority ← تأیید با امضای مبلغ (HMAC)
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
          روش
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as typeof method)}
            className="focus-ring mt-1 block rounded-lg bg-surface/70 px-3 py-2 text-sm"
          >
            <option value="zarinpal">درگاه</option>
            <option value="cash">نقدی (پذیرش)</option>
            <option value="card">کارت‌خوان</option>
          </select>
        </label>
        <button
          onClick={() => void create()}
          disabled={busy}
          className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
        >
          {busy ? "…" : "ساخت تراکنش"}
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

          {tx.status === "pending" && !started && (
            <button
              onClick={() => void start()}
              disabled={busy}
              className="rounded-lg bg-primary px-4 py-2 text-xs text-white disabled:opacity-50"
            >
              آغاز پرداخت در درگاه
            </button>
          )}

          {started && (
            <div className="space-y-2 rounded-lg border border-primary/30 p-3">
              <p className="text-ink-dim">
                authority: <span dir="ltr">{started.authority}</span>
              </p>
              <p className="text-ink-dim">مبلغ قفل‌شده با امضا — تغییر آن در callback رد می‌شود.</p>
              <a
                href={started.redirect_url}
                className="inline-block rounded-lg border border-primary/40 px-3 py-1.5 text-primary-light"
              >
                رفتن به صفحهٔ درگاه
              </a>
              <button
                onClick={() => void confirm()}
                disabled={busy}
                className="ml-2 rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-50"
              >
                بازگشت از درگاه و تأیید
              </button>
            </div>
          )}

          {tx.status === "pending" && !started && (
            <button
              onClick={() => void markFailed()}
              disabled={busy}
              className="rounded-lg border border-rose-500/40 px-3 py-1.5 text-rose-300 disabled:opacity-50"
            >
              ثبت شکست تراکنش
            </button>
          )}

          {tx.status === "paid" && (
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
              <p className="font-bold">رسید پرداخت #{receipt.payment_id}</p>
              <p>مبلغ: {fmt(receipt.amount_rial)} ریال</p>
              <p>کد پیگیری: {receipt.reference_id}</p>
              {receipt.paid_at && <p>زمان: {new Date(receipt.paid_at).toLocaleString("fa-IR")}</p>}
            </div>
          )}

          <button onClick={reset} className="text-ink-dim underline">
            پاک کردن
          </button>
        </div>
      )}
    </section>
  );
}
