import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { Jp7TrendPanel } from "../src/components/Jp7TrendPanel";
import { useAppStore } from "../src/stores/appStore";
import { Assessment } from "../src/pages/Assessment";

/**
 * G6 — روند JP7 باید تغییر را تفسیر کند، نه فقط نشان دهد، و هرگز
 * درصد چربی تأییدنشده (D-012) را نمایش ندهد.
 */

const SITES = ["chest", "triceps", "subscapular", "suprailiac", "abdomen", "thigh", "calf"];

function point(id: number, daysAgo: number, value: number) {
  const d = new Date(2026, 10, 15);
  d.setDate(d.getDate() - daysAgo);
  return {
    id,
    measured_at: d.toISOString(),
    sum_mm: value * 7,
    sites: Object.fromEntries(SITES.map((s) => [s, value])),
    body_fat_pct: null,
  };
}

function payload(over: Record<string, unknown> = {}) {
  return {
    member_id: 1,
    measurements: [point(1, 70, 14), point(2, 35, 12), point(3, 1, 10)],
    trend: {
      first_at: null,
      last_at: null,
      span_days: 69,
      first_sum_mm: 98,
      last_sum_mm: 70,
      delta_mm: -28,
      delta_mm_per_week: -2.84,
      biggest_change_site: "abdomen",
      biggest_change_mm: -12,
    },
    site_deltas: {
      abdomen: { first_mm: 14, last_mm: 2, delta_mm: -12 },
      chest: { first_mm: 14, last_mm: 10, delta_mm: -4 },
    },
    interpretation: {
      status: "decreasing",
      headline: "بافت زیرجلدی کاهش یافته است",
      detail: "مجموع چین‌ها ۲۸.۰ میلی‌متر کم شده — ولی کاهش چین همراه با افت قدرت",
      confidence: "high",
      threshold_mm: 2,
      suggestion: "بیشترین تغییر در «abdomen»",
    },
    data_state: "trend_available",
    body_fat_note:
      "درصد چربی محاسبه نشده و نمایش داده نمی‌شود: معادله تا تأیید مرجع مستقل قفل است (D-012).",
    rule_version: "jp7-trend-1.0",
    ...over,
  };
}

function mockFetch(body: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status: 200 }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  useAppStore.setState({ selectedMemberId: null });
});

describe("Jp7TrendPanel (G6)", () => {
  it("interprets the change instead of just displaying numbers", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("بافت زیرجلدی کاهش یافته است")).toBeTruthy());
    expect(screen.getByText(/افت قدرت/)).toBeTruthy();
    expect(screen.getByText("کاهش")).toBeTruthy();
  });

  it("never shows the locked body-fat percentage", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText(/D-012/)).toBeTruthy());
    expect(screen.queryByText(/%/)).toBeNull();
    expect(screen.queryByText(/درصد چربی:/)).toBeNull();
  });

  it("shows the biggest-change site as an actionable suggestion", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() => expect(screen.getAllByText(/abdomen/).length).toBeGreaterThan(0));
    expect(screen.getByText(/آستانهٔ تغییر/)).toBeTruthy();
  });

  it("declares insufficient data with the real count", async () => {
    localStorage.setItem("mp_token", "t");
    const single = payload({
      measurements: [point(1, 10, 12)],
      trend: null,
      site_deltas: {},
      interpretation: {
        status: "insufficient",
        headline: "برای تفسیر روند حداقل دو اندازه‌گیری لازم است",
        detail: "فقط 1 اندازه‌گیری ثبت شده. یک نقطه، روند نیست.",
        confidence: "insufficient",
      },
      data_state: "insufficient_measurements",
    });
    vi.stubGlobal("fetch", mockFetch(single));
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("داده ناکافی")).toBeTruthy());
    expect(screen.getByText(/حداقل دو نقطه لازم است/)).toBeTruthy();
  });

  it("says when nothing was ever measured", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      mockFetch(
        payload({
          measurements: [],
          trend: null,
          site_deltas: {},
          interpretation: {
            status: "insufficient",
            headline: "برای تفسیر روند حداقل دو اندازه‌گیری لازم است",
            detail: "فقط 0 اندازه‌گیری ثبت شده. یک نقطه، روند نیست.",
            confidence: "insufficient",
          },
          data_state: "insufficient_measurements",
        }),
      ),
    );
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText(/هیچ اندازه‌گیری JP7/)).toBeTruthy());
  });

  it("renders a sparkline from the real measurement series", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<Jp7TrendPanel memberId={1} />);

    await waitFor(() =>
      expect(screen.getByRole("img", { name: /نمودار تغییر مجموع چین/ })).toBeTruthy(),
    );
  });
});

describe("Assessment page", () => {
  it("asks for a member instead of assuming one", () => {
    render(<Assessment />);
    expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
  });

  it("renders the trend panel for the selected member", async () => {
    localStorage.setItem("mp_token", "t");
    useAppStore.setState({ selectedMemberId: 5 });
    const fetchMock = mockFetch(payload());
    vi.stubGlobal("fetch", fetchMock);

    render(<Assessment />);

    await waitFor(() => expect(screen.getByText(/روند چین‌های پوستی/)).toBeTruthy());
    expect(String(fetchMock.mock.calls[0][0])).toContain("/assessments/jp7/member/5/trend");
  });
});
