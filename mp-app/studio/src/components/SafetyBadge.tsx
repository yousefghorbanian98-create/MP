/**
 * Q7 — نشان ایمنی برنامه.
 *
 * تصمیم: «غربالگری نشده» با «بی‌خطر» **یک رنگ ندارند**. اگر هر دو سبز
 * نمایش داده شوند، مربی فکر می‌کند بررسی شده و برنامهٔ خطرناک تأیید
 * می‌شود. این اولین جایی است که چنین تفکیکی در UI دیده می‌شود.
 */

export interface SafetyFlags {
  status?: string;
  headline?: string;
  blocked?: { constraint: string; label_fa: string; blocked_exercises: string[]; alternatives: string[]; advice_fa: string }[];
  high_risk_patterns?: string[];
  notes?: string[];
  safe_to_generate?: boolean;
  disclaimer_fa?: string;
  rule_version?: string;
}

const STYLE: Record<string, { cls: string; label: string }> = {
  blocked: { cls: "bg-danger/15 text-danger", label: "ناسازگار با محدودیت" },
  needs_review: { cls: "bg-amber-400/15 text-amber-200", label: "نیازمند بازبینی" },
  clear: { cls: "bg-emerald-400/15 text-emerald-300", label: "بدون ناسازگاری" },
  unknown: { cls: "bg-surface/70 text-ink-dim", label: "غربالگری نشده" },
};

export function parseSafety(raw: string | undefined): SafetyFlags | null {
  if (!raw || raw === "{}") return null;
  try {
    return JSON.parse(raw) as SafetyFlags;
  } catch {
    return null;
  }
}

export function SafetyBadge({ flags }: { flags: SafetyFlags | null }) {
  if (!flags) {
    return (
      <span className="rounded-full bg-surface/70 px-2 py-0.5 text-[10px] text-ink-dim">
        ایمنی: غربالگری ثبت نشده
      </span>
    );
  }
  const style = STYLE[flags.status ?? "unknown"] ?? STYLE.unknown;
  return (
    <span
      title={flags.disclaimer_fa ?? undefined}
      className={`rounded-full px-2 py-0.5 text-[10px] ${style.cls}`}
    >
      ایمنی: {style.label}
    </span>
  );
}
