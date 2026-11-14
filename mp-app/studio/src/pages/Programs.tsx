import { motion } from "framer-motion";

const programs = [
  { id: 1, member: "علی رضایی", goal: "حجم‌سازی", status: "draft", engine: "rules-1.0", weeks: 4 },
  { id: 2, member: "سارا محمدی", goal: "کاهش وزن", status: "approved", engine: "rules-1.0", weeks: 6 },
  { id: 3, member: "رضا کریمی", goal: "آمادگی جسمانی", status: "draft", engine: "rules-1.0", weeks: 4 },
  { id: 4, member: "نگار صادقی", goal: "کاهش وزن", status: "rejected", engine: "rules-1.0", weeks: 4 },
];

const statusMap: Record<string, { label: string; cls: string }> = {
  draft: { label: "در انتظار تأیید مربی", cls: "pill-gold" },
  approved: { label: "تأییدشده", cls: "pill-green" },
  rejected: { label: "ردشده", cls: "pill-red" },
};

/** برنامه‌ها — خروجی موتور قواعد در انتظار تأیید مربی (G8). */
export function Programs() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className="glass-card flex items-center gap-3 border-accent/25 p-4">
        <span className="text-xl">⚖️</span>
        <p className="text-sm text-ink-dim">
          اعداد بار/ست/تکرار فقط از <b className="text-accent-soft">موتور قواعد قطعی</b> تولید می‌شوند (قانون G8)؛
          مربی پیش از نمایش به عضو، برنامه را تأیید می‌کند.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {programs.map((p, i) => (
          <motion.div
            key={p.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
            whileHover={{ y: -3 }}
            className="glass-card-hover p-5"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{p.member}</h3>
                <p className="text-xs text-ink-dim">هدف: {p.goal} · {p.weeks.toLocaleString("fa-IR")} هفته · نسخهٔ موتور {p.engine}</p>
              </div>
              <span className={statusMap[p.status].cls}>{statusMap[p.status].label}</span>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="flex -space-x-2 space-x-reverse">
                {["سینه", "پا", "پشت", "بازو"].map((g, j) => (
                  <span key={g} className="rounded-lg border border-primary/15 bg-surface/80 px-2 py-1 text-[11px] text-ink-dim">
                    {g}
                  </span>
                ))}
              </div>
              {p.status === "draft" && (
                <div className="flex gap-2">
                  <button className="btn-primary px-3 py-1.5 text-xs">تأیید</button>
                  <button className="btn-ghost px-3 py-1.5 text-xs">رد</button>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
