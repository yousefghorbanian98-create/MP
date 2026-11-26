// P-1 (F-28 نیمهٔ استودیو): ساعت یکتای استودیو.
// قرارداد: «امروز» در منطقهٔ فروشگاه (Asia/Tehran، همان پیش‌فرض app/config.py) حساب می‌شود.
import { describe, expect, it, afterEach } from "vitest";
import {
  SHOP_TIMEZONE,
  fromParts,
  now,
  setClock,
  shiftIsoDay,
  toDate,
  today,
} from "../src/lib/clock";

afterEach(() => setClock(null));

describe("clock — مرز نیمه‌شب تهران (C5)", () => {
  it("20:30Z همان روز تهران است: امروز = 2026-03-21", () => {
    setClock("2026-03-20T20:30:00Z");
    expect(today()).toBe("2026-03-21");
  });

  it("20:00Z هنوز 2026-03-20 در تهران است (23:30)", () => {
    setClock("2026-03-20T20:00:00Z");
    expect(today()).toBe("2026-03-20");
  });

  it("برعکس: 23:50Z یعنی 03:20 روز بعد در تهران", () => {
    setClock("2026-03-21T23:50:00Z");
    expect(today()).toBe("2026-03-22");
  });

  it("setClock(null) به ساعت واقعی برمی‌گردد", () => {
    setClock("2000-01-01T00:00:00Z");
    expect(now().getUTCFullYear()).toBe(2000);
    setClock(null);
    expect(now().getUTCFullYear()).toBeGreaterThanOrEqual(2026);
  });
});

describe("clock — قرارداد", () => {
  it("منطقهٔ فروشگاه همان پیش‌فرض بک‌اند است", () => {
    expect(SHOP_TIMEZONE).toBe("Asia/Tehran");
  });

  it("shiftIsoDay از مرز ماه و سال عبور می‌کند و بدون منطقهٔ محلی است", () => {
    expect(shiftIsoDay("2026-03-31", 1)).toBe("2026-04-01");
    expect(shiftIsoDay("2026-01-01", -1)).toBe("2025-12-31");
    expect(shiftIsoDay("2026-03-21", -30)).toBe("2026-02-19");
    expect(shiftIsoDay("2026-03-21", 0)).toBe("2026-03-21");
  });

  it("toDate و fromParts همان نتیجهٔ سازندهٔ قبلی را می‌دهند", () => {
    expect(toDate("2026-03-21T10:00:00Z").getTime()).toBe(Date.parse("2026-03-21T10:00:00Z"));
    expect(fromParts(2026, 2, 21).getDate()).toBe(21);
    expect(fromParts(2026, 2, 21).getMonth()).toBe(2);
  });
});
