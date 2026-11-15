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

/**
 * نمودار حضور (M45-c1) — داده از `/admin/attendance`، نه از mock.
 *
 * فقط یک سری واقعی داریم (چک‌این تأییدشده)؛ «بازدید» مرجع داده ندارد، پس
 * خط طلایی نمایش داده نمی‌شود تا عدد ساختگی وارد نمودار نشود.
 */
export function AttendanceChart({ series }: { series: AttendancePoint[] }) {
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
              <stop offset="0%" stopColor="#00B86A" stopOpacity={0.42} />
              <stop offset="100%" stopColor="#00B86A" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(0,184,106,0.08)" vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            reversed
          />
          <YAxis
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            orientation="right"
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid rgba(0,184,106,0.25)",
              borderRadius: 12,
              direction: "rtl",
              fontFamily: "Vazirmatn",
            }}
          />
          <Area
            type="monotone"
            dataKey="checkins"
            name="چک‌این تأییدشده"
            stroke="#00B86A"
            strokeWidth={2.2}
            fill="url(#greenFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
