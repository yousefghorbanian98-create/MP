/**
 * MEM-11 / PWA-3A — کیف پول و تاریخچهٔ مالی عضو.
 *
 * معیار پذیرش TODO: «مبلغ canonical backend، ترتیب، pagination، ریال و ownership؛
 * serialization عددی بدون float/گردکردن/unsafe integer JavaScript. هر رویداد
 * مالی منبع و وضعیت داشته باشد.»
 *
 * قرارداد واقعی (با `grep -n`):
 * - `modules/payments/router.py:228-241` → `GET /payments/ledger/{member_id}` با
 *   `balance_rial`، `reconcile{wallet_balance_rial, ledger_balance_rial, matches,
 *   difference_rial}` و `entries[]`.
 * - `modules/payments/ledger.py:86-95` → ترتیب `id desc` و `limit=200`؛ **offset ندارد**
 *   ⇒ صفحه‌بندی واقعی وجود ندارد و UI همین را می‌گوید.
 * - `ledger.py:189-203` → `serialize()` با `amount_rial` (عدد صحیح ریال)، `kind`،
 *   `source_type`، `source_id`، `reverses_entry_id`، `reversed_by_id`، `created_at`.
 * - `ledger.py:108-125` → `reconcile` اختلاف کیف پول و دفتر را برمی‌گرداند.
 *
 * قاعده‌ها:
 * - هیچ محاسبه‌ای در کلاینت: موجودی از `balance_rial` سرور می‌آید، نه جمع ردیف‌ها.
 * - مبلغ عدد صحیح ریال است؛ در UI با `fa-IR` گروه‌بندی می‌شود و **تقسیم/گرد کردن**
 *   انجام نمی‌شود.
 * - اگر `reconcile.matches === false` ⇒ هشدار قرمز با اختلاف؛ پنهان نمی‌شود.
 * - ردیف معکوس‌شده با `reversed_by_id` علامت می‌خورد؛ ردیف معکوس‌کننده با
 *   `reverses_entry_id` مشخص می‌شود.
 */
import { useEffect, useState } from "react";
import { toDate } from "../lib/clock";
import {
  ApiError,
  ForbiddenError,
  fetchMe,
  fetchMemberLedger,
  type LedgerRow,
  type MemberLedger,
} from "../lib/api";

const SOURCE = "منبع: GET /api/v1/payments/ledger/{member_id}";

// مقادیر واقعی `LedgerRow.kind` در تایپ کلاینت: charge | pay | refund | reversal
// (`lib/api.ts:229`). نگاشت «بدهکار/بستانکار» برای این قرارداد غلط بود.
const kindLabels: Record<string, string> = {
  charge: "شارژ حساب",
  pay: "پرداخت",
  refund: "بازگشت وجه",
  reversal: "معکوس‌سازی",
};

type Load =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: MemberLedger };

function rial(value: number): string {
  // عدد صحیح ریال؛ بدون float و بدون گرد کردن.
  return `${value.toLocaleString("fa-IR")} ریال`;
}

function stamp(iso: string | null): string {
  if (!iso) return "زمان ثبت نشده";
  // `toDate` از lib/clock است (قاعدهٔ no-restricted-syntax: بدون ساخت مستقیم Date).
  const date = toDate(iso);
  if (Number.isNaN(date.getTime())) return "زمان نامعتبر";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return "دسترسی به کیف پول این عضو مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "کیف پول از سرور دریافت نشد";
}

function EntryRow({ row }: { row: LedgerRow }) {
  const reversed = Boolean(row.reversed_by_entry_id);
  const isReversal = Boolean(row.reverses_entry_id);
  return (
    <li
      className="rounded-lg border border-primary/10 px-3 py-2 text-xs"
      data-entry-kind={row.kind}
      data-reversed={reversed ? "yes" : "no"}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">
          {row.amount_rial > 0 ? "+" : ""}
          {rial(row.amount_rial)}
        </span>
        <span className="text-ink-dim">
          {kindLabels[row.kind] ?? row.kind} · {stamp(row.created_at)}
        </span>
      </div>
      <p className="mt-1 text-ink-dim">
        منبع: {row.source_type}
        {row.source_id === null ? "" : ` #${row.source_id.toLocaleString("fa-IR")}`}
        {isReversal ? ` · این ردیف معکوس‌کنندهٔ #${row.reverses_entry_id?.toLocaleString("fa-IR")} است` : ""}
        {reversed ? ` · توسط #${row.reversed_by_entry_id?.toLocaleString("fa-IR")} معکوس شده` : ""}
        {row.note ? ` · ${row.note}` : ""}
      </p>
    </li>
  );
}

export function MemberWallet({ memberId: memberIdProp }: { memberId?: number } = {}) {
  const [memberId, setMemberId] = useState<number | null>(memberIdProp ?? null);
  const [load, setLoad] = useState<Load>({ kind: "loading" });

  useEffect(() => {
    if (memberIdProp !== undefined) return;
    const controller = new AbortController();
    fetchMe(undefined, controller.signal)
      .then((profile) => setMemberId(profile.id))
      .catch((error: unknown) => setLoad({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [memberIdProp]);

  useEffect(() => {
    if (memberId === null) return;
    const controller = new AbortController();
    setLoad({ kind: "loading" });
    fetchMemberLedger(memberId, undefined, controller.signal)
      .then((data) => setLoad({ kind: "ready", data }))
      .catch((error: unknown) => setLoad({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [memberId]);

  if (load.kind === "error") {
    return (
      <section aria-labelledby="member-wallet-title" className="space-y-3">
        <h3 id="member-wallet-title" className="text-base font-semibold">
          کیف پول
        </h3>
        <p role="alert" className="text-sm text-danger">
          {load.message}
        </p>
      </section>
    );
  }

  if (load.kind === "loading") {
    return (
      <section aria-labelledby="member-wallet-title" className="space-y-3">
        <h3 id="member-wallet-title" className="text-base font-semibold">
          کیف پول
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت دفتر مالی از سرور…
        </p>
      </section>
    );
  }

  const { data } = load;
  const mismatch = data.reconcile && data.reconcile.matches === false;

  return (
    <section aria-labelledby="member-wallet-title" className="space-y-4">
      <div>
        <h3 id="member-wallet-title" className="text-base font-semibold">
          کیف پول
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          همهٔ مبلغ‌ها از سرور می‌آیند (عدد صحیح ریال)؛ کلاینت چیزی جمع نمی‌زند و چیزی گرد نمی‌کند.
        </p>
      </div>

      <div className="rounded-xl border border-primary/10 px-4 py-3" data-balance-rial={data.balance_rial}>
        <p className="text-xs text-ink-dim">موجودی (از سرور)</p>
        <p className="mt-1 text-lg font-bold">{rial(data.balance_rial)}</p>
        <p className="mt-1 text-[11px] text-ink-dim">
          کیف پول: {rial(data.reconcile?.wallet_balance_rial ?? 0)} · دفتر:{" "}
          {rial(data.reconcile?.ledger_balance_rial ?? 0)}
        </p>
        <p className="text-[11px] text-ink-dim">{SOURCE}</p>
      </div>

      {mismatch ? (
        <p role="alert" className="rounded-xl border border-danger/40 bg-danger/10 px-4 py-2 text-xs">
          کیف پول و دفتر مالی نمی‌خوانند: اختلاف {rial(data.reconcile.difference_rial)}. این اختلاف تا
          تطبیق توسط مالی نمایش داده می‌شود و پنهان نمی‌شود.
        </p>
      ) : null}

      <div className="space-y-2">
        <h4 className="text-sm font-semibold">رویدادهای مالی ({data.entries.length.toLocaleString("fa-IR")})</h4>
        {data.entries.length === 0 ? (
          <p role="status" className="text-sm text-ink-dim">
            سرور هیچ رویداد مالی برنگرداند. این «پرداخت صفر» نیست؛ یعنی رویدادی ثبت نشده است.
          </p>
        ) : (
          <ul className="space-y-2">
            {data.entries.map((row) => (
              <EntryRow key={row.id} row={row} />
            ))}
          </ul>
        )}
        <p className="text-[11px] text-ink-dim">
          ترتیب: جدیدترین اول (سرور `id desc`) · حداکثر ۲۰۰ ردیف آخر؛ سرور صفحه‌بندی (offset) ندارد، پس
          «صفحهٔ بعد» ساخته نمی‌شود.
        </p>
      </div>
    </section>
  );
}
