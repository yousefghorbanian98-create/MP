/**
 * MEM-05 / PWA-34 — ثبت بازخورد ست از سمت عضو.
 *
 * قواعدی که عمداً پیاده شده‌اند (و تست دارند):
 * - نوشتن روی `POST /programs/sync/set-feedback` می‌رود، چون تنها قرارداد
 *   idempotent موجود است (`device_id:client_id` + `updated_at` با LWW).
 *   `POST /programs/set-feedback` هیچ کلید/نسخه‌ای ندارد و استفاده نشده است.
 * - «مهلت تمام شد» با «ثبت شد» یکی نیست: نتیجهٔ نامعلوم = شکست صریح + دکمهٔ تلاش
 *   دوباره، و تلاش دوباره **همان** `client_id`/`updated_at` را می‌فرستد.
 * - دوبار کلیک/دوبار ارسال: دکمه در حال ارسال غیرفعال است و سرور هم همان کلید را
 *   «unchanged» برمی‌گرداند، پس رکورد تکراری ساخته نمی‌شود.
 * - منبع حقیقت، پاسخ سرور است: پس از ثبت، `onRecorded` والد را وادار می‌کند
 *   آمادگی/حجم را از API دوباره بخواند؛ هیچ ردیفی از نوشتن محلی شمرده نمی‌شود.
 * - کنترل‌ها از کتابخانهٔ antd می‌آیند (Q11 — بودجهٔ ratchet: فایل تازه سهمیهٔ
 *   input خام ندارد).
 */
import { Alert, Button, Input, Tag } from "antd";
import { useRef, useState } from "react";
import { AuthError, syncSetFeedback, type MemberProgram } from "../lib/api";
import { now } from "../lib/clock";
import {
  buildPendingWrite,
  getDeviceId,
  sameValues,
  type PendingSetWrite,
  type SetValues,
} from "../lib/feedbackQueue";
import { fa } from "../lib/useApi";

const EMPTY: SetValues = {
  movementId: "",
  weight: 0,
  targetReps: 8,
  repsDone: 0,
  rir: null,
  soreness: null,
  setsDone: null,
  notes: "",
};

type Status = "idle" | "sending" | "saved" | "unchanged" | "error";

export interface SetFeedbackFormProps {
  memberId: number;
  program: MemberProgram;
  /** والد باید آمادگی/حجم را از API دوباره بخواند — نه از state محلی. */
  onRecorded: () => void;
  /** مهلت پاسخ سرور؛ در تست‌ها کوچک می‌شود تا مسیر timeout واقعی سنجیده شود. */
  timeoutMs?: number;
}

function Field({
  label,
  value,
  onChange,
  hint,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  hint?: string;
}) {
  return (
    <label className="block text-xs text-ink-dim">
      {label}
      <Input aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1" />
      {hint ? <span className="mt-1 block text-[11px] text-ink-dim">{hint}</span> : null}
    </label>
  );
}

export function SetFeedbackForm({ memberId, program, onRecorded, timeoutMs = 15000 }: SetFeedbackFormProps) {
  const [values, setValues] = useState<SetValues>(EMPTY);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const pending = useRef<PendingSetWrite | null>(null);
  const inFlight = useRef(false);

  function update<K extends keyof SetValues>(field: K, next: SetValues[K]) {
    setValues((prev) => ({ ...prev, [field]: next }));
    // تغییر مقدار = نوشتهٔ منطقی تازه؛ کلید قبلی نباید به این مقادیر بچسبد.
    pending.current = null;
    if (status !== "sending") setStatus("idle");
    if (message) setMessage(null);
  }

  function numberFrom(raw: string): number | null {
    if (raw.trim() === "") return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function numericText(value: number | null): string {
    return value === null ? "" : String(value);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (inFlight.current) return; // دوبار ارسال

    if (values.movementId.trim() === "") {
      setStatus("error");
      setMessage("شناسهٔ حرکت لازم است؛ بدون آن، بازخورد به هیچ حرکتی وصل نمی‌شود.");
      return;
    }

    inFlight.current = true;
    setStatus("sending");
    setMessage(null);

    const reusable = pending.current !== null && sameValues(pending.current.values, values);
    const write =
      reusable && pending.current
        ? pending.current
        : buildPendingWrite(values, program.id, { deviceId: getDeviceId(), at: now() });
    pending.current = write;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const result = await syncSetFeedback(memberId, [write.item], undefined, controller.signal);
      const unchanged = result.unchanged_keys.length > 0 && result.applied_keys.length === 0;
      setStatus(unchanged ? "unchanged" : "saved");
      setMessage(
        unchanged
          ? "این ست قبلاً در سرور ثبت شده بود؛ ارسال دوباره رکورد تکراری نساخت."
          : `ثبت شد: ${fa(result.applied_keys.length)} نوشته روی سرور اعمال شد (${result.rule_version}).`,
      );
      pending.current = null;
      // منبع حقیقت سرور است: آمادگی/حجم دوباره از API خوانده می‌شود.
      onRecorded();
    } catch (caught) {
      setStatus("error");
      if (caught instanceof AuthError) {
        setMessage("نشست معتبر نیست؛ دوباره با کد یک‌بارمصرف وارد شوید.");
      } else if (caught instanceof DOMException && caught.name === "AbortError") {
        setMessage("زمان پاسخ سرور گذشت — ثبت نشد. تلاش دوباره همان ست را می‌فرستد، نه ست تازه.");
      } else {
        setMessage(
          caught instanceof Error
            ? `${caught.message} — ثبت نشد.`
            : "ثبت نشد؛ وضعیت نامعلوم است و باید دوباره تلاش شود.",
        );
      }
      // مهم: `pending` پاک نمی‌شود؛ تلاش دوباره همان کلید idempotent را می‌برد.
    } finally {
      clearTimeout(timer);
      inFlight.current = false;
    }
  }

  const busy = status === "sending";

  return (
    <section aria-labelledby="set-feedback-title" className="space-y-3">
      <div>
        <h4 id="set-feedback-title" className="text-base font-semibold">
          ثبت بازخورد ست
        </h4>
        <p className="mt-1 text-xs text-ink-dim">
          این فرم روی <code>POST /api/v1/programs/sync/set-feedback</code> می‌نویسد، چون تنها قراردادی است که
          کلید idempotent دارد؛ ارسال دوباره رکورد تکراری نمی‌سازد.
        </p>
      </div>

      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
        <Field
          label="شناسهٔ حرکت"
          value={values.movementId}
          onChange={(next) => update("movementId", next)}
          hint="movement_id — همان شناسه‌ای که برنامه از سرور می‌دهد"
        />
        <Field
          label="بار"
          value={numericText(values.weight)}
          onChange={(next) => update("weight", numberFrom(next) ?? 0)}
          hint="کیلوگرم؛ صفر یعنی حرکت وزن‌بدن"
        />
        <Field
          label="تکرار هدف"
          value={numericText(values.targetReps)}
          onChange={(next) => update("targetReps", numberFrom(next) ?? 1)}
        />
        <Field
          label="تکرار انجام‌شده"
          value={numericText(values.repsDone)}
          onChange={(next) => update("repsDone", numberFrom(next) ?? 0)}
        />
        <Field label="RIR" value={numericText(values.rir)} onChange={(next) => update("rir", numberFrom(next))} />
        <Field
          label="درد عضلانی"
          value={numericText(values.soreness)}
          onChange={(next) => update("soreness", numberFrom(next))}
          hint="۰..۱۰ — خودگزارش"
        />

        <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
          <Button type="primary" htmlType="submit" disabled={busy} loading={busy}>
            {busy ? "در حال ارسال…" : "ثبت ست"}
          </Button>
          {status === "saved" ? <Tag color="green">ثبت شد</Tag> : null}
          {status === "unchanged" ? <Tag color="gold">قبلاً ثبت شده</Tag> : null}
          {message && status === "error" ? (
            <Alert type="error" showIcon role="alert" message={message} className="w-full" />
          ) : null}
          {message && status !== "error" ? (
            <span role="status" className="text-sm text-ink-dim">
              {message}
            </span>
          ) : null}
        </div>
      </form>
    </section>
  );
}
