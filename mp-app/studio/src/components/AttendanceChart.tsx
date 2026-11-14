import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { attendanceSeries } from "../data/mock";

/** نمودار حضور هفتگی — گرادیان زمردی با انیمیشن ورود. */
export function AttendanceChart() {
  return (
    <div className="glass-card p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold">حضور هفتگی</h3>
          <p className="text-xs text-ink-dim">بازدید در مقابل چک‌این تأییدشده</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-primary" /> چک‌این
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-accent" /> بازدید
          </span>
        </div>
      </div>
      <div className="h-64" dir="ltr">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={attendanceSeries} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="greenFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00B86A" stopOpacity={0.42} />
                <stop offset="100%" stopColor="#00B86A" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FFD700" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#FFD700" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(0,184,106,0.08)" vertical={false} />
            <XAxis dataKey="day" tick={{ fill: "#9CA3AF", fontSize: 11 }} axisLine={false} tickLine={false} reversed />
            <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} axisLine={false} tickLine={false} orientation="right" />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(0,184,106,0.25)",
                borderRadius: 12,
                direction: "rtl",
                fontFamily: "Vazirmatn",
              }}
            />
            <Area type="monotone" dataKey="visits" stroke="#FFD700" strokeWidth={1.6} fill="url(#goldFill)" />
            <Area type="monotone" dataKey="checkins" stroke="#00B86A" strokeWidth={2.2} fill="url(#greenFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
