import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import tailwindConfig from "../tailwind.config.js";
import { designTokens as runtimeTokens, mpTheme } from "../src/lib/designTokens";

/** Shared design tokens must reach the real Tailwind and Ant Design runtime themes. */
describe("design tokens sync", () => {
  const tokens = JSON.parse(
    readFileSync(resolve(__dirname, "../../shared/design-tokens.json"), "utf-8"),
  );
  const tailwind = tailwindConfig as unknown as {
    theme: {
      extend: {
        colors: Record<string, string | Record<string, string>>;
        fontFamily: Record<string, string[]>;
        borderRadius: Record<string, string>;
      };
    };
  };
  const palette = tailwind.theme.extend.colors;
  const primary = palette.primary as Record<string, string>;
  const accent = palette.accent as Record<string, string>;
  const ink = palette.ink as Record<string, string>;

  it("drives the runtime palettes from the shared file", () => {
    expect(runtimeTokens.color).toEqual(tokens.color);
    expect(palette.bg).toBe(tokens.color.background);
    expect(palette.surface).toBe(tokens.color.surface);
    expect(palette["brand-border"]).toBe(tokens.color.border);
    expect(primary.DEFAULT).toBe(tokens.color.primary);
    expect(primary.dark).toBe(tokens.color.primaryDark);
    expect(primary.light).toBe(tokens.color.primaryLight);
    expect(accent.DEFAULT).toBe(tokens.color.accent);
    expect(accent.soft).toBe(tokens.color.accentSoft);
    expect(ink.DEFAULT).toBe(tokens.color.textPrimary);
    expect(ink.dim).toBe(tokens.color.textSecondary);
    expect(palette.danger).toBe(tokens.color.danger);
    expect(palette.warning).toBe(tokens.color.warning);
    expect(palette.info).toBe(tokens.color.info);
  });

  it("keeps Ant Design surfaces, typography, and action colors aligned", () => {
    const antd = mpTheme.token;
    expect(antd?.colorPrimary).toBe(tokens.color.primary);
    expect(antd?.colorBgBase).toBe(tokens.color.background);
    expect(antd?.colorBgContainer).toBe(tokens.color.surface);
    expect(antd?.colorBgElevated).toBe(tokens.color.surface);
    expect(antd?.colorBorder).toBe(tokens.color.border);
    expect(antd?.colorTextBase).toBe(tokens.color.textPrimary);
    expect(antd?.colorTextSecondary).toBe(tokens.color.textSecondary);
    expect(antd?.colorTextLightSolid).toBe(tokens.color.background);
    expect(antd?.fontFamily).toBe(tokens.typography.fontFamily);
    expect(antd?.borderRadius).toBe(tokens.radius.md);
  });

  it("keeps Tailwind font and card radius aligned", () => {
    expect(tokens.typography.fontFamily).toContain("Vazirmatn");
    expect(tailwind.theme.extend.fontFamily.vazir).toEqual(
      tokens.typography.fontFamily.split(",").map((family) => family.trim()),
    );
    expect(tailwind.theme.extend.borderRadius.card).toBe(`${tokens.radius.lg}px`);
  });
});

/** WCAG contrast — brand colors on base surfaces and text on filled actions. */
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

const tokens = JSON.parse(
  readFileSync(resolve(__dirname, "../../shared/design-tokens.json"), "utf-8"),
);

describe("WCAG contrast gates", () => {
  it("text on background passes AA (4.5)", () => {
    expect(contrast(tokens.color.textPrimary, tokens.color.background)).toBeGreaterThanOrEqual(4.5);
  });
  it("primary on background passes AA large (3.0)", () => {
    expect(contrast(tokens.color.primary, tokens.color.background)).toBeGreaterThanOrEqual(3.0);
  });
  it("accent on background passes AA large (3.0)", () => {
    expect(contrast(tokens.color.accent, tokens.color.background)).toBeGreaterThanOrEqual(3.0);
  });
  it("dim text on background passes AA (4.5)", () => {
    expect(contrast(tokens.color.textSecondary, tokens.color.background)).toBeGreaterThanOrEqual(4.5);
  });
  it("dark foreground on filled brand controls passes AA (4.5)", () => {
    expect(contrast(tokens.color.background, tokens.color.primary)).toBeGreaterThanOrEqual(4.5);
    expect(contrast(tokens.color.background, tokens.color.accent)).toBeGreaterThanOrEqual(4.5);
  });
});
