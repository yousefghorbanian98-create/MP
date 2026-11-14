import { motion } from "framer-motion";
import type { Kpi } from "../data/mock";
import { AnimatedCounter } from "./AnimatedCounter";

/** کارت KPI — شیشه‌ای با اسپارک‌لاین و نشانگر تغییر. */
export function KpiCard({ kpi, index }: { kpi: Kpi; index: number }) {
  const up = kpi.deltaPct >= 0;
  const points = kpi.spark
    .map((v, i) => {
      const max = Math.max(...kpi.spark);
      const min = Math.min(...kpi.spark);
      const x = (i / (kpi.spark.length - 1)) * 100;
      const y = 28 - ((v - min) / Math.max(max - min, 1)) * 24;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, type: "spring", stiffness: 240, damping: 22 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="glass-card-hover relative overflow-hidden p-5"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-l from-transparent via-primary/40 to-transparent" />
      <p className="text-sm text-ink-dim">{kpi.label}</p>
      <div className="mt-2 flex items-end justify-between">
        <div className="text-3xl font-bold tracking-tight">
          <AnimatedCounter value={kpi.value} />
          <span className="mr-1 text-base font-medium text-ink-dim">{kpi.unit}</span>
        </div>
        <svg viewBox="0 0 100 30" className="h-8 w-24 overflow-visible" aria-hidden>
          <polyline
            points={points}
            fill="none"
            stroke={up ? "#00B86A" : "#F87171"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.9"
          />
        </svg>
      </div>
      <div className="mt-2 flex items-center gap-1 text-xs">
        <span className={up ? "text-primary-light" : "text-danger"}>
          {up ? "▲" : "▼"} {Math.abs(kpi.deltaPct).toLocaleString("fa-IR")}٪
        </span>
        <span className="text-ink-dim">نسبت به هفتهٔ قبل</span>
      </div>
    </motion.div>
  );
}
