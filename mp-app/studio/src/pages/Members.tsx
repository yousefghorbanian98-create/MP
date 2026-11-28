import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { MemberTable } from "../components/MemberTable";
import { Input, InputNumber, Select } from "antd";
import {
  fetchAssessmentHistory,
  fetchAssessmentMatrix,
  fetchMemberDetail,
  fetchMembersSummary,
  generateProgram,
  updateMember,
} from "../lib/api";
import { now, toDate } from "../lib/clock";
import { fa, useApi } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";
import { navigateToPage } from "../lib/navigation";

/** اعضا + پنل جزئیات با ورود/خروج انیمیشنی (AnimatePresence). */
const genderTabs = [
  { key: "all" as const, label: "همه" },
  { key: "male" as const, label: "آقایان" },
  { key: "female" as const, label: "بانوان" },
];

export function Members() {
  const motionPreset = useMotionPreset();
  const { selectedMemberId, selectMember, genderFilter, setGenderFilter } = useAppStore();
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
  // صفحه‌بندیِ واقعی نیاز به `offset` دارد و `members-summary` آن را ندارد
  // (GAP: STAFF-02) — پس فقط سقف صفحه از سرور انتخاب می‌شود، نه شمارهٔ صفحه.
  const [limit, setLimit] = useState<number>(200);
  // داده از API می‌آید (MemberTable خودش می‌خواند)؛ اینجا فقط برای پنل جزئیات
  const { data, reload: reloadSummary } = useApi(
    (s) => fetchMembersSummary(undefined, s, undefined, limit),
    [limit],
  );
  const member = data?.items.find((m) => m.member_id === selectedMemberId) ?? null;

  // پروندهٔ عضو از سرور (`GET /members/{id}`) — منبع فرم ویرایش، نه ردیف فهرست.
  const detail = useApi(
    (s) => (member ? fetchMemberDetail(member.member_id, undefined, s) : Promise.resolve(null)),
    [member?.member_id],
  );
  const [draft, setDraft] = useState<{ goal: string; height: string; constraints: string }>({
    goal: "",
    height: "",
    constraints: "",
  });
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  // اگر کاربر وسط تایپ است، رسیدن پاسخ detail نباید ویرایشش را پاک کند.
  const [dirty, setDirty] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [readbackNote, setReadbackNote] = useState<string | null>(null);

  // فرم با دادهٔ سرور پر می‌شود (هر بار که پرونده تازه برسد).
  const detailStamp = detail.data ? `${detail.data.id}:${detail.data.goal}:${detail.data.height_cm}:${detail.data.constraints}` : "";
  useEffect(() => {
    if (!detail.data || dirty) return;
    setDraft({
      goal: detail.data.goal ?? "",
      height: detail.data.height_cm == null ? "" : String(detail.data.height_cm),
      constraints: detail.data.constraints ?? "",
    });
    // پیام «ذخیره شد» پاک نمی‌شود: آن پیام شاهدِ بازخوانی از سرور است و فقط
    // با ویرایش بعدی کاربر (onChange) کنار می‌رود.
    setSaveState((prev) => (prev === "saved" ? prev : "idle"));
    // عمدی: فقط وقتی *محتوای* پرونده عوض شود فرم بازنویسی می‌شود، نه با هر
    // تغییر هویت شیء — وگرنه تایپ کاربر وسط ویرایش پاک می‌شد.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detailStamp]);

  async function saveProfile() {
    if (!member) return;
    setSaveState("saving");
    setSaveError(null);
    setReadbackNote(null);
    const patch: { goal?: string; height_cm?: number; constraints?: string } = { goal: draft.goal.trim() };
    if (draft.height.trim()) patch.height_cm = Number(draft.height.trim());
    patch.constraints = draft.constraints;
    try {
      await updateMember(member.member_id, patch);
      // ادعای ذخیره پیش از بازخوانی ساخته نمی‌شود؛ مقدار نمایش‌داده‌شده از سرور است.
      const fresh = await fetchMemberDetail(member.member_id);
      const matches = fresh.goal === (patch.goal ?? "") && (patch.height_cm === undefined || fresh.height_cm === patch.height_cm);
      setReadbackNote(matches ? "ذخیره شد — از سرور بازخوانی شد" : "سرور مقدار دیگری برگرداند؛ همان نمایش داده می‌شود");
      setSaveState(matches ? "saved" : "error");
      setDirty(false);
      if (!matches) setSaveError("پاسخ سرور با مقدار ارسالی نمی‌خواند");
      detail.reload();
      reloadSummary();
    } catch (e) {
      setSaveState("error");
      setSaveError((e as Error).message);
    }
  }

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
  // کهنگیِ دادهٔ فهرست: `generated_at` از سرور می‌آید؛ بیش از ۵ دقیقه ⇒ stale.
  const summaryAgeMinutes = data ? (now().getTime() - toDate(data.generated_at).getTime()) / 60_000 : 0;
  const summaryStale = Boolean(data) && summaryAgeMinutes > 5;
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
          <label className="flex items-center gap-2 text-[11px] text-ink-dim">
            سقف صفحه
            <Select
              size="small"
              value={limit}
              onChange={(value: number) => setLimit(value)}
              options={[
                { value: 50, label: "۵۰" },
                { value: 100, label: "۱۰۰" },
                { value: 200, label: "۲۰۰" },
              ]}
              data-testid="members-limit"
            />
          </label>
        </div>
        {summaryStale && (
          <p
            role="status"
            data-testid="members-stale"
            className="mb-3 rounded-lg border border-gold/30 bg-gold/10 px-3 py-2 text-[11px] text-gold"
          >
            این فهرست تازه نیست — از سرور {fa(Math.floor(summaryAgeMinutes))} دقیقه پیش تولید شده؛
            برای مقدار فعلی دوباره بخوانید.
          </p>
        )}
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

            <div className="mt-5 rounded-xl border border-primary/15 bg-surface/40 p-3">
              <h4 className="text-sm font-semibold">
                ویرایش پروفایل (STAFF-02)
                <span className="mr-2 text-[11px] font-normal text-ink-dim">
                  {detail.loading ? "در حال خواندن از سرور…" : detail.error ? `خطا: ${detail.error}` : "مقادیر از سرور"}
                </span>
              </h4>
              <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
                <label className="text-[11px] text-ink-dim">
                  هدف
                  <Input
                    data-testid="member-goal"
                    className="mt-1"
                    value={draft.goal}
                    onChange={(e) => {
                      setDirty(true);
                      setReadbackNote(null);
                      setSaveError(null);
                      setDraft({ ...draft, goal: e.target.value });
                    }}
                  />
                </label>
                <label className="text-[11px] text-ink-dim">
                  قد (سانتی‌متر)
                  <InputNumber
                    data-testid="member-height"
                    className="mt-1 w-full"
                    min={100}
                    max={250}
                    value={draft.height === "" ? null : Number(draft.height)}
                    onChange={(value) => {
                      setDirty(true);
                      setReadbackNote(null);
                      setSaveError(null);
                      setDraft({ ...draft, height: value == null ? "" : String(value) });
                    }}
                  />
                </label>
                <label className="text-[11px] text-ink-dim">
                  محدودیت‌ها (JSON سرور)
                  <Input
                    data-testid="member-constraints"
                    className="mt-1"
                    value={draft.constraints}
                    onChange={(e) => {
                      setDirty(true);
                      setReadbackNote(null);
                      setSaveError(null);
                      setDraft({ ...draft, constraints: e.target.value });
                    }}
                  />
                </label>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <button
                  onClick={() => void saveProfile()}
                  disabled={saveState === "saving" || !detail.data}
                  className="btn-ghost text-xs disabled:opacity-50"
                >
                  {saveState === "saving" ? "در حال ذخیره…" : "ذخیره و بازخوانی از سرور"}
                </button>
                {readbackNote && (
                  <span
                    data-testid="member-save-note"
                    className={`text-[11px] ${saveState === "saved" ? "text-emerald-300" : "text-gold"}`}
                  >
                    {readbackNote}
                  </span>
                )}
                {saveError && (
                  <span role="alert" className="text-[11px] text-rose-300">
                    {saveError}
                  </span>
                )}
              </div>
            </div>

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
                  onClick={() => navigateToPage("programs")}
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
