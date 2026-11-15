import { motion } from "framer-motion";
import { fa } from "../lib/useApi";

/**
 * کارت KPI (M45-c1) — از دادهٔ واقعی `/admin/kpis`.
 *
 * `value === null` یعنی داده موجود نیست (مثلاً ظرفیت کلاس ثبت نشده).
 * در آن حالت «نامعلوم» نوشته می‌شود، نه صفر و نه نمودار ساختگی.
 * sparkline حذف شد: سری زمانی واقعی KPI وجود ندارد، پس کشیدنش ادعا بود.
 */
export function KpiCard({
  label,
  value,
  unit = "",
  hint,
  index,
}: {
  label: string;
  value: number | null;
  unit?: string;
  hint?: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, type: "spring", stiffness: 240, damping: 22 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="glass-card-hover relative overflow-hidden p-5"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-l from-transparent via-primary/40 to-transparent" />
      <p className="text-sm text-ink-dim">{label}</p>
      <div className="mt-2 text-3xl font-bold tracking-tight">
        {value == null ? (
          <span className="text-lg font-medium text-ink-dim">نامعلوم</span>
        ) : (
          <>
            {fa(value)}
            {unit ? (
              <span className="mr-1 text-base font-medium text-ink-dim">{unit}</span>
            ) : null}
          </>
        )}
      </div>
      {hint && <p className="mt-2 text-[11px] text-ink-dim">{hint}</p>}
    </motion.div>
  );
}
