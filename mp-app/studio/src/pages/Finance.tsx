import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  fetchCommission,
  fetchFinanceSummary,
  fetchPaymentsCsv,
  type CommissionResult,
  type FinanceSummary,
} from "../lib/api";
import { fa } from "../lib/useApi";

const fmt = (n: number) => fa(n);

/**
 * مالی — خلاصه، کمیسیون مربی، خروجی CSV (M27/باز-۴).
 *
 * باگ M52-c1: این صفحه با `fetch` خام و **بدون هدر Authorization** صدا
 * می‌زد، پس هر سه دکمه در عمل ۴۰۱ می‌گرفتند — صفحهٔ مالی کاملاً مرده بود.
 * حالا از لایهٔ مشترک api استفاده می‌شود که توکن را می‌گذارد و ۴۰۱/۴۰۳
 * را به AuthError تبدیل می‌کند تا پیام «نیاز به توکن» نشان داده شود.
 */
export function Finance() {
  const [coachId, setCoachId] = useState("");
  const [rate, setRate] = useState("10");
  const [commission, setCommission] = useState<CommissionResult | null>(null);
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const call = async (fn: () => Promise<void>) => {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    } finally {
      setBusy(false);
    }
  };

  const fetchSummary = () =>
    call(async () => {
      setSummary(await fetchFinanceSummary());
    });

  // خلاصه هنگام باز شدن صفحه بارگذاری می‌شود — صفحهٔ مالی نباید تا کلیک
  // کاربر خالی بماند و «خراب» به نظر برسد.
  useEffect(() => {
    void fetchSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const calculateCommission = () =>
    call(async () => {
      if (!coachId.trim()) throw new Error("شناسهٔ مربی را وارد کنید");
      const id = Number(coachId);
      if (!Number.isFinite(id) || id < 1) throw new Error("شناسهٔ مربی باید عدد مثبت باشد");
      const pct = Number(rate);
      if (!Number.isFinite(pct) || pct < 0 || pct > 100) {
        throw new Error("درصد کمیسیون باید بین ۰ تا ۱۰۰ باشد");
      }
      setCommission(await fetchCommission(id, pct / 100));
    });

  const downloadCsv = () =>
    call(async () => {
      const blob = await fetchPaymentsCsv();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "payments-export.csv";
      a.click();
      URL.revokeObjectURL(url);
    });

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className="glass-card space-y-4 p-5">
        <h2 className="text-sm font-bold">گزارش مالی</h2>
        <div className="flex items-center gap-3">
          <button onClick={fetchSummary} disabled={busy} className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm text-white transition-transform hover:scale-[1.02] active:scale-95">
            خلاصهٔ مالی
          </button>
          <button onClick={downloadCsv} disabled={busy} className="focus-ring rounded-xl border border-primary/40 px-4 py-2 text-sm text-primary-light transition-colors hover:bg-primary/10">
            دانلود CSV حسابداری
          </button>
        </div>
        {summary && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-xl bg-primary/10 p-3">
              <p className="text-xs text-ink-dim">پرداخت‌شده (ریال)</p>
              <p className="text-lg font-bold">{fmt(summary.total_paid_rial)}</p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3">
              <p className="text-xs text-ink-dim">در انتظار (ریال)</p>
              <p className="text-lg font-bold">{fmt(summary.total_pending_rial)}</p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3">
              <p className="text-xs text-ink-dim">تعداد پرداخت موفق</p>
              <p className="text-lg font-bold">{fmt(summary.paid_count)}</p>
            </div>
          </motion.div>
        )}
      </div>

      <div className="glass-card space-y-4 p-5">
        <h2 className="text-sm font-bold">کمیسیون مربی</h2>
        <div className="flex flex-wrap items-center gap-3">
          <input
            value={coachId}
            onChange={(e) => setCoachId(e.target.value)}
            placeholder="شناسهٔ مربی"
            inputMode="numeric"
            className="focus-ring w-36 rounded-xl border border-primary/30 bg-transparent px-3 py-2 text-sm"
          />
          <input
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            placeholder="درصد"
            inputMode="decimal"
            className="focus-ring w-24 rounded-xl border border-primary/30 bg-transparent px-3 py-2 text-sm"
          />
          <button onClick={calculateCommission} disabled={busy} className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm text-white transition-transform hover:scale-[1.02] active:scale-95">
            محاسبه
          </button>
        </div>
        {commission && (
          <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="rounded-xl bg-primary/10 p-4 text-sm leading-7">
            <p>مربی: <b>{commission.coach_name}</b> (#{commission.coach_id})</p>
            <p>پرداخت‌های منتسب: <b>{fmt(commission.attributed_payments_rial)}</b> ریال</p>
            <p>کمیسیون {fmt(commission.rate * 100)}٪: <b className="text-primary-light">{fmt(commission.commission_rial)}</b> ریال</p>
          </motion.div>
        )}
      </div>

      {error && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          ⚠ {error}
        </motion.p>
      )}
    </motion.div>
  );
}
