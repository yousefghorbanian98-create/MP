import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ReadinessPanel } from "../src/components/ReadinessPanel";
import { useAppStore } from "../src/stores/appStore";

/**
 * G13 — پنل آمادگی باید **دلیل** تصمیم را نشان دهد، نه فقط عدد.
 * کاهش خودکار حجم بدون دلیل، جعبهٔ سیاه است.
 */

function payload(over: Record<string, unknown> = {}) {
  return {
    member_id: 1,
    program_id: 5,
    readiness: {
      score: 38.2,
      band: "fatigued",
      recommendation: "deload",
      volume_delta_sets: -1,
      signals: [
        { name: "rep_drop", value: 0.5, score: 50, reason: "۵ از ۱۰ تکرار — افت محسوس، نشانهٔ خستگی" },
        { name: "soreness", value: 9, score: 10, reason: "درد ۹/۱۰ — شدید" },
        { name: "rir_mismatch", value: null, score: null, reason: "RIR هدف یا واقعی ثبت نشده" },
      ],
      missing_signals: ["rir_mismatch"],
      reason: "امتیاز آمادگی 38.2 زیر آستانهٔ 55 است — حجم خودکار یک ست کاهش می‌یابد",
      weights: { rep_drop: 0.35, rir_mismatch: 0.25, soreness: 0.2, volume_spike: 0.2 },
      thresholds: {
        deload_below: 55,
        recovery_below: 40,
        rir_tolerance: 1,
        volume_spike_ratio: 1.3,
      },
      actionable: true,
      rule_version: "readiness-1.0",
    },
    data_counts: { feedback_rows: 3, sets_last_7_days: 6, sets_prior_7_days: 4 },
    reason: "امتیاز آمادگی 38.2 زیر آستانهٔ 55 است",
    note: "RIR هدف در برنامه ذخیره نمی‌شود، پس سیگنال «اختلاف RIR» نامعلوم می‌ماند",
    rule_version: "readiness-report-1.0",
    ...over,
  };
}

function mockFetch(body: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status: 200 }));
}

beforeEach(() => {
  useAppStore.setState({ selectedMemberId: 1 });
  localStorage.setItem("mp_token", "t");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  useAppStore.setState({ selectedMemberId: null });
});

describe("ReadinessPanel (G13)", () => {
  it("asks for a member instead of assuming one", () => {
    useAppStore.setState({ selectedMemberId: null });
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<ReadinessPanel />);
    expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
  });

  it("shows the score, the band and the automatic deload recommendation", async () => {
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<ReadinessPanel />);

    await waitFor(() => expect(screen.getByText("خسته")).toBeTruthy());
    expect(screen.getByText("کاهش خودکار حجم (−۱ ست)")).toBeTruthy();
    expect(screen.getByText(/زیر آستانهٔ 55/)).toBeTruthy();
  });

  it("explains every signal, including the unknown one", async () => {
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<ReadinessPanel />);

    await waitFor(() => expect(screen.getByText("افت تکرار")).toBeTruthy());
    expect(screen.getByText(/افت محسوس، نشانهٔ خستگی/)).toBeTruthy();
    expect(screen.getByText("نامعلوم")).toBeTruthy();
    expect(screen.getByText(/وزن این سیگنال‌ها به بقیه توزیع شده/)).toBeTruthy();
  });

  it("says why RIR is unknown instead of hiding it", async () => {
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<ReadinessPanel />);

    await waitFor(() => expect(screen.getByText(/RIR هدف در برنامه ذخیره نمی‌شود/)).toBeTruthy());
  });

  it("shows the raw data counts behind the score", async () => {
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<ReadinessPanel />);

    await waitFor(() => expect(screen.getByText(/۳ بازخورد ست/)).toBeTruthy());
    expect(screen.getByText(/۶ ست در ۷ روز اخیر/)).toBeTruthy();
  });

  it("does not invent a score when there is no feedback", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        member_id: 1,
        program_id: 5,
        readiness: null,
        reason: "هیچ بازخورد ستی برای این برنامه ثبت نشده — آمادگی سنجیده نمی‌شود",
        rule_version: "readiness-report-1.0",
      }),
    );
    render(<ReadinessPanel />);

    await waitFor(() =>
      expect(screen.getByText(/هیچ بازخورد ستی برای این برنامه ثبت نشده/)).toBeTruthy(),
    );
    expect(screen.queryByText("کاهش خودکار حجم (−۱ ست)")).toBeNull();
  });

  it("keeps volume when the athlete is ready", async () => {
    const ready = payload();
    ready.readiness.score = 96;
    ready.readiness.band = "ready";
    ready.readiness.recommendation = "keep";
    ready.readiness.volume_delta_sets = 0;
    ready.readiness.signals = [
      { name: "rep_drop", value: 1, score: 100, reason: "۱۰ تکرار از پایهٔ ۱۰ — بدون افت" },
    ];
    ready.readiness.missing_signals = [];
    vi.stubGlobal("fetch", mockFetch(ready));
    render(<ReadinessPanel />);

    await waitFor(() => expect(screen.getByText("آماده")).toBeTruthy());
    expect(screen.getByText("حفظ حجم")).toBeTruthy();
  });
});
