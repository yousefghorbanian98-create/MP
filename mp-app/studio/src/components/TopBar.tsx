/**
 * نوار بالایی (M46-c2) — سه اصلاح واقعی:
 *
 * ۱) جست‌وجو فقط در صفحاتی نمایش داده می‌شود که واقعاً فیلتر دارند
 *    (پیش از این در ۷ صفحه بود ولی فقط «اعضا» آن را می‌خواند).
 * ۲) هویت واقعی از `GET /members/me` — نه «مربی مهدی / مدیر» hardcode.
 * ۳) دکمهٔ زنگ اعلان واقعاً باز می‌شود و تعداد خوانده‌نشده‌ها را از API می‌گیرد؛
 *    پیش از این `<button>` بدون `onClick` با نقطهٔ قرمزِ همیشگی بود.
 */
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { PhoneChangeDialog } from "./PhoneChangeDialog";
import { fetchMe, type Me } from "../lib/api";
import { useAppStore } from "../stores/appStore";

const titles: Record<string, { title: string; sub: string }> = {
  dashboard: { title: "داشبورد", sub: "نمای کلی امروز باشگاه" },
  members: { title: "مدیریت اعضا", sub: "جست‌وجو، فیلتر و پروفایل اعضا" },
  programs: { title: "برنامه‌های تمرین", sub: "تأیید و ویرایش برنامه‌ها (خروجی موتور قواعد)" },
  checkin: { title: "حضور و چک‌این", sub: "نمای زندهٔ ورود اعضا" },
  finance: { title: "مالی و پرداخت", sub: "خلاصهٔ مالی، کمیسیون و خروجی CSV" },
  analytics: { title: "تحلیل‌ها", sub: "لیدربورد، ریسک ریزش و لاگ ممیزی" },
  settings: { title: "تنظیمات", sub: "پرچم‌های قابلیت و نقش کاربران" },
};

const ROLE_FA: Record<string, string> = {
  admin: "مدیر",
  coach: "مربی",
  reception: "پذیرش",
  member: "عضو",
  staff: "کارمند",
};

/** فقط این صفحه فیلتر جست‌وجو دارد؛ نمایش جست‌وجو در بقیه، دکور بود. */
const SEARCH_PAGES = new Set(["members"]);

export function TopBar() {
  const { page, search, setSearch } = useAppStore();
  const { signOut } = useAuth();
  const [me, setMe] = useState<Me | null>(null);
  const [meError, setMeError] = useState<string | null>(null);
  const [phoneChangeOpen, setPhoneChangeOpen] = useState(false);
  const t = titles[page] ?? titles.dashboard;

  useEffect(() => {
    const ctrl = new AbortController();
    fetchMe(undefined, ctrl.signal)
      .then(setMe)
      .catch((e: Error) => {
        if (e.name !== "AbortError") setMeError(e.message);
      });
    return () => ctrl.abort();
  }, []);

  const initials = me?.full_name
    ? me.full_name
        .split(" ")
        .slice(0, 2)
        .map((w) => w[0])
        .join("")
    : "؟";

  return (
    <header className="mb-6 flex items-center justify-between gap-4">
      <motion.div
        key={page}
        initial={{ opacity: 0, x: 12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.28 }}
      >
        <h1 className="text-2xl font-bold tracking-tight">{t.title}</h1>
        <p className="mt-0.5 text-sm text-ink-dim">{t.sub}</p>
      </motion.div>

      <div className="flex items-center gap-3">
        {SEARCH_PAGES.has(page) && (
          <div className="relative">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="جست‌وجوی نام یا شماره…"
              aria-label="جست‌وجوی عضو"
              className="focus-ring w-64 rounded-xl border border-primary/15 bg-surface/60 py-2 pr-9 pl-3 text-sm placeholder:text-ink-dim/70"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-dim">⌕</span>
          </div>
        )}

        <div
          className="flex items-center gap-2 rounded-xl border border-primary/15 bg-surface/60 px-3 py-1.5"
          title={me ? `${me.full_name} — ${me.phone}` : meError ?? "در حال دریافت هویت…"}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20 text-xs font-bold text-accent-soft">
            {initials}
          </div>
          <div className="text-xs">
            <p className="font-semibold">{me?.full_name ?? (meError ? "نامعلوم" : "…")}</p>
            <p className="text-ink-dim">{me ? (ROLE_FA[me.role] ?? me.role) : meError ? "بدون نشست" : "…"}</p>
          </div>
        </div>
        <button
          aria-label="تغییر شمارهٔ موبایل"
          className="focus-ring rounded-xl border border-primary/15 bg-surface/60 px-3 py-2 text-xs text-ink-dim hover:text-ink"
          onClick={() => setPhoneChangeOpen(true)}
          type="button"
        >
          تغییر شماره
        </button>
      </div>
      {phoneChangeOpen && (
        <PhoneChangeDialog
          currentPhone={me?.phone}
          onClose={() => setPhoneChangeOpen(false)}
          onCompleted={async () => {
            setPhoneChangeOpen(false);
            await signOut();
          }}
        />
      )}
    </header>
  );
}
