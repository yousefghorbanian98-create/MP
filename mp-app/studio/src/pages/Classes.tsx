import { useMemo } from "react";
import { motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { fetchCheckinFeed, fetchClasses } from "../lib/api";
import { useApi } from "../lib/useApi";
import { fa } from "../lib/useApi";
import { toDate } from "../lib/clock";

/**
 * STAFF-04 (PWA-43) — کلاس‌ها و حضور برای کارکنان، همه از سرور.
 *
 * قاعده‌هایی که این صفحه رعایت می‌کند (همان درس MEM-10/MEM-12):
 *
 *  ۱. **ظرفیت و شمارش رزرو از سرور است.** `GET /classes` هر کلاس را با
 *     `capacity`/`confirmed`/`waitlisted`/`seats_left` می‌دهد
 *     (`modules/classes/service.py:198-211`). هیچ عددی در مرورگر ساخته یا
 *     جمع زده نمی‌شود.
 *  ۲. **فهرست نام‌دار رزروها endpoint ندارد.** `GAP:` هیچ مسیری رزروهای یک
 *     کلاس را با نام عضو برنمی‌گرداند؛ پس این صفحه «roster» جعلی نمی‌سازد و
 *     نبودش را صریح می‌نویسد.
 *  ۳. **حضور ادعا نمی‌شود.** `POST /face/checkin` فقط توسط خود عضو (یا
 *     دستگاه پذیرش با توکن همان عضو) صدا زده می‌شود و `result`/`denial_reason`
 *     برمی‌گرداند؛ این صفحه هیچ دکمهٔ «حاضر شد» ندارد. آنچه نشان می‌دهد
 *     جریان واقعی `GET /admin/checkins` است و وضعیت هر ردیف **از سرور**
 *     خوانده می‌شود: `result=ok` ⇒ «ورود ثبت‌شده در سرور»، غیر آن ⇒ رد با
 *     دلیل. ردیف باز/بسته هم از `is_open` سرور می‌آید.
 */
export function Classes() {
  const motionPreset = useMotionPreset();
  const classes = useApi((s) => fetchClasses(undefined, s), []);
  const feed = useApi((s) => fetchCheckinFeed(15, undefined, s), []);

  const rows = useMemo(() => classes.data ?? [], [classes.data]);
  const recent = useMemo(() => feed.data?.items ?? [], [feed.data]);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <motion.div {...motionPreset.fade} className="glass-card overflow-hidden xl:col-span-2">
        <div className="flex items-center justify-between border-b border-primary/10 px-5 py-4">
          <h2 className="text-base font-semibold">کلاس‌ها — ظرفیت و رزرو</h2>
          <span className="text-xs text-ink-dim">
            {classes.loading ? "در حال دریافت…" : `${fa(rows.length)} کلاس`}
            {classes.data?.length ? " · منبع: سرور" : ""}
          </span>
        </div>

        {classes.error && (
          <p role="alert" className="border-b border-danger/20 px-5 py-3 text-xs text-danger">
            {classes.error}
          </p>
        )}

        {!classes.loading && !classes.error && rows.length === 0 && (
          <p className="px-5 py-10 text-center text-sm text-ink-dim">
            هیچ کلاسی ثبت نشده — دادهٔ نمایشی ساخته نمی‌شود.
          </p>
        )}

        <div className="divide-y divide-primary/5">
          {rows.map((c) => {
            const full = c.seats_left <= 0;
            return (
              <div key={c.id} className="flex flex-wrap items-center gap-3 px-5 py-3" data-testid={`class-${c.id}`}>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{c.name}</p>
                  <p className="truncate text-[11px] text-ink-dim">
                    {c.schedule_text || "زمان اعلام نشده"}
                    {c.coach_id == null ? " · مربی نامشخص" : ` · مربی #${fa(c.coach_id)}`}
                  </p>
                </div>
                <div className="text-left text-[11px] text-ink-dim">
                  <p>
                    ظرفیت {fa(c.capacity)} · تأییدشده {fa(c.confirmed)} · انتظار {fa(c.waitlisted)}
                  </p>
                  <p className={full ? "text-gold" : "text-emerald-300"}>
                    {full ? "ظرفیت پر — فقط لیست انتظار" : `${fa(c.seats_left)} جای خالی`}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <p className="border-t border-primary/10 px-5 py-3 text-[11px] text-ink-dim">
          GAP: فهرست نام‌دار رزروهای هر کلاس endpoint ندارد (نه در `api/routes.json`، نه در
          `modules/classes/router.py`) — این صفحه roster نمی‌سازد و شمارش‌ها را از سرور می‌خواند.
        </p>
      </motion.div>

      <motion.div {...motionPreset.fade} className="glass-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-primary/10 px-5 py-4">
          <h2 className="text-base font-semibold">آخرین ورودها</h2>
          <span className="text-xs text-ink-dim">{feed.loading ? "…" : `${fa(recent.length)} ردیف`}</span>
        </div>
        {feed.error && (
          <p role="alert" className="px-5 py-3 text-xs text-danger">
            {feed.error}
          </p>
        )}
        {!feed.loading && !feed.error && recent.length === 0 && (
          <p className="px-5 py-10 text-center text-sm text-ink-dim">
            ورودی ثبت نشده — «حاضر» ادعا نمی‌شود.
          </p>
        )}
        <div className="divide-y divide-primary/5">
          {recent.map((row) => {
            const accepted = row.result === "ok";
            return (
              <div key={row.checkin_id} className="px-5 py-3 text-xs" data-testid={`checkin-${row.checkin_id}`}>
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate font-semibold">{row.member_name || `عضو #${fa(row.member_id)}`}</p>
                  <span className={accepted ? "text-emerald-300" : "text-danger"}>
                    {accepted
                      ? row.is_open
                        ? "در باشگاه (باز)"
                        : "ورود ثبت‌شده در سرور"
                      : "رد شد"}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-ink-dim">
                  {row.checked_in_at ? toDate(row.checked_in_at).toISOString().slice(11, 16) : "زمان نامعلوم"}
                  {" · "}
                  {row.method === "qr" ? "QR" : row.method === "face" ? "چهره" : "دستی"}
                  {!accepted && row.denial_reason ? ` · دلیل سرور: ${row.denial_reason}` : ""}
                </p>
              </div>
            );
          })}
        </div>
        <p className="border-t border-primary/10 px-5 py-3 text-[11px] text-ink-dim">
          تأیید حضور توسط مربی endpoint ندارد؛ دکمه‌ای ساخته نمی‌شود. وضعیت هر ردیف از
          `GET /admin/checkins` خوانده می‌شود.
        </p>
      </motion.div>
    </div>
  );
}
