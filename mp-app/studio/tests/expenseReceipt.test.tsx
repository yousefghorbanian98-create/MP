import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Expenses } from "../src/pages/Expenses";

/**
 * QF-06 — فیش خصوصی هزینه در صفحهٔ هزینه‌ها.
 *
 * قفل می‌کند:
 * - آپلود فیش با هدر نشست و به مسیر همان هزینه می‌رود (multipart، نه JSON).
 * - خطای ۴۰۳ آپلود به‌عنوان «نداشتن مجوز» نمایش داده می‌شود، نه موفقیت خاموش.
 * - مشاهدهٔ فیشِ نباشته پیام صریح می‌دهد.
 */

type Call = { url: string; method: string; auth: string | null; isForm: boolean };

const expenseRow = {
  id: 7,
  amount_rial: 12_000_000,
  category: "rent",
  spent_on: "2026-03-15",
  payee: "مالک ساختمان",
  note: "اجارهٔ فروردین",
  created_at: "2026-03-15T08:00:00Z",
  deleted_at: null,
};

const periodBody = {
  from_date: "2026-02-01",
  to_date: "2026-03-20",
  count: 1,
  total_rial: 12_000_000,
  by_category: [{ category: "rent", total_rial: 12_000_000, count: 1 }],
  items: [expenseRow],
};

let calls: Call[] = [];

function stub(overrides: { post?: { status: number; body: unknown }; get?: { status: number } }) {
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
        isForm: init?.body instanceof FormData,
      });
      if (method === "POST" && url.includes("/expenses/7/receipt")) {
        const o = overrides.post ?? { status: 201, body: { expense_id: 7, mime: "image/png", size_bytes: 8 } };
        return new Response(JSON.stringify(o.body), { status: o.status });
      }
      if (method === "GET" && url.includes("/expenses/7/receipt")) {
        const status = overrides.get?.status ?? 404;
        return new Response(JSON.stringify({ error: { message: "x" } }), { status });
      }
      if (method === "GET" && /\/expenses\?from=/.test(url)) {
        return new Response(JSON.stringify(periodBody), { status: 200 });
      }
      throw new Error(`unexpected ${method} ${url}`);
    }),
  );
}

beforeEach(() => {
  calls = [];
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

describe("Expenses receipt (QF-06)", () => {
  it("uploads the picked image to the expense with the session token as multipart", async () => {
    stub({});
    const { container } = render(<Expenses />);
    await waitFor(() => expect(screen.getByText("مالک ساختمان")).toBeTruthy(), { timeout: 20000 });

    fireEvent.click(screen.getByRole("button", { name: "فیش" }));
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([new Uint8Array([137, 80, 78, 71])], "fish.png", { type: "image/png" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(
      () => expect(calls.some((c) => c.method === "POST" && c.url.includes("/expenses/7/receipt"))).toBe(true),
      { timeout: 20000 },
    );
    const post = calls.find((c) => c.method === "POST");
    expect(post?.auth).toBe("Bearer tok-123");
    expect(post?.isForm).toBe(true);
  }, 30000);

  it("shows a forbidden message when the upload is refused with 403", async () => {
    stub({ post: { status: 403, body: { error: { message: "دسترسی لازم نیست" } } } });
    const { container } = render(<Expenses />);
    await waitFor(() => expect(screen.getByText("مالک ساختمان")).toBeTruthy(), { timeout: 20000 });

    fireEvent.click(screen.getByRole("button", { name: "فیش" }));
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, {
      target: { files: [new File([new Uint8Array([1])], "x.png", { type: "image/png" })] },
    });

    await waitFor(() => expect(screen.getByText(/دسترسی لازم نیست/)).toBeTruthy(), { timeout: 20000 });
  }, 30000);

  it("explains that a missing receipt is missing, not silently empty", async () => {
    stub({ get: { status: 404 } });
    render(<Expenses />);
    await waitFor(() => expect(screen.getByText("مالک ساختمان")).toBeTruthy(), { timeout: 20000 });

    fireEvent.click(screen.getByRole("button", { name: "مشاهدهٔ فیش" }));
    await waitFor(() => expect(screen.getByText(/این هزینه فیش ندارد/)).toBeTruthy(), { timeout: 20000 });
  }, 30000);
});
