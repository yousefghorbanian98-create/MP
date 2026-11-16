/**
 * لایهٔ بازخورد UI — «هیچ عملیاتی نباید بی‌پاسخ بماند» (M59).
 *
 * چرا این فایل وجود دارد: بازبینی ۲۰۲۶-۱۱-۱۵ نشان داد در کل `src/`
 * هیچ toast/skeleton/modal نبود؛ یعنی دکمه‌ای که کار می‌کرد و دکمه‌ای که
 * شکست می‌خورد **یک‌شکل** دیده می‌شدند. هر سه جزء اینجا مینیمال و بدون
 * وابستگی جدید هستند (framer-motion از قبل هست).
 *
 * قواعد دسترس‌پذیری:
 * - toast در `role="status"` + `aria-live="polite"` (خطا: assertive)
 * - modal با `role="dialog"` + `aria-modal`، Escape می‌بندد، فوکوس برمی‌گردد
 * - skeleton با `aria-busy` و احترام به `prefers-reduced-motion`
 */
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef } from "react";
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

const KIND_ICON: Record<ToastKind, string> = { success: "✓", error: "!", info: "i" };

export function ToastViewport() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);
  const reduced = useReducedMotion();

  return (
    <div className="pointer-events-none fixed bottom-5 left-1/2 z-[70] flex w-[min(92vw,26rem)] -translate-x-1/2 flex-col gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            layout
            role={t.kind === "error" ? "alert" : "status"}
            aria-live={t.kind === "error" ? "assertive" : "polite"}
            initial={reduced ? false : { opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? undefined : { opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: reduced ? 0 : 0.22, ease: "easeOut" }}
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
      className={`animate-pulse rounded-lg bg-white/10 ${className}`}
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
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    confirmRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
      if (e.key === "Tab") {
        // trap ساده: فوکوس از دیالوگ بیرون نزند
        const nodes = ref.current?.querySelectorAll<HTMLElement>(
          "button, [href], input, textarea, select",
        );
        if (!nodes || nodes.length === 0) return;
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
          initial={reduced ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={reduced ? undefined : { opacity: 0 }}
          onClick={onCancel}
        >
          <motion.div
            ref={ref}
            role="dialog"
            aria-modal="true"
            aria-label={title}
            initial={reduced ? false : { opacity: 0, scale: 0.96, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduced ? undefined : { opacity: 0, scale: 0.97 }}
            transition={{ duration: reduced ? 0 : 0.2, ease: "easeOut" }}
            onClick={(e) => e.stopPropagation()}
            className="glass-card w-[min(94vw,28rem)] space-y-4 p-5"
          >
            <h3 className="text-base font-bold">{title}</h3>
            {body && <p className="text-sm leading-6 text-ink-dim">{body}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onCancel}
                className="focus-ring rounded-xl px-4 py-2 text-sm text-ink-dim transition-colors hover:text-ink"
              >
                انصراف
              </button>
              <button
                ref={confirmRef}
                type="button"
                onClick={onConfirm}
                className={`focus-ring rounded-xl px-4 py-2 text-sm font-medium text-white transition-transform active:scale-[0.98] ${
                  danger ? "bg-danger hover:bg-danger/90" : "bg-primary hover:bg-primary/90"
                }`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
