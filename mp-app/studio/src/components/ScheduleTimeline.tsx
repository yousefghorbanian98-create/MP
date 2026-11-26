import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { API_BASE, AuthError, ForbiddenError } from "../lib/api";
import { getAccessToken, sessionFetch } from "../lib/session";
import { useMotionPreset } from "../lib/motion";

/**
 * برنامهٔ امروز (M45-c2) — از `GET /classes` واقعی.
 *
 * قبلاً از `data/mock.ts` می‌آمد و «ارزیابی/تمدید» جعلی نشان می‌داد.
 * اکنون فقط کلاس‌های واقعیِ تعریف‌شده نمایش داده می‌شوند؛ اگر کلاسی نباشد،
 * همان را می‌گوید.
 */
interface ClassRow {
  id: number;
  name: string;
  capacity: number;
  schedule_text: string | null;
  coach_id: number | null;
  confirmed?: number;
  waitlisted?: number;
}

export function ScheduleTimeline() {
  const motionPreset = useMotionPreset();
  const [rows, setRows] = useState<ClassRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    const token = getAccessToken();
    sessionFetch(`${API_BASE}/classes`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: ctrl.signal,
    })
      .then(async (r) => {
        if (r.status === 401) throw new AuthError("نشست معتبر نیست — با کد یک‌بارمصرف دوباره وارد شوید");
        if (r.status === 403) throw new ForbiddenError("نقش شما اجازهٔ دیدن کلاس‌ها را ندارد");
        if (!r.ok) throw new Error(`خطای ${r.status}`);
        return (await r.json()) as ClassRow[];
      })
      .then(setRows)
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setError(e instanceof Error ? e.message : "خطای ناشناخته");
      });
    return () => ctrl.abort();
  }, []);

  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-base font-semibold">کلاس‌های باشگاه</h3>
        <span className="text-xs text-ink-dim">
          {rows ? `${rows.length.toLocaleString("fa-IR")} کلاس` : ""}
        </span>
      </div>

      {error ? (
        <p className="rounded-lg bg-surface/60 p-3 text-xs text-danger">{error}</p>
      ) : rows === null ? (
        <p className="text-xs text-ink-dim">در حال دریافت…</p>
      ) : rows.length === 0 ? (
        <p className="rounded-lg bg-surface/60 p-3 text-xs text-ink-dim">
          هیچ کلاسی تعریف نشده — برنامهٔ نمایشی ساخته نمی‌شود.
        </p>
      ) : (
        <ol className="relative space-y-4 border-r border-primary/15 pr-4">
          {rows.slice(0, 6).map((c, i) => (
            <motion.li
              key={c.id}
              {...motionPreset.slide}
              transition={{ ...motionPreset.slide.transition, delay: motionPreset.stagger(i) }}
              className="relative"
            >
              <span className="absolute -right-[21px] top-1.5 h-2.5 w-2.5 rounded-full bg-primary shadow-glow" />
              <p className="text-xs text-ink-dim">{c.schedule_text ?? "زمان نامشخص"}</p>
              <p className="text-sm font-semibold">{c.name}</p>
              <p className="text-[11px] text-ink-dim">
                ظرفیت {c.capacity.toLocaleString("fa-IR")}
                {c.confirmed != null ? ` · ثبت‌نام ${c.confirmed.toLocaleString("fa-IR")}` : ""}
                {c.waitlisted ? ` · انتظار ${c.waitlisted.toLocaleString("fa-IR")}` : ""}
              </p>
            </motion.li>
          ))}
        </ol>
      )}
    </div>
  );
}
