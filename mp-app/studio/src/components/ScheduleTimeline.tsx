import { motion } from "framer-motion";
import { schedule } from "../data/mock";

const kindColor: Record<string, string> = {
  assessment: "#00B86A",
  workout: "#FFD700",
  renewal: "#38BDF8",
};

/** تایم‌لاین برنامهٔ امروز. */
export function ScheduleTimeline() {
  return (
    <div className="glass-card p-5">
      <h3 className="mb-4 text-base font-semibold">برنامهٔ امروز</h3>
      <ol className="relative space-y-4 border-r border-primary/15 pr-4">
        {schedule.map((s, i) => (
          <motion.li
            key={s.id}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + i * 0.07 }}
            className="relative"
          >
            <span
              className="absolute -right-[21px] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-bg"
              style={{ background: kindColor[s.kind] }}
            />
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold">{s.title}</p>
                <p className="text-xs text-ink-dim">{s.member}</p>
              </div>
              <span className="rounded-lg bg-surface/80 px-2 py-1 text-xs text-ink-dim">{s.time}</span>
            </div>
          </motion.li>
        ))}
      </ol>
    </div>
  );
}
