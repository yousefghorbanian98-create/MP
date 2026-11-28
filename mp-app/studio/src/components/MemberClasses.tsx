/**
 * MEM-09 / PWA-38 — کلاس و رزرو در مسیر عضو.
 *
 * معیار پذیرش TODO: «ظرفیت، reserve, cancel, conflict و duplicate با backend
 * واقعی و آزمون race پوشش داده شوند؛ دکمهٔ disabled در UI اثبات عدم overbooking نیست.»
 *
 * قرارداد واقعی (با `grep -n` تولید شده):
 * - `modules/classes/service.py:198-211` → هر کلاس با `capacity`، `confirmed`،
 *   `waitlisted`، `seats_left`، و برای عضو `member_booking_status`.
 * - `service.py:66-120` → `book()` با قفل کلاس، خطای `already_booked` برای
 *   رزرو تکراری، و `status = "confirmed" if confirmed < capacity else "waitlisted"`.
 * - `service.py:165-179` → وضعیت رزرو خود عضو از سرور خوانده می‌شود، نه از کلاینت.
 *
 * قاعده‌ها:
 * - «ظرفیت» همیشه از سرور به‌صورت عدد نمایش داده می‌شود (`confirmed/capacity`،
 *   `seats_left`, `waitlisted`). دکمهٔ disabled هیچ ادعایی دربارهٔ overbooking نمی‌سازد.
 * - بعد از هر رزرو/لغو، فهرست **از سرور دوباره خوانده می‌شود** (`GET /classes`) و
 *   پیام موفقیت از پاسخ سرور (`status`: confirmed/waitlisted) می‌آید، نه از حدس.
 * - سه حالت عضویت (تأییدشده / لیست انتظار / بدون رزرو) متن جدا دارند.
 * - خطای سرور (`already_booked`، ۴۰۳ و …) به‌صورت متن دیده‌شدنی می‌آید و حذف نمی‌شود.
 */
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  ForbiddenError,
  bookClass,
  cancelClassBooking,
  fetchClasses,
  fetchMe,
  type GymClassRow,
} from "../lib/api";

const SOURCE = "منبع: GET /api/v1/classes";

const bookingLabels: Record<string, string> = {
  confirmed: "رزرو شما: تأییدشده",
  waitlisted: "رزرو شما: در لیست انتظار",
};

type Load =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; classes: GymClassRow[] };

function num(value: number): string {
  return value.toLocaleString("fa-IR");
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return "دسترسی به کلاس‌ها مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "کلاس‌ها از سرور دریافت نشد";
}

export function MemberClasses({ memberId: memberIdProp }: { memberId?: number } = {}) {
  const [memberId, setMemberId] = useState<number | null>(memberIdProp ?? null);
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [action, setAction] = useState<{ classId: number; kind: "book" | "cancel" } | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (memberIdProp !== undefined) return;
    const controller = new AbortController();
    fetchMe(undefined, controller.signal)
      .then((profile) => setMemberId(profile.id))
      .catch((error: unknown) => setLoad({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [memberIdProp]);

  const reload = useCallback(async (signal?: AbortSignal) => {
    try {
      const classes = await fetchClasses(undefined, signal);
      setLoad({ kind: "ready", classes });
      return classes;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return null;
      setLoad({ kind: "error", message: failureMessage(error) });
      return null;
    }
  }, []);

  useEffect(() => {
    if (memberId === null) return;
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [memberId, reload]);

  async function mutate(classId: number, kind: "book" | "cancel", current?: string | null) {
    if (memberId === null) return;
    setAction({ classId, kind });
    setActionError(null);
    setNotice(null);
    try {
      const result =
        kind === "book"
          ? await bookClass(classId, memberId)
          : await cancelClassBooking(classId, memberId);
      // پیام از پاسخ سرور می‌آید؛ «confirmed» یعنی صندلی گرفته شد، «waitlisted» یعنی نه.
      setNotice(
        kind === "book"
          ? result.status === "confirmed"
            ? "رزرو شما توسط سرور تأیید شد."
            : "ظرفیت پر بود؛ سرور شما را در لیست انتظار گذاشت."
          : current === "waitlisted"
            ? "رزرو شما از لیست انتظار لغو شد."
            : "رزرو شما لغو شد؛ ارتقای لیست انتظار را سرور انجام می‌دهد.",
      );
      // حقیقت از سرور: ظرفیت و وضعیت رزرو دوباره خوانده می‌شود.
      await reload();
    } catch (error) {
      setActionError(failureMessage(error));
      await reload();
    } finally {
      setAction(null);
    }
  }

  if (load.kind === "error") {
    return (
      <section aria-labelledby="member-classes-title" className="space-y-3">
        <h3 id="member-classes-title" className="text-base font-semibold">
          کلاس و رزرو
        </h3>
        <p role="alert" className="text-sm text-danger">
          {load.message}
        </p>
      </section>
    );
  }

  if (load.kind === "loading") {
    return (
      <section aria-labelledby="member-classes-title" className="space-y-3">
        <h3 id="member-classes-title" className="text-base font-semibold">
          کلاس و رزرو
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت کلاس‌ها از سرور…
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="member-classes-title" className="space-y-4">
      <div>
        <h3 id="member-classes-title" className="text-base font-semibold">
          کلاس و رزرو
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          ظرفیت و وضعیت رزرو از سرور خوانده می‌شود؛ دکمهٔ غیرفعال در این صفحه اثبات «بدون overbooking»
          نیست — تصمیم نهایی با سرور است.
        </p>
      </div>

      {notice ? (
        <p role="status" className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-xs">
          {notice}
        </p>
      ) : null}
      {actionError ? (
        <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-2 text-xs">
          {actionError}
        </p>
      ) : null}

      {load.classes.length === 0 ? (
        <p role="status" className="text-sm text-ink-dim">
          سرور هیچ کلاسی برنگرداند.
        </p>
      ) : (
        <ul className="space-y-2">
          {load.classes.map((item) => {
            const booked = item.member_booking_status ?? null;
            const full = item.seats_left <= 0;
            const busy = action?.classId === item.id;
            return (
              <li
                key={item.id}
                data-class-id={item.id}
                data-seats-left={item.seats_left}
                data-member-booking={booked ?? "none"}
                className="rounded-xl border border-primary/10 px-4 py-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="text-sm font-semibold">{item.name}</h4>
                  <span className="text-[11px] text-ink-dim">{item.schedule_text}</span>
                </div>

                <p className="mt-2 text-xs text-ink-dim">
                  ظرفیت: {num(item.confirmed)} از {num(item.capacity)} · صندلی خالی: {num(item.seats_left)} ·
                  لیست انتظار: {num(item.waitlisted)}
                </p>
                <p className="mt-1 text-xs font-semibold">
                  {booked ? bookingLabels[booked] ?? `رزرو شما: ${booked}` : "رزرو شما: بدون رزرو"}
                </p>
                {full && !booked ? (
                  <p className="mt-1 text-[11px] text-amber-200">
                    ظرفیت پر است؛ اگر رزرو کنید، سرور شما را در لیست انتظار قرار می‌دهد.
                  </p>
                ) : null}

                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={busy || booked !== null}
                    onClick={() => void mutate(item.id, "book", booked)}
                    className="rounded-xl bg-primary/25 px-3 py-1 text-xs font-semibold disabled:opacity-60"
                  >
                    {busy && action?.kind === "book" ? "در حال رزرو…" : "رزرو"}
                  </button>
                  <button
                    type="button"
                    disabled={busy || booked === null}
                    onClick={() => void mutate(item.id, "cancel", booked)}
                    className="rounded-xl bg-surface/70 px-3 py-1 text-xs font-semibold disabled:opacity-60"
                  >
                    {busy && action?.kind === "cancel" ? "در حال لغو…" : "لغو رزرو"}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <p className="text-[11px] text-ink-dim">{SOURCE}</p>
    </section>
  );
}
