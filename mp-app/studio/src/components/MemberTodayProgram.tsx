/**
 * MEM-04 / PWA-33 — برنامهٔ تأییدشدهٔ عضو، فقط از دادهٔ واقعی backend.
 *
 * قواعدی که این کامپوننت عمداً رعایت می‌کند:
 * - فقط برنامهٔ `approved` نمایش داده می‌شود. `draft`/`rejected` برنامهٔ اجرایی نیستند؛
 *   تعدادشان فقط به‌عنوان وضعیت سرور گزارش می‌شود، نه به‌عنوان برنامه.
 * - هر عدد یک منبع مکتوب دارد: `GET /api/v1/programs/member/{member_id}` برای
 *   `engine_version`/`approved_at`/حرکت‌ها و `GET …/readiness` برای آمادگی با
 *   `rule_version` خودِ سرور. هیچ عددی در کلاینت محاسبه نمی‌شود (نه مجموع ست، نه
 *   کالری، نه ۱RM) تا «منبع» چیزی بیش از یک ادعا نباشد.
 * - «امروز» از روی روزهای برنامه حدس زده نمی‌شود، چون قرارداد تاریخ شروع ندارد؛
 *   همین محدودیت روی صفحه نوشته می‌شود.
 * - نبود برنامه/آمادگی یک حالت تهیِ صادقانه است، نه صفر و نه KPI ساختگی.
 */
import type { MemberProgram, ReadinessReport } from "../lib/api";
import { SetFeedbackForm } from "./SetFeedbackForm";
import { fetchMe, fetchMemberPrograms, fetchReadiness } from "../lib/api";
import { formatMemberDateTime } from "../lib/memberAccount";
import { fa, useApi } from "../lib/useApi";

const PROGRAMS_SOURCE = "منبع: GET /api/v1/programs/member/{member_id}";
const READINESS_SOURCE = "منبع: GET /api/v1/programs/member/{member_id}/readiness";

const bandLabels: Record<string, string> = {
  ready: "آماده",
  monitor: "نیازمند پایش",
  fatigued: "خسته",
  insufficient: "داده کافی نیست",
};

const recommendationLabels: Record<string, string> = {
  increase: "افزایش تدریجی",
  keep: "حفظ وضعیت",
  deload: "کاهش حجم",
  insufficient: "بدون توصیه",
};

function SourceNote({ text }: { text: string }) {
  return <p className="mt-1 text-[11px] text-ink-dim">{text}</p>;
}

function Field({ label, value, source }: { label: string; value: string; source: string }) {
  return (
    <div className="rounded-xl border border-primary/10 px-4 py-3">
      <dt className="text-xs text-ink-dim">{label}</dt>
      <dd className="mt-1 text-sm font-semibold">{value}</dd>
      <SourceNote text={source} />
    </div>
  );
}

function newestApproved(programs: MemberProgram[]): MemberProgram | null {
  const approved = programs.filter((program) => program.status === "approved");
  if (approved.length === 0) return null;
  return approved.reduce((best, current) => (current.id > best.id ? current : best));
}

function ReadinessBlock({ report }: { report: ReadinessReport }) {
  const readiness = report.readiness;
  if (!readiness) {
    return (
      <div className="rounded-xl border border-primary/10 px-4 py-3">
        <p className="text-sm font-semibold">آمادگی: سنجیده نشد</p>
        <p role="status" className="mt-1 text-sm text-ink-dim">
          {report.reason}
        </p>
        <SourceNote text={READINESS_SOURCE} />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-primary/10 px-4 py-3">
      <p className="text-sm font-semibold">
        آمادگی: {readiness.score === null ? "امتیاز محاسبه نشد" : fa(readiness.score)}
        {" · "}
        {bandLabels[readiness.band] ?? readiness.band}
      </p>
      <p className="mt-1 text-sm text-ink-dim">
        توصیهٔ سرور: {recommendationLabels[readiness.recommendation] ?? readiness.recommendation}
        {readiness.actionable ? " (کاهش حجم پیشنهاد شده)" : ""}
      </p>
      {readiness.missing_signals.length > 0 ? (
        <p className="mt-1 text-xs text-ink-dim">
          سیگنال‌های غایب: {readiness.missing_signals.join("، ")}
        </p>
      ) : null}
      {report.data_counts ? (
        <p className="mt-1 text-xs text-ink-dim">
          بازخوردهای ثبت‌شده در سرور: {fa(report.data_counts.feedback_rows)} (۷ روز اخیر:{" "}
          {fa(report.data_counts.sets_last_7_days)})
        </p>
      ) : null}
      <SourceNote text={`${READINESS_SOURCE} · نسخهٔ قاعده: ${readiness.rule_version}`} />
    </div>
  );
}

export function MemberTodayProgram() {
  const profile = useApi((signal) => fetchMe(undefined, signal), []);
  const memberId = profile.data?.id ?? null;
  const programs = useApi(
    (signal) => (memberId === null ? Promise.resolve([]) : fetchMemberPrograms(memberId, undefined, signal)),
    [memberId],
  );
  const readiness = useApi(
    (signal) => (memberId === null ? Promise.resolve(null) : fetchReadiness(memberId, undefined, signal)),
    [memberId],
  );

  if (profile.loading) {
    return (
      <p role="status" className="text-sm text-ink-dim">
        در حال دریافت برنامهٔ عضو از سرور…
      </p>
    );
  }

  if (profile.error) {
    return (
      <p role="alert" className="text-sm text-danger">
        {profile.needsSession
          ? "نشست معتبر نیست؛ دوباره با کد یک‌بارمصرف وارد شوید."
          : "برنامهٔ عضو قابل دریافت نیست. اتصال را بررسی کنید و دوباره تلاش کنید."}
      </p>
    );
  }

  if (programs.loading) {
    return (
      <p role="status" className="text-sm text-ink-dim">
        در حال دریافت برنامه‌های تأییدشده…
      </p>
    );
  }

  if (programs.error) {
    return (
      <p role="alert" className="text-sm text-danger">
        {programs.needsSession
          ? "نشست معتبر نیست؛ دوباره با کد یک‌بارمصرف وارد شوید."
          : "فهرست برنامه‌ها از سرور دریافت نشد؛ هیچ برنامه‌ای نمایش داده نمی‌شود."}
      </p>
    );
  }

  if (programs.data !== null && !Array.isArray(programs.data)) {
    // پاسخ سرور با قرارداد فهرست برنامه نمی‌خواند؛ نمایش «فهرست خالی» در این حالت
    // همان دروغِ «برنامه‌ای ندارید» است، پس fail-closed با پیام صریح.
    return (
      <p role="alert" className="text-sm text-danger">
        پاسخ سرور با قرارداد فهرست برنامه نمی‌خواند؛ هیچ برنامه‌ای نمایش داده نمی‌شود.
      </p>
    );
  }

  const all = Array.isArray(programs.data) ? programs.data : [];
  const program = newestApproved(all);
  const pendingCount = all.filter((entry) => entry.status !== "approved").length;

  if (!program) {
    return (
      <section aria-labelledby="member-today-title" className="space-y-3">
        <h3 id="member-today-title" className="text-base font-semibold">
          برنامهٔ تأییدشده
        </h3>
        <p role="status" className="text-sm leading-7 text-ink-dim">
          هیچ برنامهٔ تأییدشده‌ای برای شما از سرور دریافت نشد. برنامهٔ تمرین، آمادگی، کالری یا عدد دیگری
          نمایش داده نمی‌شود تا مربی برنامه را تأیید کند.
        </p>
        {pendingCount > 0 ? (
          <div className="rounded-xl border border-primary/10 px-4 py-3">
            <p className="text-sm font-semibold">برنامه‌های در انتظار تأیید: {fa(pendingCount)}</p>
            <SourceNote text={`${PROGRAMS_SOURCE} · وضعیت‌های draft/rejected برنامهٔ اجرایی نیستند`} />
          </div>
        ) : null}
      </section>
    );
  }

  return (
    <section aria-labelledby="member-today-title" className="space-y-3">
      <div>
        <h3 id="member-today-title" className="text-base font-semibold">
          برنامهٔ تأییدشدهٔ شما
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          تاریخ شروع برنامه در API ثبت نمی‌شود؛ پس «امروز» از روی شمارهٔ هفته/روز حدس زده نمی‌شود.
        </p>
      </div>

      <dl className="grid gap-3 sm:grid-cols-2">
        <Field label="نسخهٔ موتور برنامه" value={program.engine_version} source={PROGRAMS_SOURCE} />
        <Field
          label="تاریخ تأیید مربی"
          value={program.approved_at ? formatMemberDateTime(program.approved_at) : "تأیید نشده (تاریخ ثبت نشده)"}
          source={PROGRAMS_SOURCE}
        />
        <Field label="هدف برنامه" value={program.goal} source={PROGRAMS_SOURCE} />
        <Field label="وضعیت گردش‌کار" value={program.status} source={PROGRAMS_SOURCE} />
      </dl>

      {program.safety_flags && program.safety_flags !== "{}" ? (
        <p className="rounded-xl border border-gold/30 px-4 py-3 text-xs text-ink-dim">
          غربالگری ایمنی این برنامه خالی نیست؛ پیش از اجرا با مربی مرور کنید.
        </p>
      ) : (
        <p className="text-[11px] text-ink-dim">
          غربالگری ایمنی برای این برنامه ثبت نشده است ({} یعنی انجام‌نشده، نه «بی‌خطر»).
        </p>
      )}

      {readiness.data ? <ReadinessBlock report={readiness.data} /> : null}

      <SetFeedbackForm
        memberId={memberId ?? program.member_id}
        program={program}
        onRecorded={() => readiness.reload()}
      />
      {readiness.error ? (
        <p role="alert" className="text-sm text-danger">
          آمادگی از سرور دریافت نشد؛ امتیازی نمایش داده نمی‌شود.
        </p>
      ) : null}

      <div className="space-y-3">
        {program.weeks.length === 0 ? (
          <p role="status" className="text-sm text-ink-dim">
            سرور برای این برنامه هیچ هفته‌ای برنگرداند.
          </p>
        ) : (
          program.weeks.map((week) => (
            <article key={week.id} className="rounded-xl border border-primary/10 px-4 py-3">
              <h4 className="text-sm font-semibold">
                هفتهٔ {fa(week.week_number)} — {week.focus}
              </h4>
              {week.exercises.length === 0 ? (
                <p className="mt-1 text-xs text-ink-dim">سرور برای این هفته حرکتی برنگرداند.</p>
              ) : (
                <ul className="mt-2 space-y-1 text-xs text-ink-dim">
                  {week.exercises.map((exercise) => (
                    <li key={exercise.id}>
                      روز {fa(exercise.day)} · حرکت #{fa(exercise.exercise_id)} · {fa(exercise.sets)} ست ×{" "}
                      {exercise.reps} تکرار · {fa(exercise.load_pct)}٪ بار · استراحت {fa(exercise.rest_seconds)} ثانیه
                    </li>
                  ))}
                </ul>
              )}
              <SourceNote text={PROGRAMS_SOURCE} />
            </article>
          ))
        )}
      </div>
    </section>
  );
}
