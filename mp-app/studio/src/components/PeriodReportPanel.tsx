import { Alert, Segmented, Spin } from "antd";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchPeriodReport, type PeriodReport } from "../lib/api";
import { today } from "../lib/clock";
import { colorWithAlpha, designTokens } from "../lib/designTokens";
import { JalaliDateField } from "./ui/JalaliDateField";
import { fa } from "../lib/useApi";
import { useMotionPreset } from "../lib/motion";

const { color, typography, radius } = designTokens;

/**
 * گزارش سود/زیان دوره‌ای (QF-10) — هفته، ماه یا سال به تقویم جلالی تهران.
 *
 * قواعدی که این پنل نشان می‌دهد و تغییرشان نمی‌دهد:
 * - بازگشت وجه در دوره‌ای حساب می‌شود که برگشت خورده، نه دوره‌ای که پول آمد.
 * - اگر بازگشتی تاریخ ندارد، هشدار «ناقص» نشان داده می‌شود؛ سود «قطعی» نمی‌شود.
 * - عدد صفر فقط وقتی صفر است که سرور صفر گفته؛ خطای شبکه یا نبود داده صفر نیست.
 */

type Kind = PeriodReport["kind"];

const KIND_OPTIONS = [
  { label: "هفته", value: "week" },
  { label: "ماه", value: "month" },
  { label: "سال", value: "year" },
];

const todayIso = (): string => today();

export function PeriodReportPanel() {
  const motionPreset = useMotionPreset();
  const [kind, setKind] = useState<Kind>("month");
  const [anchor, setAnchor] = useState<string>(todayIso());
  const [report, setReport] = useState<PeriodReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError("");
    fetchPeriodReport(kind, anchor, undefined, ctrl.signal)
      .then((r) => setReport(r))
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setReport(null);
        setError(e instanceof Error ? e.message : "خطای ناشناخته");
      })
      .finally(() => setLoading(false));
    return () => ctrl.abort();
  }, [kind, anchor]);

  const chart = report
    ? [
        { name: "دریافتی", value: report.received_rial },
        { name: "بازگشت", value: report.refunds_rial },
        { name: "هزینه", value: report.expenses_rial },
        {
          name: report.complete ? "سود خالص" : "سود نامعلوم",
          value: report.complete ? report.profit_rial : null,
        },
      ]
    : [];

  return (
    <section className="space-y-3" aria-label="گزارش سود و زیان دوره‌ای">
      <div className="flex flex-wrap items-end gap-3">
        <Segmented
          options={KIND_OPTIONS}
          value={kind}
          onChange={(v) => setKind(v as Kind)}
          aria-label="نوع دوره"
        />
        <JalaliDateField label="روز داخل دوره" value={anchor} onChange={setAnchor} />
      </div>

      {error && <Alert type="error" showIcon message={error} />}
      {loading && <Spin />}

      {report && !error && (
        <>
          <p className="text-sm text-ink-dim">
            {report.label} — از {report.start_jalali}
          </p>
          {!report.complete && (
            <Alert
              type="warning"
              showIcon
              message={`${fa(report.undated_refunds_count)} بازگشت بدون تاریخ ثبت‌شده است؛ سود این دوره قطعی نیست.`}
            />
          )}
          <dl className="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
            <div>
              <dt className="text-ink-dim">دریافتی</dt>
              <dd>{fa(report.received_rial)} ریال</dd>
            </div>
            <div>
              <dt className="text-ink-dim">بازگشت ({fa(report.refunds_count)})</dt>
              <dd>{fa(report.refunds_rial)} ریال</dd>
            </div>
            <div>
              <dt className="text-ink-dim">هزینه ({fa(report.expenses_count)})</dt>
              <dd>{fa(report.expenses_rial)} ریال</dd>
            </div>
            <div>
              <dt className="text-ink-dim">سود خالص</dt>
              <dd>{report.complete ? `${fa(report.profit_rial)} ریال` : "نامعلوم"}</dd>
            </div>
          </dl>
          <div
            className="h-56"
            dir="ltr"
            role="img"
            aria-label={
              report.complete
                ? "نمودار مبالغ دوره: دریافتی، بازگشت، هزینه و سود خالص"
                : "نمودار مبالغ دوره: دریافتی، بازگشت و هزینه؛ سود نامعلوم به‌دلیل بازگشت بدون تاریخ"
            }
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                <CartesianGrid stroke={colorWithAlpha(color.primary, 0.08)} vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: color.textSecondary, fontSize: typography.caption }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: color.textSecondary, fontSize: typography.caption }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                  tickFormatter={(value) => fa(Number(value))}
                />
                <Tooltip
                  isAnimationActive={!motionPreset.reduced}
                  contentStyle={{
                    background: color.surface,
                    border: `1px solid ${color.border}`,
                    borderRadius: radius.md,
                    color: color.textPrimary,
                    direction: "rtl",
                    fontFamily: typography.fontFamily,
                  }}
                  formatter={(value) => [`${fa(Number(value))} ریال`, "مبلغ"]}
                />
                <Bar
                  dataKey="value"
                  fill={color.primary}
                  isAnimationActive={!motionPreset.reduced}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </section>
  );
}
