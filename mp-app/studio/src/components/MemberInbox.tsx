/**
 * MEM-15 / PWA-3E — جعبهٔ اعلان (inbox) عضو.
 *
 * معیار پذیرش TODO (`TODO-PWA-RELEASE-2026-11-23.fa.md:243`): «فهرست/خوانده‌شدن
 * با scope کاربر و recovery بعد از اتصال. inbox موجود به معنی push/SMS ارسال‌شده
 * یا مشاهده‌شده نیست.»
 *
 * قرارداد واقعی (با `grep -n`):
 * - `modules/notification/router.py:22-31` → `GET /notifications/member/{id}` با
 *   `unread_only`؛ `service.py:36-50` → مرتب `id desc` و `ensure_member_scope`
 *   (دامنهٔ عضو سمت سرور).
 * - `router.py:34-37` + `service.py:53-64` → `POST /notifications/{id}/read`،
 *   ایدمپوتنت (فقط وقتی `read_at` خالی است می‌نویسد) و با همان کنترل مالکیت.
 * - `schemas.py:21-31` → `channel`, `kind`, `read_at`, `created_at`؛
 *   `db/models/notification.py:22` → پیش‌فرض کانال `inapp`.
 *
 * قاعده‌ها:
 * - `channel` صریح نمایش داده می‌شود: `inapp` یعنی اعلان درون‌برنامه‌ای، نه
 *   «پیامک/push تحویل شد». هیچ ادعای تحویل روی دستگاه در این صفحه نیست.
 * - «خوانده شد» فقط از پاسخ/بازخوانی سرور می‌آید، نه از کلیک.
 * - تعداد خوانده‌نشده از همان فهرست سرور شمرده می‌شود و منبعش نوشته شده است.
 * - ۴۰۳ ⇒ fail-closed، صفر ردیف.
 */
import { Button, Empty, Spin, Tag } from "antd";
import { useCallback, useEffect, useState } from "react";
import { toDate } from "../lib/clock";
import {
  ApiError,
  ForbiddenError,
  fetchMe,
  fetchMyNotifications,
  markNotificationRead,
  type MemberNotification,
} from "../lib/api";

const SOURCE = "منبع: GET /api/v1/notifications/member/{member_id}";

const kindLabels: Record<string, string> = {
  renewal: "تمدید",
  workout: "تمرین",
  reassessment: "ارزیابی مجدد",
  general: "عمومی",
};

function stamp(iso: string | null): string {
  if (!iso) return "بدون زمان";
  const date = toDate(iso);
  if (Number.isNaN(date.getTime())) return "زمان نامعتبر";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError)
    return "دسترسی به اعلان‌های این حساب مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "اعلان‌ها از سرور دریافت نشد";
}

export function MemberInbox() {
  const [memberId, setMemberId] = useState<number | null>(null);
  const [rows, setRows] = useState<MemberNotification[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  // خطای «علامت‌گذاری» فهرست را پاک نمی‌کند؛ یک کلیک ناموفق نباید صفحه را خالی کند.
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchMe(undefined, controller.signal)
      .then((profile) => setMemberId(profile.id))
      .catch((err: unknown) => setError(failureMessage(err)));
    return () => controller.abort();
  }, []);

  const load = useCallback((id: number, signal?: AbortSignal) => {
    return fetchMyNotifications(id, false, undefined, signal)
      .then((data) => {
        setRows(Array.isArray(data) ? data : []);
        setError(null);
      })
      .catch((err: unknown) => setError(failureMessage(err)));
  }, []);

  useEffect(() => {
    if (memberId === null) return;
    const controller = new AbortController();
    void load(memberId, controller.signal);
    return () => controller.abort();
  }, [memberId, load]);

  async function markRead(row: MemberNotification) {
    setBusyId(row.id);
    setActionError(null);
    try {
      await markNotificationRead(row.id);
      // «خوانده شد» از سرور خوانده می‌شود؛ حالت ردیف از کلیک ساخته نمی‌شود.
      if (memberId !== null) await load(memberId);
    } catch (err) {
      setActionError(failureMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  const title = <h3 className="text-base font-semibold">اعلان‌های من</h3>;

  if (error) {
    return (
      <section aria-labelledby="member-inbox-title" className="space-y-3">
        <h3 id="member-inbox-title" className="text-base font-semibold">
          اعلان‌های من
        </h3>
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      </section>
    );
  }

  if (rows === null) {
    return (
      <section aria-labelledby="member-inbox-title" className="space-y-3">
        <h3 id="member-inbox-title" className="text-base font-semibold">
          اعلان‌های من
        </h3>
        <Spin /> <span className="text-sm text-ink-dim">در حال دریافت اعلان‌ها از سرور…</span>
      </section>
    );
  }

  const unread = rows.filter((row) => row.read_at === null).length;

  return (
    <section aria-labelledby="member-inbox-title" className="space-y-4">
      <div>
        {title}
        <p className="mt-1 text-xs text-ink-dim">
          این جعبهٔ «اعلان درون‌برنامه‌ای» است. وجود یا خواندن یک اعلان اینجا به معنای ارسال
          push/SMS یا تحویل و مشاهدهٔ آن روی دستگاه نیست؛ آن مسیر جداگانه تصمیم و تست می‌خواهد.
        </p>
        <p className="text-[11px] text-ink-dim">{SOURCE}</p>
      </div>

      {actionError ? (
        <p role="alert" className="text-xs text-danger" data-action-error>
          علامت‌گذاری انجام نشد: {actionError}
        </p>
      ) : null}

      <p className="text-xs" data-unread-count={unread}>
        خوانده‌نشده: {unread.toLocaleString("fa-IR")} از {rows.length.toLocaleString("fa-IR")} اعلان
        (شمارش از همان فهرست سرور است).
      </p>

      {rows.length === 0 ? (
        <Empty description="سرور هیچ اعلانی برای این حساب برنگرداند — یعنی اعلانی ثبت نشده است، نه اینکه پیامکی ارسال شده یا نشده." />
      ) : (
        <ul className="space-y-2">
          {rows.map((row) => (
            <li
              key={row.id}
              className="space-y-1 rounded-lg border border-primary/10 px-3 py-2 text-xs"
              data-notification-id={row.id}
              data-read={row.read_at === null ? "no" : "yes"}
              data-channel={row.channel}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold">{row.title}</span>
                <span className="flex items-center gap-2 text-ink-dim">
                  <Tag>{kindLabels[row.kind] ?? row.kind}</Tag>
                  <Tag color={row.channel === "inapp" ? "default" : "blue"}>
                    کانال: {row.channel === "inapp" ? "درون‌برنامه‌ای" : row.channel}
                  </Tag>
                </span>
              </div>
              {row.body ? <p className="text-ink-dim">{row.body}</p> : null}
              <p className="text-[11px] text-ink-dim">
                ثبت: {stamp(row.created_at)}
                {row.read_at === null ? " · خوانده نشده" : ` · خوانده‌شده در ${stamp(row.read_at)}`}
              </p>
              {row.read_at === null ? (
                <Button
                  size="small"
                  loading={busyId === row.id}
                  onClick={() => void markRead(row)}
                  data-mark-read
                >
                  علامت‌گذاری به‌عنوان خوانده‌شده
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      <p className="text-[11px] text-ink-dim">
        کانال هر اعلان از فیلد `channel` سرور می‌آید؛ `inapp` یعنی فقط همین صفحه. هیچ تحویل
        push/SMS در این UI اثبات یا ادعا نمی‌شود.
      </p>
    </section>
  );
}
