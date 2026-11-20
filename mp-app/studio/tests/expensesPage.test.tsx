import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Expenses } from "../src/pages/Expenses";

/**
 * QF-06 — صفحهٔ هزینه‌های باشگاه.
 *
 * چه چیزی را قفل می‌کند:
 * - جمع دوره از سرور می‌آید (نه از حافظهٔ UI) و با هدر نشست درخواست می‌شود.
 * - اصلاح و حذف **بدون دلیل** به سرور نمی‌روند؛ سرور هم جداگانه ۴۲۲ می‌دهد.
 * - مبلغ نامعتبر (زیر ۱٬۰۰۰ ریال) درخواست نمی‌سازد.
 * - ۴۰۳ به‌عنوان «نداشتن مجوز» نمایش داده می‌شود، نه موفقیت خاموش.
 */

type Call = { url: string; method: string; auth: string | null; body: unknown };

type Route = {
  match: RegExp;
  body: unknown;
  status?: number;
};

function stub(routes: Route[]) {
  const calls: Call[] = [];
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
      const hit = routes.find((r) => r.match.test(`${method} ${url}`));
      if (!hit) throw new Error(`unexpected ${method} ${url}`);
      return new Response(JSON.stringify(hit.body), { status: hit.status ?? 200 });
    }),
  );
  return calls;
}

const row = (over: Partial<Record<string, unknown>> = {}) => ({
  id: 1,
  amount_rial: 12_000_000,
  category: "rent",
  spent_on: "2026-03-15",
  payee: "مالک ساختمان",
  note: "اجارهٔ فروردین",
  created_at: "2026-03-15T08:00:00Z",
  deleted_at: null,
  ...over,
});

const period = (items: ReturnType<typeof row>[], total: number) => ({
  from_date: "2026-02-01",
  to_date: "2026-03-20",
  count: items.length,
  total_rial: total,
  by_category: [{ category: "rent", label: "اجاره", total_rial: total, count: items.length }],
  items,
});

// jsdom این API را ندارد و antd (Table/Modal/Select) هنگام mount صدایش می‌زند.
if (typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) =>
      ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as unknown as MediaQueryList,
  });
}

beforeEach(() => {
  localStorage.setItem("mp_token", "tok-123");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("Expenses (QF-06)", () => {
  it("loads the period total on mount with the auth header", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([row()], 12_000_000) },
    ]);
    render(<Expenses />);

    await waitFor(() => expect(screen.getByText(/جمع هزینهٔ دوره/)).toBeTruthy());
    expect(screen.getAllByText(/۱۲٬۰۰۰٬۰۰۰/).length).toBeGreaterThan(0);
    expect(calls[0].auth).toBe("Bearer tok-123");
    expect(calls[0].url).toContain("from=");
    expect(calls[0].url).toContain("to=");
  }, 20000);

  it("posts a new expense with the auth header and reloads the period", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([], 0) },
      { match: /POST .*\/expenses/, body: row() },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));

    fireEvent.change(screen.getByLabelText("مبلغ هزینه"), { target: { value: "12000000" } });
    fireEvent.change(screen.getByLabelText("طرف‌حساب"), { target: { value: "مالک ساختمان" } });
    fireEvent.click(screen.getByRole("button", { name: "ثبت هزینه" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const post = calls.find((c) => c.method === "POST");
    expect(post?.auth).toBe("Bearer tok-123");
    expect(post?.body).toMatchObject({
      amount_rial: 12_000_000,
      category: "rent",
      payee: "مالک ساختمان",
    });
    await waitFor(() =>
      expect(calls.filter((c) => c.method === "GET" && c.url.includes("/expenses?")).length).toBeGreaterThan(
        1,
      ),
    );
  }, 30000);

  it("refuses an amount below 1,000 rial without calling the API", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([], 0) },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(calls.length).toBeGreaterThan(0));

    fireEvent.change(screen.getByLabelText("مبلغ هزینه"), { target: { value: "500" } });
    fireEvent.click(screen.getByRole("button", { name: "ثبت هزینه" }));

    await waitFor(() => expect(screen.getByText(/حداقل ۱٬۰۰۰ ریال/)).toBeTruthy());
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  }, 20000);

  it("requires a reason before sending an edit", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([row()], 12_000_000) },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(screen.getAllByText(/اجاره/).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: "اصلاح" }));
    fireEvent.change(screen.getByLabelText("مبلغ اصلاح‌شده"), { target: { value: "13000000" } });
    fireEvent.click(screen.getByRole("button", { name: "ثبت اصلاح" }));

    await waitFor(() => expect(screen.getByText(/دلیل اصلاح اجباری است/)).toBeTruthy());
    expect(calls.some((c) => c.method === "PATCH")).toBe(false);
  }, 20000);

  it("sends the edit with amount and reason, then reloads", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([row()], 12_000_000) },
      { match: /PATCH .*\/expenses\/1/, body: row({ amount_rial: 13_000_000 }) },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(screen.getAllByText(/اجاره/).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: "اصلاح" }));
    fireEvent.change(screen.getByLabelText("مبلغ اصلاح‌شده"), { target: { value: "13000000" } });
    fireEvent.change(screen.getByLabelText("دلیل اصلاح"), {
      target: { value: "افزایش اجارهٔ امسال" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ثبت اصلاح" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
    const patch = calls.find((c) => c.method === "PATCH");
    expect(patch?.auth).toBe("Bearer tok-123");
    expect(patch?.body).toEqual({ amount_rial: 13_000_000, reason: "افزایش اجارهٔ امسال" });
    await waitFor(() =>
      expect(calls.filter((c) => c.method === "GET" && c.url.includes("/expenses?")).length).toBeGreaterThan(
        1,
      ),
    );
  }, 30000);

  it("sends a soft delete with the prompted reason", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([row()], 12_000_000) },
      { match: /DELETE .*\/expenses\/1/, body: row({ deleted_at: "2026-03-16T10:00:00Z" }) },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(screen.getAllByText(/اجاره/).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: "حذف" }));
    fireEvent.change(screen.getByLabelText("دلیل حذف"), { target: { value: "دوبار ثبت شده بود" } });
    fireEvent.click(screen.getByRole("button", { name: "حذف کن" }));

    await waitFor(() => expect(calls.some((c) => c.method === "DELETE")).toBe(true));
    const del = calls.find((c) => c.method === "DELETE");
    expect(del?.body).toEqual({ reason: "دوبار ثبت شده بود" });
  }, 20000);

  it("does not delete when the reason prompt is cancelled", async () => {
    const calls = stub([
      { match: /GET .*\/expenses\?/, body: period([row()], 12_000_000) },
    ]);
    render(<Expenses />);
    await waitFor(() => expect(screen.getAllByText(/اجاره/).length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: "حذف" }));
    fireEvent.click(screen.getByRole("button", { name: "حذف کن" }));

    await waitFor(() => expect(screen.getByText(/دلیل حداقل ۳ نویسه لازم است/)).toBeTruthy());
    expect(calls.some((c) => c.method === "DELETE")).toBe(false);
  }, 20000);

  it("surfaces a 403 as a permission error, not a silent success", async () => {
    stub([
      {
        match: /GET .*\/expenses\?/,
        body: { error: { message: "نقش شما برای این مسیر مجاز نیست" } },
        status: 403,
      },
    ]);
    render(<Expenses />);

    await waitFor(() => expect(screen.getByText(/مجاز نیست/)).toBeTruthy());
  }, 20000);
});
