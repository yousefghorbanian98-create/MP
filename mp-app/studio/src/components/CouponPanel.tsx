import { useEffect, useRef, useState } from "react";
import { Button, Input, Select } from "antd";
import { createCoupon, listCoupons, type CouponRow } from "../lib/api";
import { JalaliDateField } from "./ui/JalaliDateField";

/**
 * G2 — کدهای تخفیف پذیرش.
 *
 * تخفیف فقط روی سرور محاسبه می‌شود؛ این پنل فقط کد را می‌سازد و فهرست را
 * نشان می‌دهد. پایان روز انقضا به وقت تهران (+۰۳:۳۰) ثبت می‌شود.
 */

const fmt = (n: number) => n.toLocaleString("fa-IR");

function describeValue(c: CouponRow): string {
  return c.kind === "percent" ? `${fmt(c.value)}٪` : `${fmt(c.value)} ریال`;
}

export function CouponPanel() {
  const [rows, setRows] = useState<CouponRow[]>([]);
  const [code, setCode] = useState("");
  const [kind, setKind] = useState<"percent" | "fixed">("percent");
  const [value, setValue] = useState("10");
  const [maxUses, setMaxUses] = useState("");
  const [expires, setExpires] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);

  const load = async () => {
    try {
      setRows(await listCoupons());
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    }
  };

  useEffect(() => {
    void load();
    // فقط یک‌بار هنگام mount
  }, []);

  const submit = async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    setError(null);
    try {
      const n = Number(value);
      const uses = maxUses.trim() ? Number(maxUses) : null;
      await createCoupon({
        code: code.trim(),
        kind,
        value: n,
        max_uses: uses,
        expires_at: expires ? `${expires}T23:59:59+03:30` : null,
      });
      setCode("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  };

  return (
    <section className="glass-card space-y-4 p-5">
      <div>
        <h2 className="text-sm font-bold">کدهای تخفیف</h2>
        <p className="text-xs text-ink-dim">
          تخفیف روی همهٔ پرداخت‌ها و فقط در سرور محاسبه می‌شود؛ هر کد می‌تواند انقضا و سقف استفاده داشته باشد.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-2 text-xs">
        <label className="text-ink-dim">
          کد
          <Input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="mt-1 block w-36"
          />
        </label>
        <div className="text-ink-dim">
          <span>نوع</span>
          <Select
            aria-label="نوع تخفیف"
            className="mt-1 block w-40"
            options={[
              { value: "percent", label: "درصدی" },
              { value: "fixed", label: "مبلغ ثابت (ریال)" },
            ]}
            value={kind}
            onChange={(v) => setKind(v as "percent" | "fixed")}
          />
        </div>
        <label className="text-ink-dim">
          مقدار
          <Input
            aria-label="مقدار تخفیف"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            inputMode="numeric"
            className="mt-1 block w-28"
          />
        </label>
        <label className="text-ink-dim">
          سقف استفاده
          <Input
            aria-label="سقف استفاده"
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
            inputMode="numeric"
            placeholder="بی‌سقف"
            className="mt-1 block w-28"
          />
        </label>
        <div className="text-ink-dim">
          <JalaliDateField label="تاریخ انقضا" value={expires} onChange={setExpires} />
        </div>
        <Button
          type="primary"
          onClick={() => void submit()}
          disabled={busy || !code.trim() || !value.trim()}
        >
          ساخت کد
        </Button>
      </div>

      {error && (
        <p role="alert" className="text-xs text-red-400">
          {error}
        </p>
      )}

      {rows.length > 0 && (
        <table className="w-full text-xs">
          <thead className="text-ink-dim">
            <tr>
              <th className="text-start">کد</th>
              <th className="text-start">تخفیف</th>
              <th className="text-start">استفاده</th>
              <th className="text-start">انقضا</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td className="py-1 font-mono">{c.code}</td>
                <td>{describeValue(c)}</td>
                <td>
                  {fmt(c.used_count)} / {c.max_uses == null ? "∞" : fmt(c.max_uses)}
                </td>
                <td>{c.expires_at ? c.expires_at.slice(0, 10) : "بدون انقضا"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
