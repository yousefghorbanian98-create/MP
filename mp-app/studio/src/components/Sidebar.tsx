import { motion } from "framer-motion";
import { useAppStore, type PageId } from "../stores/appStore";

const items: { id: PageId; label: string; icon: string }[] = [
  { id: "dashboard", label: "داشبورد", icon: "◈" },
  { id: "members", label: "اعضا", icon: "◉" },
  { id: "programs", label: "برنامه‌ها", icon: "▤" },
  { id: "checkin", label: "حضور", icon: "◎" },
  { id: "settings", label: "تنظیمات", icon: "⚙" },
];

/** نوار کناری با نشانگر متحرک و hover نرم. */
export function Sidebar() {
  const { page, setPage } = useAppStore();

  return (
    <aside className="glass-card sticky top-6 flex h-[calc(100vh-3rem)] w-56 flex-col gap-2 p-4">
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/20 text-lg text-primary-light shadow-glow">
          MP
        </div>
        <div>
          <p className="text-sm font-bold">Muscle Paradise</p>
          <p className="text-xs text-ink-dim">پنل مربی / مدیر</p>
        </div>
      </div>

      <nav className="relative flex flex-col gap-1">
        {items.map((item) => {
          const active = page === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`focus-ring relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors duration-200 ${
                active ? "text-white" : "text-ink-dim hover:bg-surface/70 hover:text-ink"
              }`}
            >
              {active && (
                <motion.span
                  layoutId="nav-pill"
                  className="absolute inset-0 rounded-xl bg-primary/20 ring-1 ring-primary/40"
                  transition={{ type: "spring", stiffness: 380, damping: 32 }}
                />
              )}
              <span className="relative z-10 text-base">{item.icon}</span>
              <span className="relative z-10 font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto">
        <div className="glass-card p-3 text-xs text-ink-dim">
          <div className="mb-1 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse-soft" />
            <span>سیستم فعال — گیت ورود متصل</span>
          </div>
          <p>نسخهٔ ۱.۰ · ساخت M06</p>
        </div>
      </div>
    </aside>
  );
}
