import { theme as antdTheme, type ThemeConfig } from "antd";
import sharedTokens from "../../../shared/design-tokens.json";

/** Studio consumes the shared palette instead of keeping a second runtime copy. */
export const designTokens = sharedTokens;

const { color, typography, radius } = designTokens;

/** Ant Design surfaces and controls use the same values as the Tailwind UI. */
export const mpTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: color.primary,
    colorInfo: color.info,
    colorSuccess: color.primaryLight,
    colorError: color.danger,
    colorWarning: color.warning,
    colorBgBase: color.background,
    colorBgContainer: color.surface,
    colorBgElevated: color.surface,
    colorBorder: color.border,
    colorTextBase: color.textPrimary,
    colorTextSecondary: color.textSecondary,
    // Dark foreground on bright fills keeps primary, warning, and status actions legible.
    colorTextLightSolid: color.background,
    borderRadius: radius.md,
    fontFamily: typography.fontFamily,
  },
};

/** Preserve component-specific opacity while deriving the hue from the shared token. */
export function colorWithAlpha(hex: string, alpha: number): string {
  const value = hex.replace("#", "");
  if (!/^[\da-fA-F]{6}$/.test(value)) {
    throw new Error(`Expected a six-digit hex color, got ${hex}`);
  }
  const [red, green, blue] = [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16));
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
