import { motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { useState } from "react";
import { approveProgram, fetchProgramsSummary, rejectProgram } from "../lib/api";
import { SafetyBadge, parseSafety } from "../components/SafetyBadge";
import { ReadinessPanel } from "../components/ReadinessPanel";
import { VolumePanel } from "../components/VolumePanel";
import { ExerciseLibrary } from "../components/ExerciseLibrary";
import { AutoregPanel } from "../components/AutoregPanel";
import { fa, useApi } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";
import { toDate } from "../lib/clock";

/**
 * برنامه‌ها (M45-c2) — از `GET /programs` واقعی، نه mock.
 *
 * فقط برنامه‌های ثبت‌شده در DB نمایش داده می‌شوند. برچسب‌های عضلانی قبلی
 * («سینه/پا/پشت/بازو») ساختگی بودند چون داده‌شان در پاسخ نبود و حذف شدند.
 */
const statusMap: Record<string, { label: string; cls: string }> = {
  draft: { label: "در انتظار تأیید مربی", cls: "pill-gold" },
  approved: { label: "تأییدشده", cls: "pill-green" },
  rejected: { label: "ردشده", cls: "pill-red" },
};

const filters = [
  { key: null as string | null, label: "همه" },
  { key: "draft", label: "در انتظار" },
  { key: "approved", label: "تأییدشده" },
  { key: "rejected", label: "ردشده" },
];

export function Programs() {
  const motionPreset = useMotionPreset();
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  async function act(id: number, kind: "approve" | "reject") {
    setBusyId(id);
    setActionError(null);
    setActionMsg(null);
    try {
      if (kind === "approve") {
        await approveProgram(id);
        setActionMsg(`برنامهٔ #${id} تأیید شد.`);
      } else {
        const reason = window.prompt("دلیل رد برنامه (الزامی):", "") ?? "";
        if (!reason.trim()) {
          setActionError("رد برنامه بدون دلیل ثبت نمی‌شود.");
          return;
        }
        await rejectProgram(id, reason.trim());
        setActionMsg(`برنامهٔ #${id} رد شد.`);
      }
      reload();
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  const [status, setStatus] = useState<string | null>(null);
  // M61/D7 — عضو انتخاب‌شده در صفحهٔ «اعضا» منبع حقیقت پنل‌های پایین صفحه است.
  // قبلاً پنل حجم با `items[0].member_id` سوار می‌شد: مربی عضو B را انتخاب
  // می‌کرد و گزارش حجم عضو A را می‌دید، در حالی که ReadinessPanel کنارش
  // درست از B می‌خواند. دو پنل هم‌سایه با دو عضو = دادهٔ آموزشی غلط.
  const selectedMemberId = useAppStore((s) => s.selectedMemberId);
  const { data, loading, error, needsSession, reload } = useApi(
    (s) => fetchProgramsSummary(status, undefined, s),
    [status],
  );

  const items = data?.items ?? [];

  return (
    <>
      {actionMsg && (
        <p className="mb-3 rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          {actionMsg}
        </p>
      )}
      {actionError && (
        <p className="mb-3 rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300" role="alert">
          {actionError}
        </p>
      )}
      <motion.div
        {...motionPreset.rise}
        className="space-y-4"
      >
      <div className="glass-card flex items-center gap-3 border-accent/25 p-4">
        <span className="text-xl">⚖️</span>
        <p className="text-sm text-ink-dim">
          اعداد بار/ست/تکرار فقط از <b className="text-accent-soft">موتور قواعد قطعی</b> تولید
          می‌شوند (قانون G8)؛ مربی پیش از نمایش به عضو، برنامه را تأیید می‌کند.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {filters.map((f) => (
          <button
            key={f.label}
            onClick={() => setStatus(f.key)}
            className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
              status === f.key
                ? "bg-primary text-white"
                : "bg-surface/70 text-ink-dim hover:text-ink"
            }`}
          >
            {f.label}
            {f.key && data?.counts_by_status?.[f.key] != null
              ? ` (${fa(data.counts_by_status[f.key])})`
              : ""}
          </button>
        ))}
        {data && (
          <span className="mr-auto text-[11px] text-ink-dim">قاعده: {data.rule_version}</span>
        )}
      </div>

      {needsSession && (
        <div className="glass-card border border-gold/30 p-4 text-sm text-gold">
          نشست معتبر نیست — برای ادامه با کد یک‌بارمصرف وارد شوید.
        </div>
      )}
      {error && !needsSession && (
        <div className="glass-card flex items-center justify-between border border-danger/30 p-4">
          <p className="text-sm text-danger">{error}</p>
          <button onClick={reload} className="text-xs text-primary-light underline">
            تلاش دوباره
          </button>
        </div>
      )}
      {loading && <p className="text-sm text-ink-dim">در حال دریافت…</p>}
      {!loading && !error && items.length === 0 && (
        <p className="glass-card p-10 text-center text-sm text-ink-dim">
          هیچ برنامه‌ای با این فیلتر ثبت نشده — دادهٔ نمایشی ساخته نمی‌شود.
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {items.map((p, i) => (
          <motion.div
            key={p.id}
            {...motionPreset.rise}
            transition={{ ...motionPreset.rise.transition, delay: motionPreset.stagger(i) }}
            {...motionPreset.hover}
            className="glass-card-hover p-5"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{p.member_name || "بدون نام"}</h3>
                <p className="text-xs text-ink-dim">
                  هدف: {p.goal || "—"} · {fa(p.weeks_count)} هفته · نسخهٔ موتور{" "}
                  {p.engine_version || "—"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <SafetyBadge flags={parseSafety(p.safety_flags)} />
                <span className={(statusMap[p.status] ?? statusMap.draft).cls}>
                  {(statusMap[p.status] ?? { label: p.status }).label}
                </span>
              </div>
            </div>
            {(() => {
              const safety = parseSafety(p.safety_flags);
              if (!safety?.blocked?.length) return null;
              return (
                <div className="mt-3 space-y-1 rounded-lg bg-danger/10 p-3 text-[11px] text-danger">
                  {safety.blocked.map((b) => (
                    <p key={b.constraint}>
                      {b.label_fa}: {b.blocked_exercises.join("، ")} ممنوع — جایگزین:{" "}
                      {b.alternatives.join("، ")}
                    </p>
                  ))}
                </div>
              );
            })()}

            {p.llm_explanation && (
              <p className="mt-3 rounded-lg bg-surface/60 p-3 text-xs text-ink-dim">
                {p.llm_explanation}
              </p>
            )}
            {p.reject_reason && (
              <p className="mt-3 rounded-lg bg-danger/10 p-3 text-xs text-danger">
                دلیل رد: {p.reject_reason}
              </p>
            )}

            <div className="mt-4 flex items-center justify-between text-[11px] text-ink-dim">
              <span>
                {p.approved_at
                  ? `تأیید: ${toDate(p.approved_at).toLocaleDateString("fa-IR")}`
                  : "تأیید نشده"}
              </span>
              {p.status === "draft" && (
                <div className="flex gap-2">
                  <button
                    onClick={() => void act(p.id, "approve")}
                    disabled={busyId === p.id}
                    className="btn-primary px-3 py-1.5 text-xs disabled:opacity-50"
                  >
                    تأیید
                  </button>
                  <button
                    onClick={() => void act(p.id, "reject")}
                    disabled={busyId === p.id}
                    className="btn-ghost px-3 py-1.5 text-xs disabled:opacity-50"
                  >
                    رد
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>

    <div className="mt-4 space-y-4">
      {selectedMemberId === null ? (
        // یک پیام، نه دو تا: ReadinessPanel هم حالت خالی خودش را دارد و
        // اگر هر دو رندر شوند، کاربر دو کارت هم‌متن می‌بیند.
        <section className="glass-card p-6 text-center text-sm text-ink-dim">
          برای دیدن آمادگی و حجم تمرین، یک عضو را از صفحهٔ «اعضا» انتخاب کنید.
        </section>
      ) : (
        <>
          <VolumePanel memberId={selectedMemberId} />
          <ReadinessPanel />
        </>
      )}
    </div>
    <div className="mt-4 space-y-4">
      <AutoregPanel />
      <ExerciseLibrary />
    </div>
    </>
  );
}
