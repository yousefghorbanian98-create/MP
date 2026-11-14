import { motion } from "framer-motion";
import { AttendanceChart } from "../components/AttendanceChart";
import { KpiCard } from "../components/KpiCard";
import { MemberTable } from "../components/MemberTable";
import { ScheduleTimeline } from "../components/ScheduleTimeline";
import { kpis } from "../data/mock";
import { useAppStore } from "../stores/appStore";

/** داشبورد — KPI + نمودار + اعضا + برنامهٔ امروز. */
export function Dashboard() {
  const { setPage, selectMember } = useAppStore();

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-6"
    >
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi, i) => (
          <KpiCard key={kpi.id} kpi={kpi} index={i} />
        ))}
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <AttendanceChart />
        </div>
        <ScheduleTimeline />
      </section>

      <section>
        <MemberTable
          onSelect={(id) => {
            selectMember(id);
            setPage("members");
          }}
        />
      </section>
    </motion.div>
  );
}
