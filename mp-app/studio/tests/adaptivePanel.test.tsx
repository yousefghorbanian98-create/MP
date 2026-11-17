import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdaptiveNutritionPanel } from "../src/components/AdaptiveNutritionPanel";

/**
 * G3 — پنل تغذیهٔ سازگار باید صادق باشد:
 *   • داده کافی نیست ⇒ «نامعلوم»، نه عدد حدسی
 *   • عدد دارد ⇒ TDEE، روند، دقت و دلیل را با هم نشان دهد
 *   • سقف گام باید دیده شود تا مربی فکر نکند عدد نهایی است
 */

function payload(over: Record<string, unknown> = {}) {
  return {
    member_id: 1,
    goal: "weight_loss",
    current_target_kcal: 2100,
    plan_id: 3,
    estimate: {
      tdee_kcal: 2650.4,
      confidence: "medium",
      data_state: "estimated",
      mean_intake_kcal: 2100,
      weight_change_kcal_per_day: -550,
      reason: "میانگین مصرف 2100 کالری در 28 روز ثبت‌شده، روند وزن -0.50 کیلوگرم/هفته ⇒ TDEE ≈ 2650 کالری",
      trend: {
        slope_kg_per_week: -0.5,
        smoothed_start_kg: 80,
        smoothed_end_kg: 78,
        days_used: 28,
        span_days: 27,
        confidence: "medium",
        reason: "شیب روند -0.50 کیلوگرم در هفته",
        notes: [],
      },
      assumptions: ["هر کیلوگرم تغییر وزن ≈ 7700 کیلوکالری", "فقط روزهای ثبت‌شده"],
      rule_version: "adaptive-nutrition-1.0",
    },
    suggestion: {
      suggested_target_kcal: 2250,
      delta_kcal: 150,
      action: "increase",
      capped: true,
      reason: "TDEE واقعی 2650 × ضریب «weight_loss» = 2252",
      rule_version: "adaptive-nutrition-1.0",
    },
    data_counts: { weight_entries: 28, intake_days: 28 },
    latest_weight_kg: 78,
    rule_version: "adaptive-nutrition-1.0",
    ...over,
  };
}

function mockFetch(body: unknown, logBody?: unknown) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/weight-logs")) {
      return new Response(
        JSON.stringify(logBody ?? { logged: 1, updated: 0, rejected: [], reason: "۱ وزن ثبت شد", rule_version: "food-logging-1.0" }),
        { status: 200 },
      );
    }
    return new Response(JSON.stringify(body), { status: 200 });
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("AdaptiveNutritionPanel (G3)", () => {
  it("shows the estimated TDEE with its confidence and reason", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<AdaptiveNutritionPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("۲٬۶۵۰")).toBeTruthy());
    expect(screen.getByText("اطمینان متوسط")).toBeTruthy();
    expect(screen.getAllByText(/-0\.50/).length).toBeGreaterThan(0);
    expect(screen.getByText(/TDEE ≈ 2650/)).toBeTruthy();
  });

  it("says unknown instead of guessing when data is insufficient", async () => {
    localStorage.setItem("mp_token", "t");
    const insufficient = payload({
      current_target_kcal: null,
      plan_id: null,
      estimate: {
        tdee_kcal: null,
        confidence: "insufficient",
        data_state: "insufficient_weight",
        mean_intake_kcal: 1800,
        reason: "فقط ۵ اندازه‌گیری وزن ثبت شده؛ حداقل ۱۴ لازم است — روند محاسبه نشد",
        trend: {
          slope_kg_per_week: null,
          smoothed_start_kg: null,
          smoothed_end_kg: null,
          days_used: 5,
          span_days: 4,
          confidence: "insufficient",
          reason: "داده کم",
          notes: [],
        },
        rule_version: "adaptive-nutrition-1.0",
      },
      suggestion: {
        suggested_target_kcal: null,
        delta_kcal: 0,
        action: "none",
        reason: "TDEE یا هدف فعلی نامعلوم است — اصلاحی پیشنهاد نمی‌شود",
        rule_version: "adaptive-nutrition-1.0",
      },
      data_counts: { weight_entries: 5, intake_days: 5 },
      latest_weight_kg: 80,
    });
    vi.stubGlobal("fetch", mockFetch(insufficient));
    render(<AdaptiveNutritionPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("نامعلوم")).toBeTruthy());
    expect(screen.getByText("داده ناکافی")).toBeTruthy();
    expect(screen.getByText(/حداقل ۱۴ لازم است/)).toBeTruthy();
    expect(screen.getByText("بدون برنامه")).toBeTruthy();
  });

  it("reveals the step cap so the number is not mistaken for the final answer", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(payload()));
    render(<AdaptiveNutritionPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("افزایش کالری")).toBeTruthy());
    expect(screen.getByText("(سقف ۱۵٪)")).toBeTruthy();
  });

  it("shows trend data-quality warnings", async () => {
    localStorage.setItem("mp_token", "t");
    const noisy = payload();
    noisy.estimate.trend.notes = ["پراکندگی وزن بالا است (میانهٔ انحراف ۱.۲ کیلوگرم)"];
    vi.stubGlobal("fetch", mockFetch(noisy));
    render(<AdaptiveNutritionPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText(/پراکندگی وزن بالا/)).toBeTruthy());
  });

  it("posts a weight entry and confirms it", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = mockFetch(payload());
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<AdaptiveNutritionPanel memberId={7} />);

    await waitFor(() => expect(screen.getByText("ثبت وزن")).toBeTruthy());

    const input = screen.getByLabelText(/وزن امروز/);
    await user.type(input, "78.4");
    await user.click(screen.getByRole("button", { name: "ثبت وزن" }));

    await waitFor(() => expect(screen.getByText("۱ وزن ثبت شد")).toBeTruthy());

    const posted = fetchMock.mock.calls.find((c) => String(c[0]).includes("/weight-logs"));
    expect(posted).toBeTruthy();
    const body = JSON.parse((posted![1] as RequestInit).body as string);
    expect(body.member_id).toBe(7);
    expect(body.entries[0].weight_kg).toBe(78.4);
    expect(body.entries[0].logged_for_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("blocks an impossible weight before it reaches the server", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = mockFetch(payload());
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<AdaptiveNutritionPanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("ثبت وزن")).toBeTruthy());

    await user.type(screen.getByLabelText(/وزن امروز/), "900");
    await user.click(screen.getByRole("button", { name: "ثبت وزن" }));

    await waitFor(() => expect(screen.getByText(/بین ۲۰ و ۴۰۰/)).toBeTruthy());
    const posted = fetchMock.mock.calls.find((c) => String(c[0]).includes("/weight-logs"));
    expect(posted).toBeUndefined();
  });
});
