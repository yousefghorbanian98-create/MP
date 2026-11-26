import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AttendancePoint } from "../lib/api";
import { colorWithAlpha, designTokens } from "../lib/designTokens";
import { useMotionPreset } from "../lib/motion";

const { color, typography, radius } = designTokens;

/**
 * نمودار حضور (M45-c1) — داده از `/admin/attendance`، نه از mock.
 *
 * فقط یک سری واقعی داریم (چک‌این تأییدشده)؛ «بازدید» مرجع داده ندارد، پس
 * خط طلایی نمایش داده نمی‌شود تا عدد ساختگی وارد نمودار نشود.
 */
export function AttendanceChart({ series }: { series: AttendancePoint[] }) {
  const motionPreset = useMotionPreset();
  const data = series.map((p) => ({
    day: p.date.slice(5).replace("-", "/"),
    checkins: p.count,
  }));

  return (
    <div className="h-64" dir="ltr">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="greenFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color.primary} stopOpacity={0.42} />
              <stop offset="100%" stopColor={color.primary} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={colorWithAlpha(color.primary, 0.08)} vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fill: color.textSecondary, fontSize: typography.caption }}
            axisLine={false}
            tickLine={false}
            reversed
          />
          <YAxis
            tick={{ fill: color.textSecondary, fontSize: typography.caption }}
            axisLine={false}
            tickLine={false}
            orientation="right"
            allowDecimals={false}
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
          />
          <Area
            isAnimationActive={!motionPreset.reduced}
            type="monotone"
            dataKey="checkins"
            name="چک‌این تأییدشده"
            stroke={color.primary}
            strokeWidth={2.2}
            fill="url(#greenFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
