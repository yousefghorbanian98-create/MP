/**
 * دستگاه‌های فعال — فاز ۴ (QF-01).
 *
 * سرور منبع حقیقت است: فهرست از `GET /auth/sessions` می‌آید و ابطال با
 * `DELETE /auth/sessions/{id}` انجام و سپس **بازخوانی** می‌شود. هیچ ردیف
 * نمونه/حدسی ساخته نمی‌شود و وضعیت «ابطال شد» پیش از پاسخ سرور نمایش
 * داده نمی‌شود. نشست جاری با برچسب «این دستگاه» مشخص است و دکمهٔ ابطال
 * ندارد؛ ابطال خود با «خروج» انجام می‌شود تا کاربر ناخواسته بیرون نیفتد.
 * شناسهٔ نمایش‌داده‌شده `RefreshToken.id` است، نه هش توکن (که سرور افشا نمی‌کند).
 */
import { Button, Empty, Popconfirm, Spin, Tag } from "antd";
import { useCallback, useEffect, useState } from "react";
import { AuthError, fetchSessions, revokeSession, type DeviceSession } from "../lib/api";
import { toDate } from "../lib/clock";

function formatUtc(iso: string): string {
  const d = toDate(iso);
  if (Number.isNaN(d.getTime())) return "نامشخص";
  return d.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

export function DeviceSessions() {
  const [sessions, setSessions] = useState<DeviceSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsSession, setNeedsSession] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchSessions()
      .then((rows) => {
        // قرارداد سرور: آرایه. بدنهٔ ناشناخته ردیف جعلی نمی‌سازد و کرش هم نمی‌کند.
        if (!Array.isArray(rows)) throw new Error("پاسخ سرور برای فهرست دستگاه‌ها معتبر نیست");
        setSessions(rows);
        setNeedsSession(false);
      })
      .catch((err: unknown) => {
        if (err instanceof AuthError) setNeedsSession(true);
        else setError(err instanceof Error ? err.message : "خطا در خواندن دستگاه‌ها");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function revoke(row: DeviceSession) {
    setBusyId(row.id);
    setError(null);
    try {
      await revokeSession(row.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "ابطال نشست ناموفق بود");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="glass-card p-5" aria-label="دستگاه‌های فعال">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">دستگاه‌های فعال</h3>
        <Button size="small" onClick={() => void load()} disabled={loading}>
          بازخوانی
        </Button>
      </header>
      <p className="mt-1 text-xs text-ink-dim">
        فقط نشست‌های معتبر همین حساب نمایش داده می‌شوند؛ ابطال هر دستگاه بلافاصله اعمال می‌شود.
      </p>

      {needsSession && (
        <p className="mt-3 rounded-xl border border-amber-500/30 p-3 text-xs text-amber-300">
          نشست معتبر نیست؛ با کد یک‌بارمصرف دوباره وارد شوید.
        </p>
      )}

      {error && (
        <p role="alert" className="mt-3 rounded-xl border border-rose-500/30 p-3 text-xs text-rose-300">
          {error}
        </p>
      )}

      {loading ? (
        <div className="mt-4 flex justify-center">
          <Spin size="small" />
        </div>
      ) : sessions.length === 0 ? (
        <Empty className="mt-4" description="نشست فعالی برای این حساب ثبت نشده" />
      ) : (
        <ul className="mt-4 divide-y divide-primary/10">
          {sessions.map((row) => (
            <li key={row.id} className="flex items-center justify-between gap-3 py-3">
              <div>
                <p className="text-sm font-semibold">
                  {row.device_info || "دستگاه ناشناس"}
                  {row.current && (
                    <Tag color="green" className="mr-2">
                      این دستگاه
                    </Tag>
                  )}
                </p>
                <p className="mt-1 font-mono text-[11px] text-ink-dim">
                  نشست #{row.id} · ساخته‌شده {formatUtc(row.created_at)} · انقضا{" "}
                  {formatUtc(row.expires_at)}
                </p>
              </div>
              {!row.current && (
                <Popconfirm
                  title="این دستگاه خارج شود؟"
                  okText="خارج کن"
                  cancelText="انصراف"
                  onConfirm={() => void revoke(row)}
                >
                  <Button danger size="small" loading={busyId === row.id}>
                    خروج دستگاه
                  </Button>
                </Popconfirm>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
