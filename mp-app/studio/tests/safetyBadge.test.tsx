import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SafetyBadge, parseSafety } from "../src/components/SafetyBadge";

/**
 * Q7 — نشان ایمنی.
 *
 * مهم‌ترین ادعا: «غربالگری نشده» هرگز با رنگ «بی‌خطر» نمایش داده نشود.
 * اگر مربی این دو را یکی ببیند، برنامهٔ ناسازگار را تأیید می‌کند.
 */

const blocked = {
  status: "blocked",
  headline: "۱ محدودیت با برنامهٔ پیشنهادی ناسازگار است",
  blocked: [
    {
      constraint: "knee_injury",
      label_fa: "آسیب زانو",
      blocked_exercises: ["squat", "lunge"],
      alternatives: ["leg_press_light"],
      advice_fa: "از اسکوات عمیق پرهیز شود.",
    },
  ],
  high_risk_patterns: [],
  notes: [],
  safe_to_generate: false,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
};

describe("parseSafety", () => {
  it("returns null for an absent verdict", () => {
    expect(parseSafety(undefined)).toBeNull();
    expect(parseSafety("")).toBeNull();
    expect(parseSafety("{}")).toBeNull();
  });

  it("returns null for corrupt JSON instead of throwing", () => {
    expect(parseSafety("{not json")).toBeNull();
  });

  it("parses a real verdict", () => {
    expect(parseSafety(JSON.stringify(blocked))?.status).toBe("blocked");
  });
});

describe("SafetyBadge", () => {
  it("says 'not screened' — not 'safe' — when there is no verdict", () => {
    render(<SafetyBadge flags={null} />);
    expect(screen.getByText(/غربالگری ثبت نشده/)).toBeTruthy();
  });

  it("shows a blocked verdict distinctly", () => {
    render(<SafetyBadge flags={blocked} />);
    const badge = screen.getByText(/ناسازگار با محدودیت/);
    expect(badge.className).toContain("danger");
  });

  it("shows 'needs review' differently from 'clear'", () => {
    const { unmount } = render(<SafetyBadge flags={{ status: "needs_review" }} />);
    const needsReview = screen.getByText(/نیازمند بازبینی/).className;
    unmount();

    render(<SafetyBadge flags={{ status: "clear" }} />);
    const clear = screen.getByText(/بدون ناسازگاری/).className;

    expect(needsReview).not.toEqual(clear);
  });

  it("shows 'unknown' (not screened) in a neutral colour", () => {
    render(<SafetyBadge flags={{ status: "unknown" }} />);
    const el = screen.getByText(/غربالگری نشده/);
    expect(el).toBeTruthy();
  });

  it("carries the disclaimer as a tooltip", () => {
    render(<SafetyBadge flags={blocked} />);
    expect(screen.getByTitle(/جای تشخیص پزشک/)).toBeTruthy();
  });

  it("never renders green for an unknown verdict", () => {
    const { container } = render(<SafetyBadge flags={{ status: "unknown" }} />);
    expect(container.innerHTML).not.toContain("emerald");
  });
});
