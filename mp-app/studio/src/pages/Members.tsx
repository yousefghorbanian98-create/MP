import { AnimatePresence, motion } from "framer-motion";
import { MemberTable } from "../components/MemberTable";
import { useAppStore } from "../stores/appStore";

const domains = [
  "قلبی-عروقی", "عضلانی-اسکلتی", "کنترل وزن", "انعطاف‌پذیری", "قدرت", "استقامت",
  "تعادل", "هماهنگی", "سرعت", "چابکی", "سلامت مفاصل", "الگوی خواب", "سطح استرس", "تغذیه",
];

/** اعضا + پنل جزئیات با ورود/خروج انیمیشنی (AnimatePresence). */
const genderTabs = [
  { key: "all" as const, label: "همه" },
  { key: "male" as const, label: "آقایان" },
  { key: "female" as const, label: "بانوان" },
];

export function Members() {
  const { selectedMemberId, selectMember, members, genderFilter, setGenderFilter } = useAppStore();
  const member = members.find((m) => m.id === selectedMemberId) ?? null;

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <div className="xl:col-span-2">
        <div className="mb-4 flex items-center gap-2">
          {genderTabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setGenderFilter(t.key)}
              className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
                genderFilter === t.key
                  ? "bg-primary text-white"
                  : "bg-surface/70 text-ink-dim hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
          <span className="mr-auto text-[11px] text-ink-dim">تفکیک جنسیت (M41) — نمای کامل ادمین</span>
        </div>
        <MemberTable onSelect={(id) => selectMember(id)} />
      </div>

      <AnimatePresence mode="wait">
        {member ? (
          <motion.div
            key={member.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ type: "spring", stiffness: 260, damping: 24 }}
            className="glass-card p-5"
          >
            <div className="flex items-center gap-3">
              <div
                className="flex h-14 w-14 items-center justify-center rounded-2xl text-lg font-bold text-white"
                style={{ background: `linear-gradient(135deg, hsl(${member.avatarHue} 60% 38%), hsl(${member.avatarHue} 55% 22%))` }}
              >
                {member.name.slice(0, 1)}
              </div>
              <div>
                <h3 className="text-lg font-bold">{member.name}</h3>
                <p className="text-xs text-ink-dim">
                  {member.phone} · هدف: {member.goal} ·{" "}
                  <span className={member.gender === "female" ? "text-pink-400" : "text-sky-400"}>
                    {member.gender === "female" ? "بانو" : "آقا"}
                  </span>
                </p>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-surface/70 p-3 text-center">
                <p className="text-2xl font-bold text-primary-light">{member.daysLeft.toLocaleString("fa-IR")}</p>
                <p className="text-xs text-ink-dim">روز باقی‌مانده</p>
              </div>
              <div className="rounded-xl bg-surface/70 p-3 text-center">
                <p className="text-2xl font-bold text-accent-soft">۸۶٪</p>
                <p className="text-xs text-ink-dim">پایبندی برنامه</p>
              </div>
            </div>

            <h4 className="mt-5 text-sm font-semibold">ارزیابی ۱۴ دامنه</h4>
            <div className="mt-3 space-y-2">
              {domains.map((d, i) => {
                const score = ((member.id * 7 + i * 3) % 5) + 1;
                return (
                  <div key={d} className="flex items-center gap-2">
                    <span className="w-28 shrink-0 text-[11px] text-ink-dim">{d}</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(score / 5) * 100}%` }}
                        transition={{ delay: i * 0.04, duration: 0.5 }}
                        className="h-full rounded-full bg-gradient-to-l from-primary to-primary-light"
                      />
                    </div>
                    <span className="w-6 text-left text-[11px] text-ink-dim">{score.toLocaleString("fa-IR")}</span>
                  </div>
                );
              })}
            </div>

            <div className="mt-5 flex gap-2">
              <button className="btn-primary flex-1">ساخت برنامه</button>
              <button className="btn-ghost flex-1">ثبت ارزیابی</button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="glass-card flex flex-col items-center justify-center p-10 text-center"
          >
            <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-2xl">👤</div>
            <p className="text-sm text-ink-dim">یک عضو را از فهرست انتخاب کنید</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
