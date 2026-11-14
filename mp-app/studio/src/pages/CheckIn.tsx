import { motion } from "framer-motion";
import { useState } from "react";

const feed = [
  { id: 1, name: "امیر حسینی", method: "face", time: "۱۷:۴۲", ok: true },
  { id: 2, name: "علی رضایی", method: "qr", time: "۱۷:۳۸", ok: true },
  { id: 3, name: "مریم احمدی", method: "face", time: "۱۷:۳۱", ok: false },
  { id: 4, name: "رضا کریمی", method: "face", time: "۱۷:۲۰", ok: true },
];

/** نمای زندهٔ چک‌این — الهام‌گرفته از موکاپ گیت چهره. */
export function CheckIn() {
  const [scanning, setScanning] = useState(true);

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-5">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card relative overflow-hidden xl:col-span-3"
      >
        <div className="relative flex h-[420px] items-center justify-center bg-[radial-gradient(600px_300px_at_50%_20%,rgba(0,184,106,0.12),transparent)]">
          {/* قاب تشخیص چهره */}
          <div className="relative h-64 w-52">
            <div className="absolute inset-0 rounded-[28px] border-2 border-primary/50" />
            {(["right-0 top-0 rounded-tr-[28px] border-t-2 border-r-2", "left-0 top-0 rounded-tl-[28px] border-t-2 border-l-2", "right-0 bottom-0 rounded-br-[28px] border-b-2 border-r-2", "left-0 bottom-0 rounded-bl-[28px] border-b-2 border-l-2"] as const).map((cls) => (
              <span key={cls} className={`absolute h-10 w-10 border-primary ${cls}`} />
            ))}
            {scanning && (
              <motion.span
                className="absolute inset-x-4 top-4 h-px bg-gradient-to-l from-transparent via-primary to-transparent shadow-[0_0_18px_rgba(0,184,106,0.8)]"
                animate={{ y: [0, 220, 0] }}
                transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
              />
            )}
            <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-30">◎</div>
          </div>

          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 text-center">
            <p className="text-sm text-ink-dim">{scanning ? "در حال اسکن... جلوی دوربین بایستید" : "اسکن متوقف شد"}</p>
            <button onClick={() => setScanning((s) => !s)} className="btn-ghost mt-3 px-3 py-1.5 text-xs">
              {scanning ? "توقف اسکن" : "شروع اسکن"}
            </button>
          </div>
        </div>
      </motion.div>

      <div className="space-y-4 xl:col-span-2">
        <div className="glass-card p-5">
          <h3 className="mb-3 text-base font-semibold">ورودهای اخیر</h3>
          <div className="space-y-3">
            {feed.map((f, i) => (
              <motion.div
                key={f.id}
                initial={{ opacity: 0, x: 14 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="flex items-center justify-between rounded-xl bg-surface/60 px-3 py-2.5"
              >
                <div className="flex items-center gap-2.5">
                  <span className={`h-2 w-2 rounded-full ${f.ok ? "bg-primary" : "bg-danger"}`} />
                  <div>
                    <p className="text-sm font-medium">{f.name}</p>
                    <p className="text-[11px] text-ink-dim">{f.method === "face" ? "تشخیص چهره" : "QR"}</p>
                  </div>
                </div>
                <div className="text-left">
                  <p className="text-xs text-ink-dim">{f.time}</p>
                  {!f.ok && <p className="text-[11px] text-danger">اشتراک منقضی</p>}
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="glass-card border-accent/25 p-5">
          <h3 className="text-sm font-semibold">SLO گیت ورود</h3>
          <div className="mt-2 flex items-end justify-between">
            <p className="text-3xl font-bold text-primary-light">۱.۴<span className="text-base text-ink-dim"> ثانیه</span></p>
            <span className="pill-green">۹۹٪ زیر ۲ ثانیه</span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "93%" }}
              transition={{ duration: 1 }}
              className="h-full rounded-full bg-gradient-to-l from-primary to-accent"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
