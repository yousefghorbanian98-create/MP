import { useState } from "react";
import { fetchMemberVolume, type VolumeLevel, type VolumeMuscleRow } from "../lib/api";
import { useApi } from "../lib/useApi";

/**
 * G2 — پنل حجم هفتگی هر گروه عضلانی (MV/MEV/MAV/MRV).
 *
 * هر عدد روی صفحه یک منبع دارد و همان منبع هم نوشته می‌شود:
 *   «برنامه» یعنی هیچ ستی گزارش نشده و عدد از خود برنامه است؛
 *   «گزارش‌شده» یعنی از بازخورد واقعی عضو و فقط ست‌های سخت شمرده شده‌اند.
 * این تفاوت پنهان نمی‌شود، چون ۱۲ ست برنامه‌ریزی‌شده با ۱۲ ست انجام‌شده یکی نیست.
 */

const statusMap: Record<string, { label: string; cls: string; bar: string }> = {
  below_mv: { label: "زیر MV", cls: "pill-red", bar: "bg-rose-400" },
  between_mv_mev: { label: "MV→MEV", cls: "pill-gold", bar: "bg-amber-400" },
  mev: { label: "روی MEV", cls: "pill-green", bar: "bg-emerald-400" },
  mav: { label: "در MAV", cls: "pill-green", bar: "bg-emerald-400" },
  above_mav: { label: "بالای MAV", cls: "pill-gold", bar: "bg-amber-400" },
  mrv_exceeded: { label: "عبور از MRV", cls: "pill-red", bar: "bg-rose-500" },
};

const levels: { key: VolumeLevel; label: string }[] = [
  { key: "beginner", label: "مبتدی" },
  { key: "intermediate", label: "متوسط" },
  { key: "advanced", label: "پیشرفته" },
];

function Bar({ row }: { row: VolumeMuscleRow }) {
  const lm = row.landmarks;
  const max = Math.max(lm.mrv, row.effective_sets, 1);
  const pct = (v: number) => `${Math.min(100, (v / max) * 100)}%`;
  const meta = statusMap[row.status] ?? { label: row.status, cls: "pill-gold", bar: "bg-amber-400" };

  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium">{row.muscle}</span>
        <span className={meta.cls}>{meta.label}</span>
      </div>
      <div className="relative h-2.5 overflow-hidden rounded-full bg-surface/70">
        {/* ناحیهٔ MAV به‌صورت پس‌زمینه، تا عدد در بستر خودش دیده شود */}
        <div
          className="absolute inset-y-0 bg-white/10"
          style={{ left: pct(lm.mav_min), width: `calc(${pct(lm.mav_max)} - ${pct(lm.mav_min)})` }}
        />
        <div className={`absolute inset-y-0 left-0 ${meta.bar}`} style={{ width: pct(row.effective_sets) }} />
      </div>
      <div className="flex flex-wrap items-center justify-between gap-x-3 text-[11px] text-ink-dim">
        <span>
          ست مؤثر <b className="text-ink">{row.effective_sets}</b> از {row.planned_sets} برنامه‌ریزی‌شده ·{" "}
          {row.source_of_number === "planned" ? "منبع: برنامه" : "منبع: گزارش عضو"}
        </span>
        <span dir="ltr" className="font-mono">
          MV {lm.mv} · MEV {lm.mev} · MAV {lm.mav_min}–{lm.mav_max} · MRV {lm.mrv}
        </span>
      </div>
      {row.data_state === "reported" && (
        <p className="text-[11px] text-ink-dim">
          ست سخت {row.hard_sets} · ست راحت {row.soft_sets}
          {row.unknown_rir_sets > 0 && ` · RIR نامعلوم ${row.unknown_rir_sets}`} (ست سخت = RIR ≤{" "}
          {row.landmarks.hard_set_max_rir})
        </p>
      )}
      <p className="text-[11px] text-ink-dim">
        پیشنهاد هفتهٔ بعد:{" "}
        <b className={row.suggestion.delta_sets > 0 ? "text-emerald-300" : row.suggestion.delta_sets < 0 ? "text-rose-300" : "text-ink"}>
          {row.suggestion.delta_sets > 0 ? `+${row.suggestion.delta_sets}` : row.suggestion.delta_sets} ست
        </b>{" "}
        — {row.suggestion.reason}
      </p>
    </div>
  );
}

export function VolumePanel({ memberId }: { memberId: number }) {
  const [level, setLevel] = useState<VolumeLevel>("intermediate");
  const { data, loading, error, needsSession } = useApi(
    (s) => fetchMemberVolume(memberId, level, undefined, s),
    [memberId, level],
  );

  return (
    <section className="glass-card space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold">حجم هفتگی و نشانگرهای علمی</h3>
          <p className="text-xs text-ink-dim">
            ست سخت هر گروه عضلانی در برابر MV/MEV/MAV/MRV — قاعدهٔ مربی‌گری، نه معادلهٔ پزشکی
          </p>
        </div>
        <div className="flex gap-1">
          {levels.map((l) => (
            <button
              key={l.key}
              onClick={() => setLevel(l.key)}
              className={`px-2.5 py-1 text-xs ${level === l.key ? "btn-primary" : "btn-ghost"}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      {needsSession && <p className="text-sm text-ink-dim">برای دیدن گزارش حجم، وارد شوید.</p>}
      {loading && <p className="text-sm text-ink-dim">در حال محاسبه…</p>}
      {error && (
        <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && data && (
        <>
          {data.muscles.length === 0 ? (
            <p className="rounded-lg bg-surface/50 p-6 text-center text-sm text-ink-dim">
              {data.reason}
            </p>
          ) : (
            <>
              <p className="text-[11px] text-ink-dim">{data.reason}</p>
              <div className="space-y-5">
                {data.muscles.map((m) => (
                  <Bar key={m.muscle} row={m} />
                ))}
              </div>
              <p className="border-t border-white/10 pt-3 text-[11px] text-ink-dim">
                منبع جدول: {data.muscles[0].landmarks.source}
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}
