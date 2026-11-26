import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { MemberTable } from "../components/MemberTable";
import { generateProgram, fetchAssessmentHistory, fetchAssessmentMatrix, fetchMembersSummary } from "../lib/api";
import { fa, useApi } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";

/** اعضا + پنل جزئیات با ورود/خروج انیمیشنی (AnimatePresence). */
const genderTabs = [
  { key: "all" as const, label: "همه" },
  { key: "male" as const, label: "آقایان" },
  { key: "female" as const, label: "بانوان" },
];

export function Members() {
  const motionPreset = useMotionPreset();
  const { selectedMemberId, selectMember, genderFilter, setGenderFilter, setPage } =
    useAppStore();
  const [busy, setBusy] = useState(false);
  const [genMsg, setGenMsg] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  async function buildProgram() {
    if (!member) return;
    setBusy(true);
    setGenError(null);
    setGenMsg(null);
    try {
      const p = await generateProgram(member.member_id, { goal: "hypertrophy" });
      setGenMsg(
        `برنامهٔ #${p.id} به‌صورت draft ساخته شد (موتور ${p.engine_version}) — برای تأیید به صفحهٔ برنامه‌ها بروید.`,
      );
    } catch (e) {
      setGenError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  // داده از API می‌آید (MemberTable خودش می‌خواند)؛ اینجا فقط برای پنل جزئیات
  const { data } = useApi((s) => fetchMembersSummary(undefined, s), []);
  const member = data?.items.find((m) => m.member_id === selectedMemberId) ?? null;

  const history = useApi(
    (s) => (member ? fetchAssessmentHistory(member.member_id, undefined, s) : Promise.resolve([])),
    [member?.member_id],
  );
  const latestAssessment = history.data?.[0] ?? null;
  const matrixState = useApi(
    (s) =>
      latestAssessment
        ? fetchAssessmentMatrix(latestAssessment.assessment_id, undefined, s)
        : Promise.resolve(null),
    [latestAssessment?.assessment_id],
  );
  const matrix = matrixState.data;
  const historyLoading = history.loading || matrixState.loading;
  const matrixError = matrixState.error ?? "ماتریس ارزیابی دریافت نشد";

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <div className="xl:col-span-2">
        <div className="mb-4 flex items-center gap-2">
          {genderTabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setGenderFilter(t.key)}
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
genderFilter === t.key
                ? "bg-primary text-bg"
                  : "bg-surface/70 text-ink-dim hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
          <span className="mr-auto text-[11px] text-ink-dim">تفکیک جنسیت (M41) — نمای کامل ادمین</span>
        </div>
        <MemberTable onSelect={(id) => selectMember(id)} />
      </div>

      <AnimatePresence mode="wait">
        {member ? (
          <motion.div
            key={member.member_id}
            {...motionPreset.slide}
            exit={
              motionPreset.reduced
                ? { opacity: 0, transition: motionPreset.fade.transition }
                : { opacity: 0, x: -20 }
            }
            transition={
              motionPreset.reduced
                ? motionPreset.fade.transition
                : { type: "spring", stiffness: 260, damping: 24 }
            }
            className="glass-card p-5"
          >
            <div className="flex items-center gap-3">
              <div
                className="flex h-14 w-14 items-center justify-center rounded-2xl text-lg font-bold text-white"
                style={{
                  background: `linear-gradient(135deg, hsl(${(member.member_id * 47) % 360} 60% 38%), hsl(${(member.member_id * 47) % 360} 55% 22%))`,
                }}
              >
                {(member.full_name || "?").slice(0, 1)}
              </div>
              <div>
                <h2 className="text-lg font-bold">{member.full_name || "بدون نام"}</h2>
                <p className="text-xs text-ink-dim">
                  {member.phone || "—"} · هدف: {member.goal} ·{" "}
                  <span className={member.gender === "female" ? "text-pink-400" : "text-sky-400"}>
                    {member.gender === "female" ? "بانو" : "آقا"}
                  </span>
                </p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-surface/70 p-3 text-center">
                <p className="text-2xl font-bold text-primary-light">
                  {member.days_left == null ? "—" : fa(member.days_left)}
                </p>
                <p className="text-xs text-ink-dim">روز باقی‌مانده</p>
              </div>
              <div className="rounded-xl bg-surface/70 p-3 text-center">
                <p className="text-2xl font-bold text-accent-soft">
                  {member.plan_name ?? "—"}
                </p>
                <p className="text-xs text-ink-dim">پلن فعلی</p>
              </div>
            </div>

            <h4 className="mt-5 text-sm font-semibold">
              ارزیابی ۱۴ محور
              {matrix && (
                <span className="mr-2 text-[11px] font-normal text-ink-dim">
                  {matrix.status} · {matrix.rule_versions?.score}
                </span>
              )}
            </h4>
            {historyLoading ? (
              <p className="mt-3 text-xs text-ink-dim">در حال دریافت…</p>
            ) : !latestAssessment ? (
              <p className="mt-3 rounded-lg bg-surface/50 p-3 text-xs text-ink-dim">
                این عضو هیچ ارزیابی ثبت‌شده‌ای ندارد — نمره‌ای نمایش داده نمی‌شود.
              </p>
            ) : matrix ? (
              <div className="mt-3 space-y-2">
                {matrix.axes.map((axis, i) => (
                  <div key={axis.axis} className="flex items-center gap-2">
                    <span className="w-28 shrink-0 text-[11px] text-ink-dim">{axis.name_fa}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                      {axis.score == null ? (
                        <div className="h-full w-full bg-[repeating-linear-gradient(45deg,rgba(156,163,175,0.25)_0_4px,transparent_4px_8px)]" />
                      ) : (
                        <motion.div
                          initial={motionPreset.reduced ? false : { width: 0 }}
                          animate={{ width: `${axis.score}%` }}
                          transition={
                            motionPreset.reduced
                              ? { duration: 0 }
                              : { delay: motionPreset.stagger(i), duration: 0.5 }
                          }
                          className="h-full rounded-full bg-gradient-to-l from-primary to-primary-light"
                        />
                      )}
                    </div>
                    <span className="w-10 text-left text-[11px] text-ink-dim">
                      {axis.score == null ? "نامعلوم" : fa(axis.score)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-xs text-danger">{matrixError}</p>
            )}

            <div className="mt-5 space-y-2">
              <div className="flex gap-2">
                <button
                  onClick={() => void buildProgram()}
                  disabled={busy || !member}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  {busy ? "در حال ساخت…" : "ساخت برنامه از موتور قواعد"}
                </button>
                <button
                  onClick={() => setPage("programs")}
                  className="btn-ghost flex-1"
                  title="ثبت ارزیابی در صفحهٔ برنامه‌ها و ارزیابی انجام می‌شود"
                >
                  دیدن برنامه‌ها
                </button>
              </div>
              {genMsg && (
                <p className="rounded-lg bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
                  {genMsg}
                </p>
              )}
              {genError && (
                <p className="rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300" role="alert">
                  {genError}
                </p>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            {...motionPreset.fade}
            exit={{ opacity: 0, transition: motionPreset.fade.transition }}
            className="glass-card flex flex-col items-center justify-center p-10 text-center"
          >
            <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-2xl">👤</div>
            <p className="text-sm text-ink-dim">یک عضو را از فهرست انتخاب کنید</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
