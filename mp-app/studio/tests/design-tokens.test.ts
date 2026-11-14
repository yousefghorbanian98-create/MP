import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * تست همگام‌سازی توکن‌ها (M07) — tailwind.config.js باید با design-tokens.json یکی باشد.
 * هرگونه واگرایی = چرخه قبول نیست (قاعدهٔ مکانیکی‌سازی درس‌ها).
 */
describe("design tokens sync", () => {
  const tokens = JSON.parse(
    readFileSync(resolve(__dirname, "../../shared/design-tokens.json"), "utf-8")
  );
  const tailwind = readFileSync(resolve(__dirname, "../tailwind.config.js"), "utf-8");

  it("primary color matches", () => {
    expect(tailwind).toContain(tokens.color.primary);
  });

  it("accent color matches", () => {
    expect(tailwind).toContain(tokens.color.accent);
  });

  it("background color matches", () => {
    expect(tailwind).toContain(tokens.color.background);
  });

  it("surface color matches", () => {
    expect(tailwind).toContain(tokens.color.surface);
  });

  it("font family includes Vazirmatn", () => {
    expect(tokens.typography.fontFamily).toContain("Vazirmatn");
    expect(tailwind).toContain("Vazirmatn");
  });
});

/** WCAG contrast — گیت کنتراست برند (مکانیکی). */
function luminance(hex: string): number {
  const n = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16) / 255);
  const f = (c: number) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

function contrast(h1: string, h2: string): number {
  const [l1, l2] = [luminance(h1), luminance(h2)].sort((a, b) => b - a);
  return (l1 + 0.05) / (l2 + 0.05);
}

describe("WCAG contrast gates", () => {
  it("text on background passes AA (4.5)", () => {
    expect(contrast("#F3F6F8", "#0B0F14")).toBeGreaterThanOrEqual(4.5);
  });
  it("primary on background passes AA large (3.0)", () => {
    expect(contrast("#00B86A", "#0B0F14")).toBeGreaterThanOrEqual(3.0);
  });
  it("accent on background passes AA large (3.0)", () => {
    expect(contrast("#FFD700", "#0B0F14")).toBeGreaterThanOrEqual(3.0);
  });
  it("dim text on background passes AA (4.5)", () => {
    expect(contrast("#9CA3AF", "#0B0F14")).toBeGreaterThanOrEqual(4.5);
  });
});
