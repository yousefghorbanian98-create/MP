import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SafetyBadge, parseSafety } from "../src/components/SafetyBadge";
import {
  ProgramSafetyPanel,
  executionBlockReason,
  isExecutable,
  safetyStatus,
} from "../src/components/ProgramSafetyPanel";

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

/**
 * MEM-06 — آزمون اصلی: چهار وضعیت باید **متن متفاوت** داشته باشند.
 *
 * تستی که فقط وجود یک کلمه را چک کند چیزی را تضمین نمی‌کند؛ همان اشتباهی که در
 * `MemberTodayProgram` رخ داده بود (یک پیام برای سه وضعیت). پس اینجا متن کامل هر
 * چهار رندر با هم مقایسه می‌شود.
 */
const needsReview = {
  status: "needs_review",
  headline: "محدودیت ناشناخته ثبت شده — نیازمند بازبینی مربی",
  blocked: [],
  high_risk_patterns: [],
  notes: ["تأییدیهٔ پزشک ثبت نشده است."],
  safe_to_generate: false,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
};

const unknownVerdict = {
  status: "unknown",
  headline: "هیچ محدودیت پزشکی ثبت نشده است — یعنی نامعلوم، نه بی‌خطر",
  blocked: [],
  high_risk_patterns: [],
  notes: [],
  safe_to_generate: false,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
};

const clearVerdict = {
  status: "clear",
  headline: "برنامه با محدودیت‌های ثبت‌شده ناسازگاری ندارد",
  blocked: [],
  high_risk_patterns: [],
  notes: [],
  safe_to_generate: true,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
};

describe("ProgramSafetyPanel — four statuses, four different texts (MEM-06)", () => {
  const marker: Record<string, RegExp> = {
    blocked: /این برنامه برای شما ناسازگار است/,
    needs_review: /نیازمند بازبینی مربی/,
    unknown: /غربالگری نشده — نه «بی‌خطر»/,
    clear: /بدون ناسازگاری با محدودیت‌های ثبت‌شده/,
  };

  it("renders four pairwise-different bodies, each with its own marker", () => {
    const bodies: Record<string, string> = {};
    for (const [status, flags] of Object.entries({
      blocked,
      needs_review: needsReview,
      unknown: unknownVerdict,
      clear: clearVerdict,
    })) {
      const { container, unmount } = render(<ProgramSafetyPanel flags={flags} />);
      bodies[status] = container.textContent ?? "";
      expect(screen.getAllByText(marker[status]).length).toBeGreaterThan(0);
      // هیچ وضعیتی متن بقیه را تکرار نمی‌کند.
      for (const [otherStatus, otherMarker] of Object.entries(marker)) {
        if (otherStatus === status) continue;
        expect(bodies[status].match(otherMarker)).toBeNull();
      }
      unmount();
    }
    const distinct = new Set(Object.values(bodies));
    expect(distinct.size).toBe(4);
  });

  it("blocked names the constraint, blocked movements and alternatives", () => {
    render(<ProgramSafetyPanel flags={blocked} />);
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("آسیب زانو");
    expect(alert.textContent).toContain("squat");
    expect(alert.textContent).toContain("leg_press_light");
    expect(alert.textContent).toContain("دلیل توقف اجرا");
  });

  it("unknown is not dressed up as safe: no green, no 'clear' wording", () => {
    const { container } = render(<ProgramSafetyPanel flags={unknownVerdict} />);
    expect(container.innerHTML).not.toContain("emerald");
    expect(container.textContent).not.toContain("بدون ناسازگاری");
    expect(container.textContent).toContain("نامعلوم، نه بی‌خطر");
  });

  it("prints the reason as visible text, not only as a tooltip", () => {
    render(<ProgramSafetyPanel flags={needsReview} />);
    expect(screen.getByText(/دلیل توقف اجرا:/)).toBeTruthy();
  });

  it("shows 'not screened' for an absent verdict instead of falling back to clear", () => {
    render(<ProgramSafetyPanel flags={null} />);
    expect(screen.getByText(/غربالگری نشده — نه «بی‌خطر»/)).toBeTruthy();
    expect(screen.queryByText(/بدون ناسازگاری با محدودیت‌های ثبت‌شده/)).toBeNull();
  });
});

describe("safetyStatus / isExecutable — truth table (MEM-06 gate)", () => {
  it("maps unknown server values to 'unknown', never to 'clear'", () => {
    expect(safetyStatus(null)).toBe("unknown");
    expect(safetyStatus({ status: "weird" })).toBe("unknown");
    expect(safetyStatus({})).toBe("unknown");
  });

  it("only clear + safe_to_generate=true is executable", () => {
    expect(isExecutable(clearVerdict)).toBe(true);
    expect(isExecutable({ status: "clear", safe_to_generate: undefined })).toBe(false);
    expect(isExecutable({ status: "clear", safe_to_generate: false })).toBe(false);
    expect(isExecutable(blocked)).toBe(false);
    expect(isExecutable(needsReview)).toBe(false);
    expect(isExecutable(unknownVerdict)).toBe(false);
    expect(isExecutable(null)).toBe(false);
  });

  it("gives a different reason for every status", () => {
    const reasons = [
      executionBlockReason(blocked),
      executionBlockReason(needsReview),
      executionBlockReason(unknownVerdict),
      executionBlockReason({ status: "clear", safe_to_generate: false }),
    ];
    expect(new Set(reasons).size).toBe(4);
  });
});
