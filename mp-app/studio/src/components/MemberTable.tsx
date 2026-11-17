import { motion } from "framer-motion";
import type { MemberSummaryRow, MembershipStatus } from "../lib/api";
import { fetchMembersSummary } from "../lib/api";
import { fa, useApi } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";

/**
 * جدول اعضا (M45-c1) — داده از `/admin/members-summary`، نه از mock.
 *
 * `unknown` یک وضعیت واقعی است: عضو هیچ اشتراکی ندارد. قبلاً mock این حالت را
 * «منقضی» نشان می‌داد که ادعای بی‌پایه بود (E05: نامعلوم ≠ صفر/منقضی).
 */
const statusPill: Record<MembershipStatus, { label: string; cls: string }> = {
  active: { label: "فعال", cls: "pill-green" },
  expiring: { label: "رو به انقضا", cls: "pill-gold" },
  expired: { label: "منقضی", cls: "pill-red" },
  unknown: { label: "نامعلوم", cls: "pill-muted" },
};

/** رنگ آواتار از شناسهٔ عضو — پایدار و بدون تصادفی‌بودن. */
const hueOf = (id: number) => (id * 47) % 360;

export function MemberTable({ onSelect }: { onSelect?: (id: number) => void }) {
  const genderFilter = useAppStore((s) => s.genderFilter);
  const search = useAppStore((s) => s.search);
  const { data, loading, error, needsSession, reload } = useApi(
    (s) => fetchMembersSummary(undefined, s),
    [],
  );

  const items = data?.items ?? [];
  const q = search.trim();
  const filtered = items.filter(
    (m) =>
      (genderFilter === "all" || m.gender === genderFilter) &&
      (!q || m.full_name.includes(q) || m.phone.includes(q)),
  );

  return (
    <div className="glass-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-primary/10 px-5 py-4">
        {/* h2 نه h3: صفحه یک h1 دارد (TopBar)، و پرش h1→h3 برای صفحه‌خوان خطاست */}
        <h2 className="text-base font-semibold">اعضا</h2>
        <span className="text-xs text-ink-dim">
          {loading ? "در حال دریافت…" : `${fa(filtered.length)} عضو`}
          {data ? ` · قاعدهٔ ${data.rule_version}` : ""}
        </span>
      </div>

      {needsSession && (
        <p className="border-b border-gold/20 px-5 py-3 text-xs text-gold">
          نشست معتبر نیست — برای ادامه با کد یک‌بارمصرف وارد شوید.
        </p>
      )}
      {error && !needsSession && (
        <div className="flex items-center justify-between border-b border-danger/20 px-5 py-3">
          <p className="text-xs text-danger">{error}</p>
          <button onClick={reload} className="text-xs text-primary-light underline">
            تلاش دوباره
          </button>
        </div>
      )}
      {!loading && !error && filtered.length === 0 && (
        <p className="px-5 py-10 text-center text-sm text-ink-dim">
          عضوی مطابق فیلتر نیست. دادهٔ نمایشی ساخته نمی‌شود.
        </p>
      )}

      <div className="divide-y divide-primary/5">
        {filtered.map((m: MemberSummaryRow, i) => (
          <motion.button
            key={m.member_id}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, duration: 0.3 }}
            whileHover={{ backgroundColor: "rgba(0,184,106,0.06)" }}
            onClick={() => onSelect?.(m.member_id)}
            className="flex w-full items-center gap-3 px-5 py-3 text-right"
          >
            <div
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
              style={{
                background: `linear-gradient(135deg, hsl(${hueOf(m.member_id)} 60% 38%), hsl(${hueOf(m.member_id)} 55% 24%))`,
              }}
            >
              {(m.full_name || "?").slice(0, 1)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{m.full_name || "بدون نام"}</p>
              <p className="truncate text-xs text-ink-dim">
                {m.phone || "—"} · {m.goal} · {m.gender === "female" ? "بانو" : "آقا"}
              </p>
            </div>
            <div className="text-left">
              <span className={statusPill[m.status].cls}>{statusPill[m.status].label}</span>
              <p className="mt-1 text-[11px] text-ink-dim">
                {m.days_left == null
                  ? "بدون اشتراک"
                  : m.days_left >= 0
                    ? `${fa(m.days_left)} روز باقی‌مانده`
                    : "اتمام اشتراک"}
              </p>
            </div>
            <div className="hidden w-28 text-xs text-ink-dim lg:block">{m.plan_name ?? "—"}</div>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
