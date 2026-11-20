import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Finance } from "../src/pages/Finance";

/**
 * M52-c1 — رگرسیون صفحهٔ مالی.
 *
 * باگ اصلی: `fetch` خام بدون هدر Authorization ⇒ هر سه دکمه ۴۰۱ می‌گرفت.
 * این تست تضمین می‌کند هر درخواست مالی توکن را همراه ببرد، وگرنه صفحه
 * بی‌صدا مرده است و در دمو «کار می‌کند» به نظر می‌رسد.
 */

type Call = { url: string; method: string; auth: string | null; body: unknown };

/**
 * صفحهٔ مالی از QF-10 هم گزارش دوره‌ای را هنگام mount می‌گیرد. این مسیر در هر
 * stub باید پاسخ داشته باشد؛ وگرنه fetch ساختگی خطا می‌دهد و شمارش درخواست‌ها
 * به ترتیب زمان‌بندی (که در CI کندتر است) وابسته می‌شود.
 */
const periodRoute = {
  match: /GET .*\/finance\/reports\/period/,
  body: {
    kind: "month",
    label: "1405/08",
    timezone: "Asia/Tehran",
    start: "2026-10-23",
    end_exclusive: "2026-11-22",
    start_jalali: "1405/08/01",
    received_rial: 0,
    received_count: 0,
    refunds_rial: 0,
    refunds_count: 0,
    net_income_rial: 0,
    expenses_rial: 0,
    expenses_count: 0,
    profit_rial: 0,
    undated_refunds_count: 0,
    complete: true,
  },
};

const summaryCalls = (calls: Call[]) =>
  calls.filter((c) => /\/payments\/finance\/summary/.test(c.url)).length;

function stub(routes: { match: RegExp; body: unknown; status?: number }[]) {
  const calls: Call[] = [];
  const all = [...routes, periodRoute];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = (init?.method ?? "GET").toUpperCase();
      const headers = (init?.headers ?? {}) as Record<string, string>;
      calls.push({
        url,
        method,
        auth: headers.Authorization ?? headers.authorization ?? null,
        body: init?.body ? JSON.parse(String(init.body)) : null,
      });
      const hit = all.find((r) => r.match.test(`${method} ${url}`));
      if (!hit) throw new Error(`unexpected ${method} ${url}`);
      if (hit.body instanceof Blob) return new Response(hit.body, { status: hit.status ?? 200 });
      return new Response(JSON.stringify(hit.body), { status: hit.status ?? 200 });
    }),
  );
  return calls;
}

const summary = {
  total_paid_rial: 12_500_000,
  total_pending_rial: 2_000_000,
  paid_count: 5,
  generated_at: "2026-11-15T10:00:00Z",
};

const commission = {
  coach_id: 3,
  coach_name: "مربی احمدی",
  rate: 0.1,
  attributed_payments_rial: 8_000_000,
  commission_rial: 800_000,
};

beforeEach(() => {
  localStorage.setItem("mp_token", "tok-123");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("Finance (M52-c1)", () => {
  it("loads the summary on mount WITH the auth header", async () => {
    const calls = stub([{ match: /GET .*\/payments\/finance\/summary/, body: summary }]);
    render(<Finance />);

    await waitFor(() => expect(screen.getByText(/۱۲٬۵۰۰٬۰۰۰/)).toBeTruthy());
    expect(calls[0].auth).toBe("Bearer tok-123");
  });

  it("reloads the summary when the button is pressed", async () => {
    const calls = stub([{ match: /GET .*\/payments\/finance\/summary/, body: summary }]);
    render(<Finance />);
    await waitFor(() => expect(summaryCalls(calls)).toBeGreaterThan(0));

    const before = summaryCalls(calls);
    fireEvent.click(screen.getByRole("button", { name: "خلاصهٔ مالی" }));
    await waitFor(() => expect(summaryCalls(calls)).toBe(before + 1));
    const last = calls.filter((c) => /\/payments\/finance\/summary/.test(c.url)).at(-1);
    expect(last?.auth).toBe("Bearer tok-123");
  });

  it("computes commission with the token and shows the result", async () => {
    const calls = stub([
      { match: /GET .*\/payments\/finance\/summary/, body: summary },
      { match: /POST .*\/payments\/finance\/commission/, body: commission },
    ]);
    render(<Finance />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));

    fireEvent.change(screen.getByPlaceholderText("شناسهٔ مربی"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: /محاسبه/ }));

    await waitFor(() => expect(screen.getByText(/۸۰۰٬۰۰۰/)).toBeTruthy());
    const post = calls.find((c) => c.method === "POST");
    expect(post?.auth).toBe("Bearer tok-123");
    expect(post?.body).toEqual({ coach_id: 3, rate: 0.1 });
  });

  it("rejects a non-numeric coach id without calling the API", async () => {
    const calls = stub([{ match: /GET .*\/payments\/finance\/summary/, body: summary }]);
    render(<Finance />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));

    fireEvent.change(screen.getByPlaceholderText("شناسهٔ مربی"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: /محاسبه/ }));

    await waitFor(() => expect(screen.getByText(/عدد مثبت/)).toBeTruthy());
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  });

  it("downloads the CSV with the auth header", async () => {
    const calls = stub([
      { match: /GET .*\/payments\/finance\/summary/, body: summary },
      { match: /GET .*\/payments\/finance\/export\.csv/, body: new Blob(["a,b\n1,2"], { type: "text/csv" }) },
    ]);
    const clickSpy = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(clickSpy);
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: vi.fn(() => "blob:x"),
      revokeObjectURL: vi.fn(),
    });

    render(<Finance />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: /CSV/ }));

    await waitFor(() => expect(calls.some((c) => c.url.includes("export.csv"))).toBe(true));
    const csv = calls.find((c) => c.url.includes("export.csv"));
    expect(csv?.auth).toBe("Bearer tok-123");
    expect(clickSpy).toHaveBeenCalled();
  });

  it("shows an OTP re-login error instead of a silent empty table on 401", async () => {
    stub([
      {
        match: /GET .*\/payments\/finance\/summary/,
        body: { error: { message: "unauthorized" } },
        status: 401,
      },
    ]);
    render(<Finance />);

    await waitFor(() => expect(screen.getByText(/با کد یک‌بارمصرف دوباره وارد شوید/)).toBeTruthy());
  });

  it("sends no Authorization header when there is no token", async () => {
    localStorage.clear();
    const calls = stub([
      { match: /GET .*\/payments\/finance\/summary/, body: summary, status: 401 },
    ]);
    render(<Finance />);

    await waitFor(() => expect(summaryCalls(calls)).toBeGreaterThan(0));
    expect(calls.find((c) => /summary/.test(c.url))?.auth).toBeNull();
    await waitFor(() => expect(screen.getByText(/با کد یک‌بارمصرف دوباره وارد شوید/)).toBeTruthy());
  });
});
