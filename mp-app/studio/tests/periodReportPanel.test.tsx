import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { PeriodReportPanel } from "../src/components/PeriodReportPanel";

/**
 * QF-10 — پنل گزارش سود/زیان دوره‌ای.
 *
 * قفل می‌کند:
 * - درخواست با نوع دوره و تاریخ میلادی به سرور می‌رود و هدر نشست دارد.
 * - بازگشت بدون تاریخ → هشدار «قطعی نیست»؛ سود صفر به‌جای آن نشان داده نمی‌شود.
 * - خطای سرور به‌جای عدد صفر نمایش داده می‌شود.
 */

const base = {
  kind: "month",
  label: "1405/08",
  timezone: "Asia/Tehran",
  start: "2026-10-23",
  end_exclusive: "2026-11-22",
  start_jalali: "1405/08/01",
  received_rial: 300,
  received_count: 3,
  refunds_rial: 100,
  refunds_count: 1,
  net_income_rial: 200,
  expenses_rial: 50,
  expenses_count: 1,
  profit_rial: 150,
  undated_refunds_count: 0,
  complete: true,
};

let urls: string[] = [];
let auth: (string | null)[] = [];

function stub(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      urls.push(typeof input === "string" ? input : input.toString());
      const h = (init?.headers ?? {}) as Record<string, string>;
      auth.push(h.Authorization ?? null);
      return new Response(JSON.stringify(body), { status });
    }),
  );
}

beforeEach(() => {
  urls = [];
  auth = [];
  localStorage.setItem("mp_token", "tok-123");
  window.matchMedia ??= ((q: string) => ({
    matches: false,
    media: q,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
});

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe("PeriodReportPanel (QF-10)", () => {
  it("requests the month report with a session token and shows the profit", async () => {
    stub(base);
    render(<PeriodReportPanel />);
    await waitFor(() => expect(screen.getByText(/سود خالص/)).toBeTruthy(), { timeout: 20000 });
    expect(urls[0]).toMatch(/\/finance\/reports\/period\?kind=month&anchor=\d{4}-\d{2}-\d{2}/);
    expect(auth[0]).toBe("Bearer tok-123");
    expect(screen.getByText(/۱۵۰/)).toBeTruthy();
  }, 30000);

  it("marks profit unknown and omits its value and bar when a refund has no date", async () => {
    stub({ ...base, undated_refunds_count: 2, complete: false });
    render(<PeriodReportPanel />);
    await waitFor(() => expect(screen.getByText(/سود این دوره قطعی نیست/)).toBeTruthy(), {
      timeout: 20000,
    });
    expect(screen.getByText("نامعلوم")).toBeTruthy();
    expect(screen.queryByText(/۱۵۰ ریال/)).toBeNull();
    expect(screen.getByRole("img", { name: /سود نامعلوم/ })).toBeTruthy();
  }, 30000);

  it("shows the server error and does not display zero profit", async () => {
    stub({ error: { code: "permission_required", message: "دسترسی لازم نیست" } }, 403);
    render(<PeriodReportPanel />);
    await waitFor(() => expect(screen.getByText(/اجازهٔ این کار را ندارد|دسترسی/)).toBeTruthy(), {
      timeout: 20000,
    });
    expect(screen.queryByText(/سود خالص/)).toBeNull();
  }, 30000);
});
