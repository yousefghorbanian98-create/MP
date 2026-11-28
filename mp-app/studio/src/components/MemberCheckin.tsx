/**
 * MEM-10 / PWA-39 — QR حضور در مسیر عضو.
 *
 * معیار پذیرش TODO: «عمر/انقضا، امضا یا قرارداد اعتبارسنجی، replay، duplicate،
 * عضو دیگر و fallback با server test بررسی شود … QR محلی به‌تنهایی حضور/هویت
 * اثبات نمی‌کند؛ face recognition اضافه نشود.»
 *
 * قرارداد واقعی (با `grep -n`، نه از حافظه):
 * - `modules/face_id/router.py:70-80` → `GET /api/v1/face/qr-token` توکن امضاشده
 *   برای **عضو لاگین‌شده** صادر می‌کند (`member = Member.user_id == user.id`).
 * - `app/security/jwt.py:40-56` → `type="checkin_qr"`، `jti` تصادفی، `exp = now+2min`.
 * - `modules/face_id/router.py:83-126` → ریدیم با `ensure_member_scope` (عضو دیگر ⇒ ۴۰۳)
 *   و گارد replay: پیش‌بررسی + ایندکس یکتا `uq_checkins_qr_jti_hash`
 *   (`db/models/face_id.py:52`) ⇒ ریدیم دوم ⇒ `409 qr_replayed`.
 * - سه حالت در backend آزموده شده‌اند: `tests/integration/test_m65_qr_security.py:144`
 *   (replay)، `:160` (توکن منقضی)، `:131` (عضو دیگر). این فایل UI آن‌ها را دوباره
 *   نمی‌سازد و **ادعای اثبات حضور نمی‌کند**.
 *
 * قاعده‌ها:
 * - UI فقط توکن صادر می‌کند و تاریخچهٔ سرور را نشان می‌دهد؛ **ریدیم** کار پذیرش/کیوسک است.
 * - هیچ «حضور ثبت شد ✅» نمایش داده نمی‌شود؛ متن صریح: تأیید نهایی با مربی/سیستم.
 * - توکن در حافظهٔ صفحه است، در localStorage ذخیره نمی‌شود (اثر انگشت حضور نشت نکند).
 * - face recognition در این کامپوننت وجود ندارد و صدا زده نمی‌شود.
 */
import { useEffect, useState } from "react";
import { toDate } from "../lib/clock";
import {
  ApiError,
  ForbiddenError,
  fetchCheckinQrToken,
  fetchMyCheckins,
  type MyCheckinHistory,
} from "../lib/api";

const HISTORY_SOURCE = "منبع: GET /api/v1/membership/me/checkins";
const TOKEN_SOURCE = "منبع: GET /api/v1/face/qr-token";

type History =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: MyCheckinHistory };

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return "دسترسی به تاریخچهٔ حضور مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "اطلاعات حضور از سرور دریافت نشد";
}

function stamp(iso: string | null): string {
  if (!iso) return "زمان ثبت نشده";
  // `toDate` از lib/clock است (قاعدهٔ no-restricted-syntax: بدون ساخت مستقیم Date).
  const date = toDate(iso);
  if (Number.isNaN(date.getTime())) return "زمان نامعتبر";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

export function MemberCheckin() {
  const [history, setHistory] = useState<History>({ kind: "loading" });
  const [token, setToken] = useState<string | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchMyCheckins(10, 0, undefined, controller.signal)
      .then((data) => setHistory({ kind: "ready", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHistory({ kind: "error", message: failureMessage(error) });
      });
    return () => controller.abort();
  }, []);

  async function issueToken() {
    setBusy(true);
    setTokenError(null);
    try {
      const result = await fetchCheckinQrToken();
      setToken(result.payload);
      // تاریخچه دوباره خوانده نمی‌شود: صدور توکن «حضور» نیست.
    } catch (error) {
      setTokenError(failureMessage(error));
      setToken(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="member-checkin-title" className="space-y-4">
      <div>
        <h3 id="member-checkin-title" className="text-base font-semibold">
          حضور (QR)
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          این کد برای پذیرش است. QR به‌تنهایی حضور یا هویت را اثبات نمی‌کند؛ تأیید نهایی با مربی/سیستم
          است و هر کد فقط یک‌بار قابل استفاده است.
        </p>
      </div>

      <div className="rounded-xl border border-primary/10 px-4 py-3">
        <button
          type="button"
          onClick={() => void issueToken()}
          disabled={busy}
          className="rounded-xl bg-primary/25 px-4 py-2 text-sm font-semibold disabled:opacity-60"
        >
          {busy ? "در حال صدور…" : "دریافت کد QR"}
        </button>

        {tokenError ? (
          <p role="alert" className="mt-2 text-sm text-danger">
            {tokenError}
          </p>
        ) : null}

        {token ? (
          <div className="mt-3 space-y-2" data-qr-issued="yes">
            <p className="text-xs text-ink-dim">
              کد زیر را به پذیرش نشان دهید. عمر آن کوتاه است (سرور `exp` دو دقیقه‌ای می‌گذارد) و بعد از
              اولین استفاده باطل می‌شود.
            </p>
            <code className="block break-all rounded-lg bg-surface/70 px-3 py-2 text-[11px]" data-qr-payload>
              {token}
            </code>
            <p className="text-[11px] text-ink-dim">
              این کد در مرورگر ذخیره نمی‌شود و با بستن صفحه از بین می‌رود. حضور شما برای این نشست ثبت
              شد؛ تأیید نهایی توسط مربی/سیستم.
            </p>
            <p className="text-[11px] text-ink-dim">{TOKEN_SOURCE}</p>
          </div>
        ) : null}
      </div>

      <div className="space-y-2">
        <h4 className="text-sm font-semibold">تاریخچهٔ حضور</h4>
        {history.kind === "error" ? (
          <p role="alert" className="text-sm text-danger">
            {history.message}
          </p>
        ) : history.kind === "loading" ? (
          <p role="status" className="text-sm text-ink-dim">
            در حال دریافت تاریخچه از سرور…
          </p>
        ) : history.data.items.length === 0 ? (
          <p role="status" className="text-sm text-ink-dim">
            سرور هیچ رکورد حضوری برنگرداند. این «حضور صفر» نیست؛ یعنی چیزی ثبت نشده است.
          </p>
        ) : (
          <ul className="space-y-1 text-xs text-ink-dim">
            {history.data.items.map((row) => (
              <li key={row.checkin_id} data-checkin-result={row.result}>
                {stamp(row.checked_in_at)} · روش: {row.method} · نتیجه: {row.result}
                {row.denial_reason ? ` · دلیل رد: ${row.denial_reason}` : ""}
                {row.checked_out_at ? ` · خروج: ${stamp(row.checked_out_at)}` : ""}
              </li>
            ))}
          </ul>
        )}
        {history.kind === "ready" ? (
          <>
            <p className="text-[11px] text-ink-dim">
              {history.data.has_more ? "رکوردهای بیشتری در سرور هست؛ صفحه‌بندی در این نما انجام نشده." : "همهٔ رکوردهای بازگشتی نمایش داده شد."}
            </p>
            <p className="text-[11px] text-ink-dim">{HISTORY_SOURCE}</p>
          </>
        ) : null}
      </div>
    </section>
  );
}
