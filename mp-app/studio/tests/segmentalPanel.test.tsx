import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SegmentalPanel } from "../src/components/SegmentalPanel";
import { useAppStore } from "../src/stores/appStore";

/**
 * M54-c1 — پنل سگمنتال.
 *
 * چیزهایی که محافظت می‌شوند:
 *   • ادعای صادقانه: «InBody نیست» همیشه دیده می‌شود
 *   • سیگنال نامعلوم ⇒ «نامعلوم»، هرگز صفر
 *   • ورودی نامعتبر هرگز به سرور نمی‌رود
 */

function payload(over: Record<string, unknown> = {}) {
  return {
    member_id: 1,
    latest: {
      id: 3,
      member_id: 1,
      measured_at: "2026-11-15T10:00:00Z",
      neck_cm: null,
      chest_cm: null,
      waist_cm: 88,
      hip_cm: 100,
      upper_arm_right_cm: 37,
      upper_arm_left_cm: 34,
      thigh_right_cm: null,
      thigh_left_cm: null,
      calf_right_cm: null,
      calf_left_cm: null,
      quality: null,
      notes: "",
    },
    analysis: {
      ratios: {
        waist_to_height: {
          value: 0.494,
          band: "normal",
          reason: "نسبت کمر به قد 0.49 — در محدودهٔ مطلوب",
          threshold: 0.5,
        },
        waist_to_hip: {
          value: 0.88,
          band: "normal",
          reason: "نسبت کمر به باسن 0.88",
          threshold: 0.9,
        },
        arm_to_waist: {
          value: null,
          band: "unknown",
          reason: "محیط بازو یا کمر ثبت نشده",
          threshold: 0.36,
        },
      },
      asymmetry: {
        upper_arm: {
          right_cm: 37,
          left_cm: 34,
          delta_cm: 3,
          dominant_side: "right",
          band: "notable",
          reason: "اختلاف 3.0 سانتی‌متر — نامتقارنی محسوس",
          threshold_cm: 1,
        },
        thigh: null,
        calf: null,
      },
      headline: "نامتقارنی محسوس در upper_arm",
      missing: ["whtr"],
      note: "این تحلیل آنتروپومتریک است، نه ترکیب بدنی سگمنتی.",
      rule_version: "segmental-1.0",
    },
    trend: null,
    measurements_count: 1,
    reason: "تحلیل بر پایهٔ آخرین اندازه‌گیری",
    note: "این تحلیل آنتروپومتریک است، نه ترکیب بدنی سگمنتی.",
    rule_version: "segmental-report-1.0",
    ...over,
  };
}

function stub(routes: { match: RegExp; body: unknown; status?: number }[]) {
  const calls: { method: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = (init?.method ?? "GET").toUpperCase();
      calls.push({ method, body: init?.body ? JSON.parse(String(init.body)) : null });
      const hit = routes.find((r) => r.match.test(`${method} ${url}`));
      if (!hit) throw new Error(`unexpected ${method} ${url}`);
      return new Response(JSON.stringify(hit.body), { status: hit.status ?? 200 });
    }),
  );
  return calls;
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

describe("SegmentalPanel (M54-c1)", () => {
  it("asks for a member instead of guessing", () => {
    useAppStore.setState({ selectedMemberId: null });
    vi.stubGlobal("fetch", vi.fn());
    render(<SegmentalPanel />);
    expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
  });

  it("always states that this is NOT body composition", async () => {
    stub([{ match: /GET/, body: payload() }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/InBody/)).toBeTruthy());
    expect(screen.getByText(/ترکیب بدنی سگمنتی/)).toBeTruthy();
  });

  it("shows real ratios and renders an unknown ratio as نامعلوم", async () => {
    stub([{ match: /GET/, body: payload() }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/دور کمر به قد/)).toBeTruthy());

    expect(screen.getByText(/۰٫۴۹۴/)).toBeTruthy();
    expect(screen.getAllByText(/نامعلوم/).length).toBeGreaterThan(0); // arm_to_waist.value === null
  });

  it("reports asymmetry with both sides", async () => {
    stub([{ match: /GET/, body: payload() }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getAllByText(/نامتقارنی محسوس/).length).toBeGreaterThan(0));
    expect(screen.getByText(/راست ۳۷ \/ چپ ۳۴/)).toBeTruthy();
  });

  it("does not render asymmetry rows when a side is missing", async () => {
    const p = payload();
    (p.analysis.asymmetry as Record<string, unknown>).upper_arm = null;
    stub([{ match: /GET/, body: p }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/هر دو سمت باید/)).toBeTruthy());
  });

  it("refuses to submit an empty form", async () => {
    const calls = stub([{ match: /GET/, body: payload() }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/دور کمر به قد/)).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: /ثبت اندازه/ }));
    await waitFor(() => expect(screen.getByText(/حداقل یک محیط/)).toBeTruthy());
    expect(calls.every((c) => c.method === "GET")).toBe(true);
  });

  it("refuses a nonsensical circumference without calling the API", async () => {
    const calls = stub([{ match: /GET/, body: payload() }]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/دور کمر به قد/)).toBeTruthy());

    fireEvent.change(screen.getByLabelText(/^کمر/), { target: { value: "999" } });
    fireEvent.click(screen.getByRole("button", { name: /ثبت اندازه/ }));

    await waitFor(() => expect(screen.getByText(/عددی بین ۱ و ۳۰۰/)).toBeTruthy());
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("sends only the filled fields and reloads the report", async () => {
    const calls = stub([
      { match: /GET/, body: payload() },
      { match: /POST/, body: { id: 9, member_id: 1, waist_cm: 87 } },
    ]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/دور کمر به قد/)).toBeTruthy());

    fireEvent.change(screen.getByLabelText(/^کمر/), { target: { value: "87" } });
    fireEvent.click(screen.getByRole("button", { name: /ثبت اندازه/ }));

    await waitFor(() => expect(screen.getByText(/اندازه‌گیری ثبت شد/)).toBeTruthy());
    const post = calls.find((c) => c.method === "POST");
    expect(post?.body).toEqual({ member_id: 1, waist_cm: 87 });
    // گزارش بعد از ثبت دوباره خوانده می‌شود
    expect(calls.filter((c) => c.method === "GET").length).toBeGreaterThan(1);
  });

  it("shows the member-facing reason when there is no measurement yet", async () => {
    stub([
      {
        match: /GET/,
        body: payload({
          latest: null,
          analysis: null,
          trend: null,
          measurements_count: 0,
          reason: "هیچ اندازه‌گیری محیط اندامی برای این عضو ثبت نشده است",
        }),
      },
    ]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/هیچ اندازه‌گیری محیط اندامی/)).toBeTruthy());
  });

  it("shows the trend headline once two measurements exist", async () => {
    stub([
      {
        match: /GET/,
        body: payload({
          measurements_count: 2,
          trend: {
            span_days: 60,
            changes_cm: { waist_cm: -6 },
            biggest_change: "waist_cm",
            headline: "بیشترین تغییر: کاهش ۶ سانتی‌متر در waist_cm",
            rule_version: "segmental-1.0",
          },
        }),
      },
    ]);
    render(<SegmentalPanel />);
    await waitFor(() => expect(screen.getByText(/روند در ۶۰ روز/)).toBeTruthy());
    expect(screen.getByText(/کاهش ۶ سانتی‌متر/)).toBeTruthy();
  });
});
