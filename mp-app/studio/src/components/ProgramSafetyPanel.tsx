/**
 * MEM-06 / PWA-35 — تفکیک واقعی چهار وضعیت غربالگری ایمنی در مسیر **عضو**.
 *
 * مشکل قبلی (`MemberTodayProgram`): برای هر سه وضعیت `blocked` / `needs_review` /
 * `clear` یک پیام واحد نمایش داده می‌شد («غربالگری ایمنی این برنامه خالی نیست»).
 * یعنی برنامه‌ای که موتور `blocked` علامت زده بود، به عضو می‌گفت «با مربی مرور کنید»،
 * نه «این برنامه با محدودیت شما ناسازگار است». این نقض معیار پذیرش MEM-06 است:
 * «هیچ safety flag صرفاً برای ثبت یا warning دور زده نشود».
 *
 * قاعده‌های این کامپوننت:
 * - چهار وضعیت چهار متن و چهار رنگ متفاوت دارند؛ هیچ‌کدام به دیگری fallback نمی‌شود.
 * - `clear` تنها وضعیتی است که می‌تواند بگوید «بدون ناسازگاری». `unknown` هرگز سبز نیست.
 * - دلایل (reason) همیشه **متن دیده‌شدنی** هستند، نه tooltip؛ tooltip برای موس است،
 *   نه برای کسی که با صفحه‌خوان یا روی موبایل برنامه را باز می‌کند.
 * - هیچ دادهٔ ساختگی ساخته نمی‌شود: هرچه هست از `safety_flags` سرور می‌آید.
 */
import { SafetyBadge, type SafetyFlags } from "./SafetyBadge";

export type SafetyStatus = "blocked" | "needs_review" | "unknown" | "clear";

/** وضعیت مؤثر: هر مقدار ناشناختهٔ سرور به «غربالگری نشده» تنزل می‌کند، نه به «بی‌خطر». */
export function safetyStatus(flags: SafetyFlags | null): SafetyStatus {
  const raw = flags?.status;
  if (
    raw === "blocked" ||
    raw === "needs_review" ||
    raw === "unknown" ||
    raw === "clear"
  ) {
    return raw;
  }
  return "unknown";
}

/**
 * اجرا فقط وقتی مجاز است که سرور صریحاً `status=clear` **و** `safe_to_generate=true`
 * بدهد. `{}`/`null` (غربالگری نشده) و هر پاسخ ناقص، اجرا را باز نمی‌کند.
 */
export function isExecutable(flags: SafetyFlags | null): boolean {
  return !!flags && flags.status === "clear" && flags.safe_to_generate === true;
}

/** دلیل انسانی و مخصوص هر وضعیت؛ در UI دیده می‌شود و متنش بین وضعیت‌ها یکسان نیست. */
export function executionBlockReason(flags: SafetyFlags | null): string {
  switch (safetyStatus(flags)) {
    case "blocked":
      return "موتور ایمنی این برنامه را با محدودیت‌های ثبت‌شدهٔ شما ناسازگار علامت زده است؛ تا بازبینی مربی، برنامه به‌عنوان برنامهٔ اجرایی ارائه نمی‌شود.";
    case "needs_review":
      return "این برنامه نیازمند بازبینی مربی است؛ تا ثبت نتیجهٔ بازبینی، اجرای آن مجاز نیست.";
    case "clear":
      return "سرور اجرای این برنامه را آزاد نکرده است (پرچم ایمنی ناقص است).";
    default:
      return "غربالگری ایمنی برای این برنامه انجام نشده است؛ «غربالگری نشده» یعنی نامعلوم، نه بی‌خطر.";
  }
}

const CARD: Record<SafetyStatus, string> = {
  blocked: "border-danger/40 bg-danger/10 text-danger",
  needs_review: "border-amber-400/40 bg-amber-400/10 text-amber-100",
  unknown: "border-primary/15 bg-surface/70 text-ink-dim",
  clear: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
};

function Reason({ text, id }: { text: string; id?: string }) {
  return (
    <p id={id} className="mt-2 text-xs leading-6">
      {text}
    </p>
  );
}

export function ProgramSafetyPanel({ flags }: { flags: SafetyFlags | null }) {
  const status = safetyStatus(flags);
  const ruleVersion = flags?.rule_version
    ? `نسخهٔ قاعده: ${flags.rule_version}`
    : "نسخهٔ قاعده در پاسخ نبود";
  const notes = flags?.notes ?? [];
  const highRisk = flags?.high_risk_patterns ?? [];

  return (
    <div className="space-y-2" data-safety-status={status}>
      <div className="flex flex-wrap items-center gap-2">
        <SafetyBadge flags={flags} />
        <span className="text-[11px] text-ink-dim">{ruleVersion}</span>
      </div>

      {status === "blocked" ? (
        <div
          role="alert"
          className={`rounded-xl border px-4 py-3 text-xs leading-6 ${CARD.blocked}`}
        >
          <p className="text-sm font-semibold">
            این برنامه برای شما ناسازگار است — اجرا نشود
          </p>
          {(flags?.blocked ?? []).map((item) => (
            <div key={`${item.constraint}-${item.label_fa}`} className="mt-2">
              <p className="font-semibold">محدودیت: {item.label_fa}</p>
              <p>
                حرکات مسدود:{" "}
                {item.blocked_exercises.length > 0
                  ? item.blocked_exercises.join("، ")
                  : "نامشخص"}
              </p>
              <p>
                جایگزین پیشنهادی:{" "}
                {item.alternatives.length > 0
                  ? item.alternatives.join("، ")
                  : "جایگزینی ثبت نشده"}
              </p>
              {item.advice_fa ? <p>توصیه: {item.advice_fa}</p> : null}
            </div>
          ))}
          {(flags?.blocked ?? []).length === 0 ? (
            <Reason text="سرور وضعیت را «ناسازگار» اعلام کرده ولی جزئیات محدودیت را برنگردانده است؛ فهرست حرکات مسدود نامعلوم است." />
          ) : null}
          <Reason text={`دلیل توقف اجرا: ${executionBlockReason(flags)}`} />
        </div>
      ) : null}

      {status === "needs_review" ? (
        <div
          role="status"
          className={`rounded-xl border px-4 py-3 text-xs leading-6 ${CARD.needs_review}`}
        >
          <p className="text-sm font-semibold">نیازمند بازبینی مربی</p>
          {flags?.headline ? <p>{flags.headline}</p> : null}
          {notes.map((note) => (
            <p key={note}>یادداشت موتور: {note}</p>
          ))}
          <Reason text={`دلیل توقف اجرا: ${executionBlockReason(flags)}`} />
        </div>
      ) : null}

      {status === "unknown" ? (
        <div
          role="status"
          className={`rounded-xl border px-4 py-3 text-xs leading-6 ${CARD.unknown}`}
        >
          <p className="text-sm font-semibold">غربالگری نشده — نه «بی‌خطر»</p>
          <p>
            سرور برای این برنامه نتیجهٔ غربالگری برنگردانده است. نبودِ پرچم به
            معنی تأیید ایمنی نیست؛ برای همین برنامه در این وضعیت اجرایی نیست.
          </p>
          <Reason text={`دلیل توقف اجرا: ${executionBlockReason(flags)}`} />
        </div>
      ) : null}

      {status === "clear" ? (
        <div
          role="status"
          className={`rounded-xl border px-4 py-3 text-xs leading-6 ${CARD.clear}`}
        >
          <p className="text-sm font-semibold">
            بدون ناسازگاری با محدودیت‌های ثبت‌شده
          </p>
          {flags?.headline ? <p>{flags.headline}</p> : null}
          <p>
            این نتیجه فقط دربارهٔ محدودیت‌های ثبت‌شده است؛ محدودیت ثبت‌نشده در
            غربالگری دیده نمی‌شود.
          </p>
        </div>
      ) : null}

      {highRisk.length > 0 ? (
        <p className="text-[11px] text-amber-200">
          حرکات پرخطر در برنامه: {highRisk.join("، ")}
        </p>
      ) : null}

      {flags?.disclaimer_fa ? (
        <p className="text-[11px] text-ink-dim">{flags.disclaimer_fa}</p>
      ) : null}
    </div>
  );
}
