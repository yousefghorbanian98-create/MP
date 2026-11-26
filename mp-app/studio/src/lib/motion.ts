/**
 * M60/G4 — توکن‌های حرکت + یک نقطهٔ تصمیم برای reduced-motion.
 *
 * # چرا این فایل لازم شد
 *
 * اندازه‌گیری روی ۸ صفحه: همه انیمیشن داشتند، هیچ‌کدام `useReducedMotion` را
 * نمی‌خواندند. فقط `App.tsx` و `Feedback.tsx` رعایتش می‌کردند. یعنی کاربری که
 * در سیستم «کاهش حرکت» را روشن کرده بود، در صفحهٔ مالی/چک‌این/فروشگاه همچنان
 * انیمیشن می‌دید. برای افرادی با حساسیت دهلیزی این فقط «سلیقه» نیست؛
 * سرگیجه و سردرد است.
 *
 * قاعدهٔ منبع: reduced-motion نباید «هیچ فیدبکی» بدهد — باید حرکت را با
 * تغییر حالت (فید/رنگ) عوض کند تا اطلاعات از دست نرود.
 *
 * # قاعدهٔ استفاده
 *
 * ```tsx
 * const m = useMotionPreset();
 * <motion.div {...m.rise}>…</motion.div>
 * ```
 *
 * نه `duration` دستی در صفحه، نه `initial/animate` پراکنده.
 */

import { useSyncExternalStore } from "react";

/** زمان‌بندی‌ها — بیرون از کامپوننت‌ها، تا هر صفحه ریتم خودش را نسازد. */
export const DURATION = {
  /** بازخورد فوری فشار دکمه */
  press: 0.12,
  /** ورود کارت/ردیف */
  enter: 0.28,
  /** حرکت بزرگ (شیت، صفحه) */
  page: 0.34,
} as const;

/** منحنی مشترک: خروج نرم، بدون پرش انتهایی. */
export const EASE = [0.22, 1, 0.36, 1] as const;

/**
 * شکل یک «ورودی حرکت». عمداً باز است (نه سه تایپ دقیق و جدا):
 * در حالت reduced-motion هر سه (rise/fade/slide) به یک فید ساده تبدیل
 * می‌شوند — همان جانشینی که منابع توصیه می‌کنند — و تایپِ باریک این تبدیل را
 * غیرمجاز می‌دانست. اطلاعاتی که اهمیت دارد این است که هر سه یک شکل دارند.
 */
export interface MotionEntry {
  initial: { opacity: number; y?: number; x?: number };
  animate: { opacity: number; y?: number; x?: number };
  transition: { duration: number; ease?: readonly number[] };
}

export interface MotionPreset {
  /** آیا کاربر کاهش حرکت خواسته است؟ */
  reduced: boolean;
  /** ورود از پایین + فید — در reduced: فید */
  rise: MotionEntry;
  /** فید ساده — جانشین امن هر حرکت */
  fade: MotionEntry;
  /** ورود از کنار (فهرست‌ها) — در reduced: فید */
  slide: MotionEntry;
  /** بازخورد فشار — در حالت کاهش حرکت خالی است */
  press: { whileTap?: { scale: number } };
  /** هاور — فقط وقتی حرکت مجاز است */
  hover: { whileHover?: { y: number } };
  /** تأخیر پله‌ای مهارشده: فهرست بلند هرگز کند حس نمی‌شود */
  stagger: (i: number) => number;
}

/** سقف تأخیر پله‌ای — ۱۲ آیتم بعد از آن هم‌زمان می‌آیند. */
const STAGGER_CAP = 12;
const STAGGER_STEP = 0.045;

/**
 * منطق خالص: یک ورودی (آیا کاهش حرکت؟) → یک پریست.
 *
 * چرا جدا از هوک: نسخهٔ اول فقط هوک بود و تستش شکست، چون framer-motion مقدار
 * `matchMedia` را در زمان بارگذاری ماژول می‌خواند و بعد از آن تغییر stub اثر
 * نمی‌کند. منطقِ خالص هم تست‌پذیر است و هم می‌شود بدون مرورگر سنجیدش.
 */
export function buildPreset(reduced: boolean): MotionPreset {
  if (reduced) {
    // هیچ جابه‌جایی، هیچ مقیاسی. فید کوتاه می‌ماند تا «اتفاق افتاد» معلوم باشد.
    const fade: MotionEntry = {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: DURATION.press },
    };
    return {
      reduced: true,
      rise: fade,
      fade,
      slide: fade,
      press: {},
      hover: {},
      stagger: () => 0,
    };
  }

  return {
    reduced: false,
    rise: {
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: DURATION.enter, ease: EASE },
    },
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: DURATION.enter },
    },
    slide: {
      initial: { opacity: 0, x: 14 },
      animate: { opacity: 1, x: 0 },
      transition: { duration: DURATION.enter, ease: EASE },
    },
    press: { whileTap: { scale: 0.97 } },
    hover: { whileHover: { y: -2 } },
    stagger: (i: number) => Math.min(i, STAGGER_CAP) * STAGGER_STEP,
  };
}

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
type MatchMediaSource = (query: string) => MediaQueryList;

interface ReducedMotionMedia {
  source: MatchMediaSource;
  queryList: MediaQueryList;
}

/** اگر ثبت/پاک‌سازی listener در یک پیاده‌سازی شکست بخورد، fail-closed می‌مانیم. */
const failedSubscriptions = new WeakSet<MatchMediaSource>();
const NOOP_UNSUBSCRIBE = (): void => undefined;

function supportsChangeEvents(queryList: MediaQueryList): boolean {
  try {
    return (
      (typeof queryList.addEventListener === "function" &&
        typeof queryList.removeEventListener === "function") ||
      (typeof queryList.addListener === "function" &&
        typeof queryList.removeListener === "function")
    );
  } catch {
    return false;
  }
}

/**
 * نبودن window/matchMedia، خطای API یا نبودن API قابل پاک‌سازی، preference را
 * نامعلوم می‌کند؛ نامعلوم را محافظه‌کارانه reduced فرض می‌کنیم.
 */
function readReducedMotionMedia(): ReducedMotionMedia | null {
  try {
    if (typeof window === "undefined") return null;
    const source = window.matchMedia;
    if (typeof source !== "function" || failedSubscriptions.has(source)) return null;

    const queryList = source.call(window, REDUCED_MOTION_QUERY);
    if (!queryList || !supportsChangeEvents(queryList)) return null;
    return { source, queryList };
  } catch {
    return null;
  }
}

function getReducedMotionSnapshot(): boolean {
  const media = readReducedMotionMedia();
  if (!media) return true;
  try {
    return media.queryList.matches;
  } catch {
    return true;
  }
}

/** SSR/عدم دسترسی مرورگر تا hydration، نیز باید حالت محافظه‌کار داشته باشد. */
function getServerReducedMotionSnapshot(): boolean {
  return true;
}

function subscribeToReducedMotion(onStoreChange: () => void): () => void {
  const media = readReducedMotionMedia();
  if (!media) return NOOP_UNSUBSCRIBE;

  const { queryList, source } = media;
  const onChange = (): void => onStoreChange();

  try {
    if (
      typeof queryList.addEventListener === "function" &&
      typeof queryList.removeEventListener === "function"
    ) {
      queryList.addEventListener("change", onChange);
      return () => {
        try {
          queryList.removeEventListener("change", onChange);
        } catch {
          failedSubscriptions.add(source);
        }
      };
    }

    queryList.addListener(onChange);
    return () => {
      try {
        queryList.removeListener(onChange);
      } catch {
        failedSubscriptions.add(source);
      }
    };
  } catch {
    failedSubscriptions.add(source);
    onStoreChange();
    return NOOP_UNSUBSCRIBE;
  }
}

/**
 * هوک مصرفی: تغییر زندهٔ media query را subscribe می‌کند؛ محیط نامعلوم،
 * بدون پشتیبانی، یا دارای API ناسالم به حالت reduced برمی‌گردد.
 */
export function useMotionPreset(): MotionPreset {
  const reduced = useSyncExternalStore(
    subscribeToReducedMotion,
    getReducedMotionSnapshot,
    getServerReducedMotionSnapshot,
  );
  return buildPreset(reduced);
}
