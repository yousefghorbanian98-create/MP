/**
 * بنر به‌روزرسانی بدون نصب مجدد (M20) — نوار پایین با انیمیشن ورود.
 */
import { AnimatePresence, motion } from "framer-motion";
import { useUpdateCheck } from "../lib/update";

export function UpdateBanner({ current }: { current: string }) {
  const { manifest, apply } = useUpdateCheck(current, "web");
  return (
    <AnimatePresence>
      {manifest && (
        <motion.div
          initial={{ y: 64, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 64, opacity: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 24 }}
          className="fixed bottom-4 inset-x-4 z-50 mx-auto max-w-md rounded-2xl border border-emerald-500/30 bg-gray-900/90 p-4 shadow-2xl backdrop-blur"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400">
              ↻
            </div>
            <div className="flex-1 text-right">
              <p className="text-sm font-bold text-gray-100">نسخهٔ جدید {manifest.latest} آماده است</p>
              <p className="mt-0.5 text-xs text-gray-400">به‌روزرسانی بدون نصب مجدد — {manifest.notes}</p>
            </div>
            <button
              onClick={apply}
              className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-bold text-white transition hover:bg-emerald-400 active:scale-95"
            >
              به‌روزرسانی
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
