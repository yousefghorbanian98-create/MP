import { useCallback, useEffect, useState } from "react";
import {
  fetchSegmentalReport,
  recordLimbMeasurement,
  type SegmentalReport,
} from "../lib/api";
import { fa } from "../lib/useApi";
import { useAppStore } from "../stores/appStore";

/**
 * M54-c1 — آنالیز سگمنتال آنتروپومتریک.
 *
 * صادقانه: این «ترکیب بدنی سگمنتی» نیست. فرم فقط محیط می‌گیرد و پنل
 * نسبت‌ها و تقارن را نشان می‌دهد. هر سیگنال نامعلوم «نامعلوم» می‌ماند
 * و هرگز صفر نمایش داده نمی‌شود.
 */

const FIELDS: { key: string; label: string }[] = [
  { key: "neck_cm", label: "گردن" },
  { key: "chest_cm", label: "سینه" },
  { key: "waist_cm", label: "کمر" },
  { key: "hip_cm", label: "باسن" },
  { key: "upper_arm_right_cm", label: "بازوی راست" },
  { key: "upper_arm_left_cm", label: "بازوی چپ" },
  { key: "thigh_right_cm", label: "ران راست" },
  { key: "thigh_left_cm", label: "ران چپ" },
  { key: "calf_right_cm", label: "ساق راست" },
  { key: "calf_left_cm", label: "ساق چپ" },
];

const BAND_FA: Record<string, string> = {
  normal: "طبیعی",
  elevated: "بالا",
  high: "بالا",
  low: "کم",
  adequate: "کافی",
  mild: "خفیف",
  notable: "محسوس",
  unknown: "نامعلوم",
};

const BAND_COLOR: Record<string, string> = {
  normal: "text-emerald-300",
  adequate: "text-emerald-300",
  elevated: "text-amber-300",
  high: "text-amber-300",
  low: "text-amber-300",
  mild: "text-amber-300",
  notable: "text-danger",
  unknown: "text-ink-dim",
};

const RATIO_LABEL: Record<string, string> = {
  waist_to_height: "دور کمر به قد",
  waist_to_hip: "دور کمر به باسن",
  arm_to_waist: "بازو به کمر",
};

const SIDE_LABEL: Record<string, string> = {
  upper_arm: "بازو",
  thigh: "ران",
  calf: "ساق",
};

export function SegmentalPanel() {
  const selectedMemberId = useAppStore((s) => s.selectedMemberId);
  const [report, setReport] = useState<SegmentalReport | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (selectedMemberId === null) {
      setReport(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await fetchSegmentalReport(selectedMemberId));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedMemberId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (selectedMemberId === null) {
    return (
      <p className="glass-card p-4 text-xs text-ink-dim">
        برای دیدن تحلیل سگمنتال، یک عضو را از صفحهٔ «اعضا» انتخاب کنید.
      </p>
    );
  }

  async function submit() {
    const values: Record<string, number | null> = {};
    for (const f of FIELDS) {
      const raw = form[f.key];
      if (raw === undefined || raw.trim() === "") continue;
      const n = Number(raw);
      if (!Number.isFinite(n) || n <= 0 || n > 300) {
        setError(`مقدار «${f.label}» باید عددی بین ۱ و ۳۰۰ باشد.`);
        return;
      }
      values[f.key] = n;
    }
    if (Object.keys(values).length === 0) {
      setError("حداقل یک محیط را وارد کنید.");
      return;
    }

    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      await recordLimbMeasurement(selectedMemberId as number, values);
      setForm({});
      setNotice("اندازه‌گیری ثبت شد.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  const analysis = report?.analysis ?? null;

  return (
    <div className="glass-card space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">آنالیز سگمنتال (آنتروپومتریک)</h3>
        <span className="text-[10px] text-ink-dim">{report?.rule_version ?? ""}</span>
      </div>

      <p className="rounded-lg bg-amber-400/10 px-3 py-2 text-[11px] text-amber-200">
        این تحلیل بر پایهٔ محیط اندام و نسبت‌های استاندارد WHO است — ترکیب بدنی
        سگمنتی یا InBody نیست و دادهای از امپدانس استفاده نمیکند.
      </p>

      {error && (
        <p role="alert" className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger">
          {error}
        </p>
      )}
      {notice && <p className="text-[11px] text-emerald-300">{notice}</p>}
      {loading && <p className="text-xs text-ink-dim">در حال بارگذاری…</p>}

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {FIELDS.map((f) => (
          <label key={f.key} className="text-[11px]">
            <span className="mb-1 block text-ink-dim">{f.label} (cm)</span>
            <input
              aria-label={f.label}
              inputMode="decimal"
              value={form[f.key] ?? ""}
              onChange={(e) => setForm((p) => ({ ...p, [f.key]: e.target.value }))}
              className="focus-ring w-full rounded-lg bg-surface/70 px-2 py-1.5 text-xs"
            />
          </label>
        ))}
      </div>

      <button
        onClick={() => void submit()}
        disabled={saving}
        className="btn-primary px-4 py-2 text-xs disabled:opacity-50"
      >
        {saving ? "در حال ثبت…" : "ثبت اندازهگیری"}
      </button>

      {!loading && report && report.measurements_count === 0 && (
        <p className="text-xs text-ink-dim">{report.reason}</p>
      )}

      {analysis && (
        <>
          <div className="space-y-1">
            {Object.entries(analysis.ratios).map(([key, r]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-ink-dim">{RATIO_LABEL[key] ?? key}</span>
                <span className={BAND_COLOR[r.band] ?? ""}>
                  {r.value === null ? "نامعلوم" : fa(r.value)} · {BAND_FA[r.band] ?? r.band}
                </span>
              </div>
            ))}
          </div>

          <div className="space-y-1 border-t border-white/10 pt-2">
            <p className="text-xs font-medium">{analysis.headline}</p>
            {Object.entries(analysis.asymmetry)
              .filter(([, v]) => v !== null)
              .map(([site, v]) => {
                const a = v as NonNullable<typeof v>;
                return (
                  <div key={site} className="flex items-center justify-between text-[11px]">
                    <span className="text-ink-dim">{SIDE_LABEL[site] ?? site}</span>
                    <span className={BAND_COLOR[a.band] ?? ""}>
                      راست {fa(a.right_cm)} / چپ {fa(a.left_cm)} — {a.reason}
                    </span>
                  </div>
                );
              })}
            {Object.values(analysis.asymmetry).every((v) => v === null) && (
              <p className="text-[11px] text-ink-dim">
                برای بررسی تقارن، هر دو سمت باید در همان جلسه اندازهگیری شوند.
              </p>
            )}
          </div>

          {analysis.missing.length > 0 && (
            <p className="text-[10px] text-ink-dim">
              سیگنال نامعلوم: {analysis.missing.join("، ")} — با دادهٔ ناقص
              هیچ نسبتی ساخته نمیشود.
            </p>
          )}
        </>
      )}

      {report?.trend && (
        <div className="border-t border-white/10 pt-2">
          <p className="text-[11px] text-ink-dim">
            روند در {fa(report.trend.span_days)} روز: {report.trend.headline}
          </p>
        </div>
      )}
    </div>
  );
}
