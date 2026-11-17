/**
 * تست منطق آپدیت تفاضلی وب (M20).
 */
import { describe, expect, it } from "vitest";
import { isNewer, parseVersion } from "../src/lib/update";

describe("update logic", () => {
  it("مقایسهٔ نسخه قطعی است", () => {
    expect(parseVersion("1.1.0")).toEqual([1, 1, 0]);
    expect(parseVersion("1.0")).toEqual([1, 0, 0]); // نرمال‌سازی
    expect(isNewer("1.1.0", "1.0.9")).toBe(true);
    expect(isNewer("1.0.0", "1.0.0")).toBe(false);
    expect(isNewer("2.0.0", "1.9.9")).toBe(true);
    expect(isNewer("1.0.1", "1.0.10")).toBe(false); // 10 > 1 در جزء سوم
  });
});
