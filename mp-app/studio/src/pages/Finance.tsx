import { motion } from "framer-motion";
import { useState } from "react";

interface CommissionResult {
  coach_id: number;
  coach_name: string;
  rate: number;
  attributed_payments_rial: number;
  commission_rial: number;
}

interface FinanceSummary {
  total_paid_rial: number;
  total_pending_rial: number;
  paid_count: number;
}

const fmt = (n: number) => n.toLocaleString("fa-IR");

/**
 * مالی — خلاصه، کمیسیون مربی، خروجی CSV (M27/باز-۴).
 * هر دکمه خروجی واقعی می‌دهد؛ خطا صریح نمایش داده می‌شود (هرگز بی‌صدا).
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
      const r = await fetch("/api/v1/payments/finance/summary");
      if (!r.ok) throw new Error(`خلاصهٔ مالی دریافت نشد (HTTP ${r.status})`);
      setSummary(await r.json());
    });

  const fetchCommission = () =>
    call(async () => {
      if (!coachId.trim()) throw new Error("شناسهٔ مربی را وارد کنید");
      const r = await fetch("/api/v1/payments/finance/commission", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ coach_id: Number(coachId), rate: Number(rate) / 100 }),
      });
      if (!r.ok) throw new Error(`محاسبه ناموفق (HTTP ${r.status})`);
      setCommission(await r.json());
    });

  const downloadCsv = () =>
    call(async () => {
      const r = await fetch("/api/v1/payments/finance/export.csv");
      if (!r.ok) throw new Error(`CSV دریافت نشد (HTTP ${r.status})`);
      const blob = await r.blob();
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
          <button onClick={fetchCommission} disabled={busy} className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm text-white transition-transform hover:scale-[1.02] active:scale-95">
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
