import { motion } from "framer-motion";
import { DURATION, useMotionPreset } from "../lib/motion";
import { useState } from "react";
import { fetchCheckinFeed } from "../lib/api";
import { useApi } from "../lib/useApi";
import { toDate } from "../lib/clock";

/**
 * نمای زندهٔ چک‌این (M45-c2) — جریان ورودها از `GET /admin/checkins`.
 *
 * فهرست ثابت قبلی ساختگی بود (نام‌های محلی + زمان‌های دستی). اکنون فقط
 * چک‌این‌های واقعی نمایش داده می‌شوند، شامل ورودهای رد‌شده با دلیل رد.
 * خود اسکنر چهره یک شبیه‌سازی بصری است (دوربین مرورگر در دسترس نیست) و
 * همین را صریح می‌گوید.
 */
const methodLabel: Record<string, string> = {
  qr: "QR",
  face: "چهره",
  manual: "دستی",
};

export function CheckIn() {
  const motionPreset = useMotionPreset();
  const [scanning, setScanning] = useState(true);
  const { data, loading, error } = useApi((s) => fetchCheckinFeed(20, undefined, s), []);
  const feed = data?.items ?? [];

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <motion.div {...motionPreset.fade} className="glass-card relative overflow-hidden xl:col-span-3">
        <div className="relative flex h-[420px] items-center justify-center bg-[radial-gradient(600px_300px_at_50%_20%,rgba(0,184,106,0.12),transparent)]">
          {/* قاب تشخیص چهره */}
          <div className="relative h-64 w-52">
            <div className="absolute inset-0 rounded-[28px] border-2 border-primary/50" />
            {(["right-0 top-0 rounded-tr-[28px] border-t-2 border-r-2", "left-0 top-0 rounded-tl-[28px] border-t-2 border-l-2", "right-0 bottom-0 rounded-br-[28px] border-b-2 border-r-2", "left-0 bottom-0 rounded-bl-[28px] border-b-2 border-l-2"] as const).map((cls) => (
              <span key={cls} className={`absolute h-10 w-10 border-primary ${cls}`} />
            ))}
            {/*
              خط اسکن: تکرار بی‌پایان (repeat: Infinity) بدترین حالت برای
              حساسیت دهلیزی است. در حالت کاهش حرکت، حرکت رفت‌وبرگشتی حذف
              می‌شود و یک خط ثابت + تغییر وضعیت متنی جای آن را می‌گیرد —
              اطلاعات («در حال اسکن») از دست نمی‌رود، حرکت می‌رود.
            */}
            {scanning &&
              (motionPreset.reduced ? (
                <span
                  data-testid="scan-static"
                  className="absolute inset-x-4 top-1/2 h-px bg-primary/70"
                />
              ) : (
                <motion.span
                  className="absolute inset-x-4 top-4 h-px bg-gradient-to-l from-transparent via-primary to-transparent shadow-[0_0_18px_rgba(0,184,106,0.8)]"
                  animate={{ y: [0, 220, 0] }}
                  transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
                />
              ))}
            <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-30">◎</div>
          </div>

          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-center">
            <p className="text-sm text-ink-dim">
              {scanning ? "در حال اسکن..." : "اسکن متوقف شد"}
            </p>
            <p className="mt-1 text-[11px] text-ink-dim">
              شبیه‌سازی بصری — دوربین واقعی در این نسخه وصل نیست
            </p>
            <button onClick={() => setScanning((s) => !s)} className="btn-ghost mt-3 px-3 py-1.5 text-xs">
              {scanning ? "توقف اسکن" : "شروع اسکن"}
            </button>
          </div>
        </div>
      </motion.div>

      <div className="space-y-4 xl:col-span-2">
        <div className="glass-card p-5">
          <h3 className="mb-3 flex items-center justify-between text-base font-semibold">
            <span>ورودهای اخیر</span>
            {data && <span className="text-[11px] font-normal text-ink-dim">{data.rule_version}</span>}
          </h3>
          {loading && <p className="text-xs text-ink-dim">در حال دریافت…</p>}
          {error && <p className="rounded-lg bg-surface/60 p-3 text-xs text-danger">{error}</p>}
          {!loading && !error && feed.length === 0 && (
            <p className="rounded-lg bg-surface/60 p-3 text-xs text-ink-dim">
              هیچ ورودی ثبت نشده — دادهٔ نمایشی ساخته نمی‌شود.
            </p>
          )}
          <div className="space-y-3">
            {feed.map((f, i) => (
              <motion.div
                key={f.checkin_id}
                {...motionPreset.slide}
                transition={{ delay: i * 0.08 }}
                className="flex items-center justify-between rounded-xl bg-surface/60 px-3 py-2.5"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`h-2 w-2 rounded-full ${f.result === "ok" ? "bg-primary" : "bg-danger"}`}
                  />
                  <div>
                    <p className="text-sm font-medium">{f.member_name || "بدون نام"}</p>
                    <p className="text-[11px] text-ink-dim">
                      {methodLabel[f.method] ?? f.method}
                      {f.is_open ? " · در باشگاه" : ""}
                    </p>
                  </div>
                </div>
                <div className="text-left">
                  <p className="text-xs text-ink-dim">
                    {f.checked_in_at
                      ? toDate(f.checked_in_at).toLocaleTimeString("fa-IR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "—"}
                  </p>
                  {f.result !== "ok" && (
                    <p className="text-[11px] text-danger">{f.denial_reason || "رد شد"}</p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="glass-card border-accent/25 p-5">
          <h3 className="text-sm font-semibold">SLO گیت ورود</h3>
          <div className="mt-2 flex items-end justify-between">
            <p className="text-lg font-bold text-ink-dim">اندازه‌گیری‌نشده</p>
            <span className="pill-muted">نیازمند سنجش واقعی</span>
          </div>
          <p className="mt-2 text-[11px] text-ink-dim">
            عدد قبلی (۱.۴ ثانیه / ۹۹٪) ساختگی بود و حذف شد — تا اجرای benchmark واقعی روی
            دستگاه، هیچ ادعای SLO نمی‌شود.
          </p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface">
            <motion.div
              initial={motionPreset.reduced ? false : { width: 0 }}
              animate={{ width: "93%" }}
              transition={
                motionPreset.reduced ? { duration: DURATION.press } : { duration: DURATION.page }
              }
              className="h-full rounded-full bg-gradient-to-l from-primary to-accent"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
