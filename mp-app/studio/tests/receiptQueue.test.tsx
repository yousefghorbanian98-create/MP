/**
 * صف بازبینی فیش — فاز ۶ (QF-08/QF-09).
 *
 * با `fetch` واقعیِ stub‌شده: مسیر، متد و بدنهٔ درخواست‌ها سنجیده می‌شوند تا
 * ادعای «تأیید/رد سرورمحور است» قابل بازرسی باشد.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ReceiptQueue } from "../src/components/ReceiptQueue";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

interface Call {
  method: string;
  path: string;
  body: string | null;
}

const ROW = {
  id: 42,
  member_id: 7,
  amount_rial: 2_500_000,
  method: "card_to_card",
  status: "in_review",
  reference_id: "",
  description: "",
  paid_at: null,
};

function stubApi(state: { rows: unknown[]; approveStatus?: number }) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const method = (init?.method ?? "GET").toUpperCase();
      calls.push({
        method,
        path: `${url.pathname}${url.search}`,
        body: typeof init?.body === "string" ? init.body : null,
      });
      if (url.pathname === "/api/v1/payments" && method === "GET") return reply(200, state.rows);
      if (url.pathname.endsWith("/approve") && method === "POST") {
        if (state.approveStatus === 403) {
          return reply(403, {
            error: { message: "تأیید پرداختی که خودتان ثبت کرده‌اید مجاز نیست" },
          });
        }
        state.rows = [];
        return reply(200, { id: 42, status: "paid", membership_id: 9 });
      }
      if (url.pathname.endsWith("/reject") && method === "POST") {
        state.rows = [];
        return reply(200, { payment_id: 42, status: "failed", review_id: "r-1" });
      }
      throw new Error(`Unexpected request: ${method} ${url.pathname}`);
    }),
  );
  return calls;
}

// jsdom این API را ندارد و antd (Table/Modal) هنگام mount صدایش می‌زند.
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
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("صف بازبینی فیش", () => {
  it("فهرست را از ?status=in_review می‌خواند و مبلغ را نشان می‌دهد", async () => {
    const calls = stubApi({ rows: [ROW] });
    render(<ReceiptQueue />);

    expect(await screen.findByText("۲٬۵۰۰٬۰۰۰ ریال")).toBeTruthy();
    expect(calls[0]).toMatchObject({ method: "GET", path: "/api/v1/payments?status=in_review" });
  });

  it("تأیید را به POST /payments/{id}/approve می‌فرستد و صف را بازخوانی می‌کند", async () => {
    const calls = stubApi({ rows: [ROW] });
    render(<ReceiptQueue />);

    fireEvent.click(await screen.findByRole("button", { name: "تأیید" }));
    fireEvent.click(await screen.findByRole("button", { name: "تأیید کن" }));

    await waitFor(() => expect(screen.getByText("فیشی در انتظار بازبینی نیست")).toBeTruthy());
    expect(calls.some((c) => c.method === "POST" && c.path === "/api/v1/payments/42/approve")).toBe(true);
    expect(calls.filter((c) => c.path === "/api/v1/payments?status=in_review").length).toBeGreaterThanOrEqual(2);
  });

  it("خطای سرور (تأیید پرداخت خود) را نشان می‌دهد و ردیف را خوش‌بینانه حذف نمی‌کند", async () => {
    stubApi({ rows: [ROW], approveStatus: 403 });
    render(<ReceiptQueue />);

    fireEvent.click(await screen.findByRole("button", { name: "تأیید" }));
    fireEvent.click(await screen.findByRole("button", { name: "تأیید کن" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("تأیید پرداختی که خودتان ثبت کرده‌اید مجاز نیست");
    expect(screen.getByText("۲٬۵۰۰٬۰۰۰ ریال")).toBeTruthy();
  });

  it("رد فیش دلیل می‌خواهد و آن را در بدنه می‌فرستد", async () => {
    const calls = stubApi({ rows: [ROW] });
    render(<ReceiptQueue />);

    fireEvent.click(await screen.findByRole("button", { name: "رد" }));
    const reason = await screen.findByLabelText("دلیل رد فیش");
    fireEvent.change(reason, { target: { value: "مبلغ واریزی نمی‌خواند" } });
    fireEvent.click(screen.getByRole("button", { name: "ثبت رد" }));

    await waitFor(() =>
      expect(calls.some((c) => c.method === "POST" && c.path === "/api/v1/payments/42/reject")).toBe(true),
    );
    const post = calls.find((c) => c.path.endsWith("/reject"))!;
    expect(JSON.parse(post.body!)).toEqual({ reason: "مبلغ واریزی نمی‌خواند" });
  });
});
