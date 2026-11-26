/**
 * M60/G4 — تست قرارداد helper و مسیرهای reduced-motion.
 *
 * این تست‌ها تصمیم‌های source و یک fixture JSDOM را می‌سنجند؛ computed style،
 * paint واقعی، مرورگر/OS یا پذیرش دسترس‌پذیری را ثابت نمی‌کنند.
 *
 *  ۱) حالت reduced جابه‌جایی/scale و stagger را حذف و fade کوتاه را حفظ می‌کند.
 *  ۲) حالت normal دارای حرکت کنترل‌شده است.
 *  ۳) مصرف‌کنندگان motion از helper مشترک استفاده می‌کنند و CSS media guard وجود دارد.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { useState } from "react";
import { renderToString } from "react-dom/server";
import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { buildPreset, useMotionPreset, DURATION } = await import("../src/lib/motion");

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
type ChangeListener = () => void;
type ListenerMode = "modern" | "legacy";

let originalMatchMedia: PropertyDescriptor | undefined;

beforeEach(() => {
  originalMatchMedia = Object.getOwnPropertyDescriptor(window, "matchMedia");
});

afterEach(() => {
  if (originalMatchMedia) {
    Object.defineProperty(window, "matchMedia", originalMatchMedia);
  } else {
    Reflect.deleteProperty(window, "matchMedia");
  }
});

function setMatchMedia(value: unknown): void {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value,
  });
}

function installMatchMedia(matches: boolean, mode: ListenerMode = "modern") {
  let currentMatches = matches;
  const listeners = new Set<ChangeListener>();
  const addEventListener =
    mode === "modern"
      ? vi.fn((_type: string, listener: ChangeListener) => listeners.add(listener))
      : undefined;
  const removeEventListener =
    mode === "modern"
      ? vi.fn((_type: string, listener: ChangeListener) => listeners.delete(listener))
      : undefined;
  const addListener =
    mode === "legacy" ? vi.fn((listener: ChangeListener) => listeners.add(listener)) : undefined;
  const removeListener =
    mode === "legacy" ? vi.fn((listener: ChangeListener) => listeners.delete(listener)) : undefined;
  const queryList = {
    get matches() {
      return currentMatches;
    },
    media: REDUCED_MOTION_QUERY,
    onchange: null,
    addEventListener,
    removeEventListener,
    addListener,
    removeListener,
  } as unknown as MediaQueryList;
  const matchMedia = vi.fn((_query: string) => queryList);

  setMatchMedia(matchMedia);
  return {
    queryList,
    matchMedia,
    listeners,
    addEventListener,
    removeEventListener,
    addListener,
    removeListener,
    setMatches(next: boolean) {
      currentMatches = next;
      for (const listener of [...listeners]) listener();
    },
  };
}

function MotionAwareDraft() {
  const preset = useMotionPreset();
  const [draft, setDraft] = useState("");
  return (
    <>
      <input aria-label="draft" value={draft} onChange={(event) => setDraft(event.target.value)} />
      <output>{preset.reduced ? "reduced" : "normal"}</output>
    </>
  );
}

describe("buildPreset — منطق خالص حرکت", () => {
  it("با prefers-reduced-motion، هیچ y/x/scale ای باقی نمی‌ماند", () => {
    const m = buildPreset(true);

    expect(m.reduced).toBe(true);
    for (const key of ["rise", "fade", "slide"] as const) {
      expect(m[key].initial, key).not.toHaveProperty("y");
      expect(m[key].initial, key).not.toHaveProperty("x");
      expect(m[key].animate, key).not.toHaveProperty("y");
      expect(m[key].animate, key).not.toHaveProperty("x");
    }
    // فید می‌ماند: اطلاعات «اتفاق افتاد» نباید از دست برود
    expect(m.fade.initial.opacity).toBe(0);
    expect(m.fade.animate.opacity).toBe(1);
    // بازخورد فشار و هاور حذف می‌شوند
    expect(m.press.whileTap).toBeUndefined();
    expect(m.hover.whileHover).toBeUndefined();
    // تأخیر پله‌ای صفر — فهرست بلند نباید در حالت reduced هم منتظر بماند
    expect(m.stagger(5)).toBe(0);
  });

  it("بدون این تنظیم، حرکت واقعاً هست (تست سبزِ خالی نباشد)", () => {
    const m = buildPreset(false);

    expect(m.reduced).toBe(false);
    expect(m.rise.initial.y).toBe(10);
    expect(m.slide.initial.x).toBe(14);
    expect(m.press.whileTap).toEqual({ scale: 0.97 });
    expect(m.hover.whileHover).toEqual({ y: -2 });
    expect(m.stagger(0)).toBe(0);
    expect(m.stagger(3)).toBeGreaterThan(0);
  });

  it("تأخیر پله‌ای سقف دارد — فهرست ۵۰ آیتمی کند نمی‌شود", () => {
    const m = buildPreset(false);
    expect(m.stagger(50)).toBe(m.stagger(12));
    expect(m.stagger(50)).toBeLessThan(1);
  });

  it("زمان‌بندی‌ها کوتاه‌اند — اگر کاربر انیمیشن را دید، طولانی بوده", () => {
    expect(DURATION.press).toBeLessThanOrEqual(0.15);
    expect(DURATION.enter).toBeLessThanOrEqual(0.35);
    expect(DURATION.page).toBeLessThanOrEqual(0.4);
  });

  it("وقتی preference نامعلوم یا API پشتیبانی‌نشده است، fail-closed می‌شود", () => {
    const unavailableSources: unknown[] = [
      undefined,
      vi.fn(() => {
        throw new Error("matchMedia unavailable");
      }),
      vi.fn(() => ({ matches: false, media: REDUCED_MOTION_QUERY })),
    ];

    for (const source of unavailableSources) {
      setMatchMedia(source);
      const { result, unmount } = renderHook(() => useMotionPreset());
      expect(result.current.reduced).toBe(true);
      expect(result.current.rise.initial).not.toHaveProperty("y");
      unmount();
    }
  });

  it("در SSR تا زمان hydration حالت محافظه‌کار را رندر می‌کند", () => {
    const media = installMatchMedia(false);
    const html = renderToString(<MotionAwareDraft />);

    expect(html).toContain("<output>reduced</output>");
    expect(media.matchMedia).not.toHaveBeenCalled();
  });

  it("تغییر زندهٔ preference، draft و focus را حفظ می‌کند و listener را پاک می‌کند", () => {
    const media = installMatchMedia(false);
    const { unmount } = render(<MotionAwareDraft />);
    const input = screen.getByRole("textbox", { name: "draft" }) as HTMLInputElement;

    fireEvent.change(input, { target: { value: "unfinished draft" } });
    input.focus();
    expect(screen.getByText("normal")).toBeTruthy();

    act(() => media.setMatches(true));
    expect(screen.getByText("reduced")).toBeTruthy();
    expect(input.value).toBe("unfinished draft");
    expect(document.activeElement).toBe(input);

    act(() => media.setMatches(false));
    expect(screen.getByText("normal")).toBeTruthy();
    expect(input.value).toBe("unfinished draft");
    expect(document.activeElement).toBe(input);
    expect(media.matchMedia).toHaveBeenCalledWith(REDUCED_MOTION_QUERY);

    unmount();
    expect(media.listeners.size).toBe(0);
    expect(media.removeEventListener).toHaveBeenCalledWith("change", expect.any(Function));
  });

  it("برای API قدیمی addListener نیز live update و cleanup دارد", () => {
    const media = installMatchMedia(false, "legacy");
    const { result, unmount } = renderHook(() => useMotionPreset());
    expect(result.current.reduced).toBe(false);

    act(() => media.setMatches(true));
    expect(result.current.reduced).toBe(true);
    unmount();

    expect(media.listeners.size).toBe(0);
    expect(media.removeListener).toHaveBeenCalledTimes(1);
  });

  it("خطای ثبت listener را نیز به حالت reduced تبدیل می‌کند", () => {
    const addEventListener = vi.fn(() => {
      throw new Error("listener registration failed");
    });
    const removeEventListener = vi.fn();
    const queryList = {
      matches: false,
      media: REDUCED_MOTION_QUERY,
      onchange: null,
      addEventListener,
      removeEventListener,
    } as unknown as MediaQueryList;
    setMatchMedia(vi.fn(() => queryList));

    const { result, unmount } = renderHook(() => useMotionPreset());
    expect(result.current.reduced).toBe(true);
    expect(addEventListener).toHaveBeenCalledTimes(1);
    unmount();
  });
});

describe("گیت منبع: مصرف‌کنندگان حرکت از helper مشترک تبعیت می‌کنند", () => {
  const consumers = [
    ["App.tsx", "App.tsx"],
    ["Analytics.tsx", "pages/Analytics.tsx"],
    ["CheckIn.tsx", "pages/CheckIn.tsx"],
    ["Dashboard.tsx", "pages/Dashboard.tsx"],
    ["Finance.tsx", "pages/Finance.tsx"],
    ["Members.tsx", "pages/Members.tsx"],
    ["Programs.tsx", "pages/Programs.tsx"],
    ["Settings.tsx", "pages/Settings.tsx"],
    ["Shop.tsx", "pages/Shop.tsx"],
    ["Feedback.tsx", "components/Feedback.tsx"],
    ["KpiCard.tsx", "components/KpiCard.tsx"],
    ["MemberTable.tsx", "components/MemberTable.tsx"],
    ["ScheduleTimeline.tsx", "components/ScheduleTimeline.tsx"],
    ["Sidebar.tsx", "components/Sidebar.tsx"],
    ["TopBar.tsx", "components/TopBar.tsx"],
    ["UpdateBanner.tsx", "components/UpdateBanner.tsx"],
    ["AttendanceChart.tsx", "components/AttendanceChart.tsx"],
    ["PeriodReportPanel.tsx", "components/PeriodReportPanel.tsx"],
    ["VisualConcepts.tsx", "visual-concepts/VisualConcepts.tsx"],
  ];

  for (const [name, relativePath] of consumers) {
    it(`${name} wires Framer Motion through useMotionPreset`, () => {
      const src = readFileSync(join(__dirname, "..", "src", relativePath), "utf8");
      expect(src).toContain("useMotionPreset");
      expect(src).not.toContain("useReducedMotion");
      expect(src, "stagger delay باید از helper سقف‌دار بیاید").not.toMatch(/delay:\s*i\s*\*/);
    });
  }

  it("VisualConcepts disables its shared-layout spring when reduced motion is active", () => {
    const src = readFileSync(
      join(__dirname, "..", "src", "visual-concepts", "VisualConcepts.tsx"),
      "utf8",
    );
    const marker = src.match(/<motion\.span\b[\s\S]*?\/>/)?.[0] ?? "";

    expect(marker).not.toBe("");
    expect(marker).toMatch(
      /layoutId=\{motionPreset\.reduced\s*\?\s*undefined\s*:\s*"active-direction"\}/,
    );
    expect(marker).toMatch(
      /motionPreset\.reduced\s*\?\s*\{\s*duration:\s*0\s*\}\s*:\s*\{\s*type:\s*"spring"/,
    );
    expect(src).toMatch(/motionPreset\.reduced\s*\?\s*motionPreset\.fade\s*:\s*motionPreset\.rise/);
    expect(src).toContain("motionPreset.hover.whileHover");
  });

  it("separate VisualConcepts lab has a delay/hover-safe reduced-motion stylesheet", () => {
    const css = readFileSync(
      join(__dirname, "..", "src", "visual-concepts", "visual-concepts.css"),
      "utf8",
    );
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
    expect(css).toContain("animation-delay: 0ms !important;");
    expect(css).toContain("transition-delay: 0ms !important;");
    expect(css).toContain(".direction-choice:hover { transform: none !important; }");
  });

  it("Recharts disables chart and tooltip animation when reduced motion is active", () => {
    for (const file of ["AttendanceChart.tsx", "PeriodReportPanel.tsx"]) {
      const src = readFileSync(join(__dirname, "..", "src", "components", file), "utf8");
      expect(src.match(/isAnimationActive=\{!motionPreset\.reduced\}/g)).toHaveLength(2);
    }
  });

  it("stylesheet برای CSS animation/transition و scroll در reduced-motion guard دارد", () => {
    const css = readFileSync(join(__dirname, "..", "src", "styles", "index.css"), "utf8");
    expect(css).toMatch(/@media\s*\(prefers-reduced-motion:\s*reduce\)/);
    expect(css).toContain("animation-duration: 0.01ms !important;");
    expect(css).toContain("animation-iteration-count: 1 !important;");
    expect(css).toContain("transition-duration: 0.01ms !important;");
    expect(css).toContain("scroll-behavior: auto !important;");
    expect(css).toContain(".btn-primary:active");
  });
});
