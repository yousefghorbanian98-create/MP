/**
 * M60/G4 — تست reduced-motion.
 *
 * چرا: اندازه‌گیری نشان داد ۸ صفحه انیمیشن داشتند و هیچ‌کدام تنظیم سیستمی
 * «کاهش حرکت» را نمی‌خواندند. برای کاربر با حساسیت دهلیزی این سرگیجه است، نه
 * سلیقه. این تست سه چیز را قفل می‌کند:
 *
 *  ۱) در حالت reduced، هیچ جابه‌جایی/مقیاسی وجود ندارد (فقط فید)
 *  ۲) در حالت عادی، حرکت هست (وگرنه «تست سبز بی‌معنا» می‌شد)
 *  ۳) هیچ صفحه‌ای بدون رعایت reduced-motion باقی نمانده (گیت روی سورس)
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const { buildPreset, useMotionPreset, DURATION } = await import("../src/lib/motion");

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

  it("هوک در jsdom با تنظیم سیستمی کار می‌کند (نه فقط منطق خالص)", () => {
    // framer-motion مقدار matchMedia را در بارگذاری ماژول می‌خواند؛ این تست
    // فقط ثابت می‌کند هوک Boolean برمی‌گرداند و کرش نمی‌کند.
    const { result } = renderHook(() => useMotionPreset());
    expect(typeof result.current.reduced).toBe("boolean");
    expect(result.current.fade.animate.opacity).toBe(1);
  });
});

describe("گیت سورس: هیچ صفحه‌ای بدون reduced-motion نمی‌ماند", () => {
  // هر صفحهٔ انیمیشن‌دار باید از useMotionPreset استفاده کند.
  const pages = [
    "Analytics",
    "CheckIn",
    "Dashboard",
    "Finance",
    "Members",
    "Programs",
    "Settings",
    "Shop",
  ];

  for (const page of pages) {
    it(`${page}.tsx از useMotionPreset استفاده می‌کند`, () => {
      const src = readFileSync(join(__dirname, "..", "src", "pages", `${page}.tsx`), "utf8");
      const hasMotion = /motion\./.test(src);
      if (!hasMotion) return; // صفحه‌ای که انیمیشن ندارد، تعهدی هم ندارد
      expect(src).toContain("useMotionPreset");
      /*
        duration دستی در صفحه ممنوع — ریتم باید از توکن بیاید.
        دو استثنای مستند:
          duration: 0   → خاموش‌کردن کامل انیمیشن (مثلاً اسپرینگ تب)
          duration: 2.8 → خط اسکن چهره، که چون شرطی داخل بلوک
                          `motionPreset.reduced ? … : …` است، در حالت reduced
                          اصلاً رندر نمی‌شود. تست زیر همان شرط را هم بررسی می‌کند.
      */
      const manualDurations = src.match(/duration:\s*[0-9.]+/g) ?? [];
      const allowed = manualDurations.filter((d) => /duration:\s*(0|2\.8)/.test(d));
      expect(manualDurations.length, `duration دستی: ${manualDurations.join(", ")}`).toBe(
        allowed.length,
      );

      // هر انیمیشن تکرارشونده باید مسیر reduced داشته باشد (بدترین حالت دهلیزی)
      if (/repeat:\s*Infinity/.test(src)) {
        expect(src, "انیمیشن بی‌پایان بدون مسیر reduced").toContain("motionPreset.reduced");
      }
    });
  }
});
