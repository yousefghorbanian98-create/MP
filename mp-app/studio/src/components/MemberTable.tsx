import { motion } from "framer-motion";
import type { MemberRow } from "../data/mock";
import { useAppStore } from "../stores/appStore";

const statusPill: Record<MemberRow["status"], { label: string; cls: string }> = {
  active: { label: "فعال", cls: "pill-green" },
  expiring: { label: "رو به انقضا", cls: "pill-gold" },
  expired: { label: "منقضی", cls: "pill-red" },
};

/** جدول اعضا با ورود پلکانی و ردیف‌های تعاملی. */
export function MemberTable({ onSelect }: { onSelect?: (id: number) => void }) {
  const filteredMembers = useAppStore((s) => s.filteredMembers);

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-primary/10 px-5 py-4">
        <h3 className="text-base font-semibold">اعضای اخیر</h3>
        <span className="text-xs text-ink-dim">{filteredMembers().length.toLocaleString("fa-IR")} عضو</span>
      </div>
      <div className="divide-y divide-primary/5">
        {filteredMembers().map((m, i) => (
          <motion.button
            key={m.id}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
            whileHover={{ backgroundColor: "rgba(0,184,106,0.06)" }}
            onClick={() => onSelect?.(m.id)}
            className="flex w-full items-center gap-3 px-5 py-3 text-right"
          >
            <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
              style={{ background: `linear-gradient(135deg, hsl(${m.avatarHue} 60% 38%), hsl(${m.avatarHue} 55% 24%))` }}
            >
              {m.name.slice(0, 1)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{m.name}</p>
              <p className="truncate text-xs text-ink-dim">
                {m.phone} · {m.goal} · {m.gender === "female" ? "بانو" : "آقا"}
              </p>
            </div>
            <div className="text-left">
              <span className={statusPill[m.status].cls}>{statusPill[m.status].label}</span>
              <p className="mt-1 text-[11px] text-ink-dim">
                {m.daysLeft >= 0 ? `${m.daysLeft.toLocaleString("fa-IR")} روز باقی‌مانده` : "اتمام اشتراک"}
              </p>
            </div>
            <div className="hidden w-28 text-xs text-ink-dim lg:block">{m.lastSeen}</div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
