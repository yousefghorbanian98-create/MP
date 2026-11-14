import { motion } from "framer-motion";
import { useAppStore } from "../stores/appStore";

const titles: Record<string, { title: string; sub: string }> = {
  dashboard: { title: "داشبورد", sub: "نمای کلی امروز باشگاه" },
  members: { title: "مدیریت اعضا", sub: "جست‌وجو، فیلتر و پروفایل اعضا" },
  programs: { title: "برنامه‌های تمرین", sub: "تأیید و ویرایش برنامه‌ها (خروجی موتور قواعد)" },
  checkin: { title: "حضور و چک‌این", sub: "نمای زندهٔ ورود اعضا" },
  settings: { title: "تنظیمات", sub: "پرچم‌های قابلیت و سیستم" },
};

/** نوار بالایی — عنوان صفحه + جست‌وجو + اعلان‌ها. */
export function TopBar() {
  const { page, search, setSearch } = useAppStore();
  const t = titles[page] ?? titles.dashboard;

  return (
    <header className="mb-6 flex items-center justify-between gap-4">
      <motion.div key={page} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.28 }}>
        <h1 className="text-2xl font-bold tracking-tight">{t.title}</h1>
        <p className="mt-0.5 text-sm text-ink-dim">{t.sub}</p>
      </motion.div>

      <div className="flex items-center gap-3">
        <div className="relative">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="جست‌وجوی عضو..."
            className="focus-ring w-64 rounded-xl border border-primary/15 bg-surface/60 py-2 pr-9 pl-3 text-sm placeholder:text-ink-dim/70"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-dim">⌕</span>
        </div>
        <button className="focus-ring relative rounded-xl border border-primary/15 bg-surface/60 p-2.5 text-ink-dim transition-colors hover:text-ink">
          ◔
          <span className="absolute left-1.5 top-1.5 h-2 w-2 rounded-full bg-accent" />
        </button>
        <div className="flex items-center gap-2 rounded-xl border border-primary/15 bg-surface/60 px-3 py-1.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20 text-xs font-bold text-accent-soft">
            م‌م
          </div>
          <div className="text-xs">
            <p className="font-semibold">مربی مهدی</p>
            <p className="text-ink-dim">مدیر</p>
          </div>
        </div>
      </div>
    </header>
  );
}
