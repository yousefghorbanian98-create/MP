import { motion } from "framer-motion";
import { AttendanceChart } from "../components/AttendanceChart";
import { KpiCard } from "../components/KpiCard";
import { MemberTable } from "../components/MemberTable";
import { ScheduleTimeline } from "../components/ScheduleTimeline";
import { fetchAttendance, fetchKpis } from "../lib/api";
import { fa, useApi } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";

/**
 * داشبورد (M45-c1) — KPI از `/admin/kpis`، حضور از `/admin/attendance`.
 *
 * قاعدهٔ بازنمایی صادقانه: هر عددی که منبع واقعی ندارد نمایش داده نمی‌شود.
 * `class_fill_rate` وقتی ظرفیتی ثبت نشده باشد null است → «نامعلوم»، نه صفر.
 */
export function Dashboard() {
  const { setPage } = useAppStore();
  const kpis = useApi((s) => fetchKpis(undefined, s), []);
  const attendance = useApi((s) => fetchAttendance(7, undefined, s), []);

  const k = kpis.data;
  const a = attendance.data;

  const cards = [
    {
      id: "revenue",
      label: "درآمد وصول‌شده (ریال)",
      value: k ? k.revenue_paid_rial : null,
      hint: "جمع پرداخت‌های با وضعیت paid",
    },
    {
      id: "members",
      label: "اعضای فعال",
      value: k ? k.active_members : null,
      hint: k ? `از ${fa(k.members_total)} عضو ثبت‌شده` : "—",
    },
    {
      id: "new",
      label: "اعضای جدید (۳۰ روز)",
      value: k ? k.new_members_30d : null,
      hint: "تاریخ عضویت در ۳۰ روز اخیر",
    },
    {
      id: "fill",
      label: "ضریب پرشدن کلاس‌ها",
      value: k?.class_fill_rate != null ? Math.round(k.class_fill_rate * 100) : null,
      hint:
        k?.class_fill_rate == null
          ? "نامعلوم — ظرفیتی ثبت نشده"
          : `${fa(k.classes)} کلاس تعریف‌شده`,
      unit: k?.class_fill_rate != null ? "٪" : "",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      {kpis.needsToken && (
        <div className="glass-card border border-gold/30 p-4 text-sm text-gold">
          برای دیدن دادهٔ واقعی، توکن مدیر را در تنظیمات وارد کنید. هیچ عددی نمایش داده نمی‌شود
          تا دادهٔ واقعی بیاید.
        </div>
      )}
      {kpis.error && !kpis.needsToken && (
        <div className="glass-card border border-danger/30 p-4 text-sm text-danger">
          {kpis.error}
        </div>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c, i) =>
          kpis.loading ? (
            <div key={c.id} className="glass-card p-5">
              <p className="text-sm text-ink-dim">{c.label}</p>
              <div className="mt-2 text-3xl font-bold text-ink-dim">…</div>
            </div>
          ) : (
            <KpiCard
              key={c.id}
              label={c.label}
              value={c.value}
              unit={c.unit ?? ""}
              hint={c.hint}
              index={i}
            />
          ),
        )}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <div className="glass-card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">حضور ۷ روز اخیر</h3>
              {a && <span className="text-xs text-ink-dim">قاعده: {a.rule_version}</span>}
            </div>
            {attendance.loading ? (
              <p className="text-sm text-ink-dim">در حال دریافت…</p>
            ) : a && a.total_checkins === 0 ? (
              <p className="py-8 text-center text-sm text-ink-dim">
                هیچ چک‌اینی در ۷ روز اخیر ثبت نشده — صفر واقعی است، نه دادهٔ نمایشی.
              </p>
            ) : a ? (
              <>
                <div className="mb-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                  <Stat label="چک‌این" value={fa(a.total_checkins)} />
                  <Stat label="اعضای حاضر" value={fa(a.distinct_members)} />
                  <Stat label="جلسهٔ بسته" value={fa(a.closed_sessions)} />
                  <Stat label="جلسهٔ باز" value={fa(a.open_sessions)} />
                </div>
                <AttendanceChart series={a.series} />
              </>
            ) : (
              <p className="text-sm text-danger">{attendance.error}</p>
            )}
          </div>
        </div>
        <ScheduleTimeline />
      </section>

      <section>
        <MemberTable onSelect={() => setPage("members")} />
      </section>
    </motion.div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-surface/60 px-3 py-2">
      <p className="text-[11px] text-ink-dim">{label}</p>
      <p className="mt-0.5 text-lg font-bold">{value}</p>
    </div>
  );
}
