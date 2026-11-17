import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AutoregPanel } from "../src/components/AutoregPanel";

/**
 * autoreg-1.0 — پنل وزنهٔ ست بعدی.
 *
 * باگ «کد بی‌مصرف»: `POST /ai/suggest-weight` هیچ مصرف‌کننده‌ای نداشت.
 * این تست‌ها ثابت می‌کنند پنل واقعاً درخواست می‌فرستد، عددِ **سرور** را
 * نشان می‌دهد (نه محاسبهٔ محلی)، و ورودی نامعتبر را قبل از رفت‌وبرگشت
 * رد می‌کند.
 */

const suggestion = {
  next_weight: 55,
  action: "decrease",
  reason: "تکرار 8/10 یا RPE=None ← محافظه‌کاری",
  rule_version: "autoreg-1.0",
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("AutoregPanel", () => {
  it("پاسخ سرور را با دلیل و نسخهٔ قاعده نشان می‌دهد", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify(suggestion), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<AutoregPanel />);

    await user.click(screen.getByRole("button", { name: "محاسبه" }));

    await waitFor(() => expect(screen.getByText("۵۵")).toBeTruthy());
    expect(screen.getByText("(کاهش)")).toBeTruthy();
    expect(screen.getByText(/محافظه‌کاری/)).toBeTruthy();
    expect(screen.getByText(/autoreg-1.0/)).toBeTruthy();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/ai/suggest-weight");
    expect(JSON.parse(String(init.body))).toMatchObject({
      last_weight: 60,
      reps_done: 8,
      target_reps: 10,
      rpe: null,
    });
  });

  it("ورودی نامعتبر را قبل از ارسال رد می‌کند", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<AutoregPanel />);

    const weight = screen.getByLabelText(/وزنهٔ ست قبل/);
    await user.clear(weight);
    await user.type(weight, "0");
    await user.click(screen.getByRole("button", { name: "محاسبه" }));

    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("بزرگ‌تر از صفر"),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("RPE بیرون از ۱..۱۰ رد می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<AutoregPanel />);

    await user.type(screen.getByLabelText(/RPE/), "11");
    await user.click(screen.getByRole("button", { name: "محاسبه" }));
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("بین ۱ و ۱۰"),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("خطای شبکه را نشان می‌دهد، نه سکوت", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("down");
      }),
    );
    const user = userEvent.setup();
    render(<AutoregPanel />);
    await user.click(screen.getByRole("button", { name: "محاسبه" }));
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  });
});
