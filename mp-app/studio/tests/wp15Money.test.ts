/**
 * WP 1.5 (F‑09) — مبلغ ریالی در استودیو فقط عدد صحیح ایمن است.
 * قبل از اصلاح: Number(...) برای مبالغ، «1e3»، «1000.5»، «2^53+1» را بی‌صدا می‌پذیرفت.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { MAX_SAFE_RIAL, formatRial, parseRial } from "../src/lib/money";

describe("parseRial", () => {
  it("accepts plain integers, Persian digits and grouping separators", () => {
    expect(parseRial("1000")).toBe(1000);
    expect(parseRial("۱۰۰۰۰")).toBe(10000);
    expect(parseRial("1,000,000")).toBe(1000000);
    expect(parseRial("۱٬۰۰۰")).toBe(1000);
    expect(parseRial(" 2000 ")).toBe(2000);
  });

  it.each(["", "abc", "1e3", "1000.5", "-1000", "0x10", "1000.0", "1 000 000 0.5"])(
    "rejects %s",
    (raw) => {
      expect(parseRial(raw)).toBeNull();
    },
  );

  it("rejects values above 2^53-1", () => {
    expect(MAX_SAFE_RIAL).toBe(Number.MAX_SAFE_INTEGER);
    expect(parseRial("9007199254740991")).toBe(MAX_SAFE_RIAL);
    expect(parseRial("9007199254740992")).toBeNull();
    expect(parseRial("1000000000000000000")).toBeNull();
  });

  it("formats with Persian digits and never loses precision for safe ints", () => {
    expect(formatRial(1234567)).toBe("۱٬۲۳۴٬۵۶۷");
  });
});

describe("money call sites no longer use Number() on rial fields", () => {
  const root = resolve(__dirname, "../src");
  it.each(["components/PaymentPanel.tsx", "components/CouponPanel.tsx", "pages/Shop.tsx", "pages/Analytics.tsx"])(
    "%s has no Number() on rial fields",
    (file) => {
      const src = readFileSync(resolve(root, file), "utf8");
      expect(src).not.toMatch(/price_rial: Number\(|Number\(row\.total_paid_rial\)|Number\(amount\)/);
    },
  );
  it("PaymentPanel and CouponPanel use parseRial", () => {
    expect(readFileSync(resolve(root, "components/PaymentPanel.tsx"), "utf8")).toMatch(/parseRial\(amount\)/);
    expect(readFileSync(resolve(root, "components/CouponPanel.tsx"), "utf8")).toMatch(/parseRial\(value\)/);
    expect(readFileSync(resolve(root, "components/CouponPanel.tsx"), "utf8")).not.toMatch(/Number\(value\)/);
  });
});
