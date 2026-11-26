/**
 * لایهٔ بازخورد UI — «هیچ عملیاتی نباید بی‌پاسخ بماند» (M59).
 *
 * چرا این فایل وجود دارد: بازبینی ۲۰۲۶-۱۱-۱۵ نشان داد در کل `src/`
 * هیچ toast/skeleton/modal نبود؛ یعنی دکمه‌ای که کار می‌کرد و دکمه‌ای که
 * شکست می‌خورد **یک‌شکل** دیده می‌شدند.
 *
 * Q11 (۲۰۲۶-۱۱-۱۹): دیالوگ تأیید دیگر دست‌ساز نیست؛ `ConfirmDialog` پوستهٔ
 * نازک روی `Modal` کتابخانهٔ antd است (فوکوس‌تراپ، Escape، aria-modal و
 * بازگشت فوکوس در خود کتابخانه آزموده شده‌اند). toast و skeleton به‌عنوان
 * لایهٔ بازخورد باقی می‌مانند چون کامپوننت «کنترل ورودی» نیستند؛ انتقال آن‌ها
 * به `message`/`Alert` antd کار جدا و با تست جداگانه است.
 *
 * قواعد دسترس‌پذیری باقی‌مانده:
 * - toast در `role="status"` + `aria-live="polite"` (خطا: assertive)
 * - skeleton با `aria-busy` و احترام به `prefers-reduced-motion`
 */
import {
  CheckCircleFilled,
  ExclamationCircleFilled,
  InfoCircleFilled,
} from "@ant-design/icons";
import { Modal } from "antd";
import { AnimatePresence, motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";

export interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastState {
  toasts: Toast[];
  push: (kind: ToastKind, message: string) => void;
  dismiss: (id: number) => void;
}

let toastSeq = 0;

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  push: (kind, message) => {
    const id = ++toastSeq;
    set({ toasts: [...get().toasts, { id, kind, message }] });
    // خطا بیشتر می‌ماند: کاربر باید فرصت خواندن داشته باشد.
    const ttl = kind === "error" ? 6500 : 3800;
    if (typeof setTimeout === "function") setTimeout(() => get().dismiss(id), ttl);
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}));

/** فراخوانی از هر جای کد (حتی بیرون از کامپوننت). */
export const toast = {
  success: (m: string) => useToastStore.getState().push("success", m),
  error: (m: string) => useToastStore.getState().push("error", m),
  info: (m: string) => useToastStore.getState().push("info", m),
};

const KIND_STYLE: Record<ToastKind, string> = {
  success: "border-success/40 bg-success/15 text-ink",
  error: "border-danger/50 bg-danger/15 text-ink",
  info: "border-primary/40 bg-primary/15 text-ink",
};

const KIND_ICON: Record<ToastKind, React.ReactNode> = {
  success: <CheckCircleFilled aria-hidden="true" />,
  error: <ExclamationCircleFilled aria-hidden="true" />,
  info: <InfoCircleFilled aria-hidden="true" />,
};

export function ToastViewport() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);
  const motionPreset = useMotionPreset();

  return (
    <div className="pointer-events-none fixed bottom-5 left-1/2 z-[70] flex w-[min(92vw,26rem)] -translate-x-1/2 flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout={!motionPreset.reduced}
            role={t.kind === "error" ? "alert" : "status"}
            aria-live={t.kind === "error" ? "assertive" : "polite"}
            {...(motionPreset.reduced ? motionPreset.fade : motionPreset.rise)}
            exit={
              motionPreset.reduced
                ? { opacity: 0, transition: motionPreset.fade.transition }
                : { opacity: 0, y: 8, scale: 0.98 }
            }
            transition={
              motionPreset.reduced ? motionPreset.fade.transition : { duration: 0.22, ease: "easeOut" }
            }
            className={`pointer-events-auto flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm shadow-glow backdrop-blur ${KIND_STYLE[t.kind]}`}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs">
              {KIND_ICON[t.kind]}
            </span>
            <span className="flex-1 leading-6">{t.message}</span>
            <button
              type="button"
              onClick={() => dismiss(t.id)}
              aria-label="بستن پیام"
              className="focus-ring rounded-lg px-2 text-ink-dim transition-colors hover:text-ink"
            >
              ×
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

/** اسکلتون بارگذاری — جای محتوا، نه اسپینر وسط صفحهٔ خالی. */
export function Skeleton({ className = "h-4 w-full" }: { className?: string }) {
  return (
    <div
      aria-busy="true"
      aria-hidden="true"
      className={`animate-pulse motion-reduce:animate-none rounded-lg bg-white/10 ${className}`}
    />
  );
}

export function SkeletonCards({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-card space-y-3 p-4" aria-busy="true">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ))}
    </div>
  );
}

/** دیالوگ تأیید برای عملیات برگشت‌ناپذیر (حذف، تأیید قیمت، تسویه). */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "تأیید",
  danger = false,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  body?: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      centered
      cancelText="انصراف"
      okButtonProps={{ danger }}
      okText={confirmLabel}
      open={open}
      title={title}
      onCancel={onCancel}
      onOk={onConfirm}
    >
      {body && <p className="text-sm leading-6 text-ink-dim">{body}</p>}
    </Modal>
  );
}
