/**
 * امنیت حساب عضو (MEM-03 / PWA-32) — نشست‌های دستگاه و «خروج از همهٔ دستگاه‌ها».
 *
 * چرا این کارت لازم بود: `GET /auth/sessions`، `DELETE /auth/sessions/{id}` و
 * `POST /auth/logout-all` سه قرارداد واقعیِ backend بودند، اما فقط در shell
 * کارکنان مصرف می‌شدند. عضو هیچ راهی برای دیدن/بستن نشست‌هایش نداشت و
 * `logout-all` در گیت api-coverage با TODO «پنل امنیتی» ثبت شده بود.
 *
 * قواعد:
 * - هیچ ردیف نمونه ساخته نمی‌شود؛ فهرست فقط از پاسخ سرور می‌آید (`DeviceSessions`).
 * - خروج از همهٔ دستگاه‌ها فقط وقتی «انجام شد» اعلام می‌شود که سرور ۲۰۰ بدهد.
 *   در خطای شبکه/سرور، نشست محلی پاک نمی‌شود تا کاربر بتواند دوباره تلاش کند؛
 *   ادعای خروج بدون تأیید سرور، دروغِ وضعیت است.
 */
import { Popconfirm } from "antd";
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { DeviceSessions } from "./DeviceSessions";

export function MemberSecurity() {
  const { signOutEverywhere } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function endEverywhere(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      const confirmed = await signOutEverywhere();
      if (!confirmed) {
        setError(
          "سرور خروج از همهٔ دستگاه‌ها را تأیید نکرد؛ نشست‌های شما هنوز معتبرند. اتصال را بررسی و دوباره تلاش کنید.",
        );
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "خروج از همهٔ دستگاه‌ها ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4" aria-labelledby="member-security-title">
      <div>
        <h4 id="member-security-title" className="text-base font-semibold">
          امنیت و دستگاه‌ها
        </h4>
        <p className="mt-1 text-xs text-ink-dim">
          دستگاه‌های واردشده به حساب خود را ببینید و هر نشست ناشناس را ببندید.
        </p>
      </div>

      <DeviceSessions />

      <div className="rounded-xl border border-primary/10 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">خروج از همهٔ دستگاه‌ها</p>
            <p className="mt-1 text-xs text-ink-dim">
              همهٔ نشست‌ها از جمله همین مرورگر بسته می‌شود و باید دوباره با کد یک‌بارمصرف وارد شوید.
            </p>
          </div>
          <Popconfirm
            title="از همهٔ دستگاه‌ها خارج شوید؟"
            description="همهٔ نشست‌های این حساب بسته می‌شود."
            okText="خارج شو"
            cancelText="انصراف"
            onConfirm={() => void endEverywhere()}
          >
            <button
              type="button"
              disabled={busy}
              className="focus-ring rounded-xl border border-danger/30 px-3 py-2 text-sm text-danger hover:bg-danger/10 disabled:opacity-50"
            >
              {busy ? "در حال خروج…" : "خروج از همهٔ دستگاه‌ها"}
            </button>
          </Popconfirm>
        </div>
        {error && (
          <p role="alert" className="mt-3 rounded-xl border border-danger/20 px-3 py-2 text-xs text-danger">
            {error}
          </p>
        )}
      </div>
    </section>
  );
}
