/**
 * MEM-12 / PWA-3B — پرداخت کارت‌به‌کارت و ارسال فیش (سمت عضو).
 *
 * قفل‌ها (هر کدام یک تست):
 * - فهرست از `GET /payments` می‌آید و کلاینت `member_id` نمی‌فرستد (دامنهٔ سرور).
 * - ورودی فیش فقط برای ردیف `card_to_card` با وضعیت `pending` باز است.
 * - نوع/حجم پیش از ارسال و **همچنین** در سرور سنجیده می‌شود؛ خطای سرور با کدش نمایش داده می‌شود.
 * - پاسخ 202 ⇒ «در صف بازبینی»، هرگز «پرداخت شد» یا «اشتراک فعال شد».
 * - هیچ مسیر تأیید/رد/verify/wallet/start/refund صدا زده نمی‌شود.
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberPayments } from "../src/components/MemberPayments";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const payment = (overrides: Record<string, unknown> = {}) => ({
  id: 9,
  member_id: 17,
  amount_rial: 3500000,
  method: "card_to_card",
  status: "pending",
  reference_id: "",
  refund_reference: null,
  gateway_authority: "",
  description: "شهریهٔ آذر",
  paid_at: "2026-11-26T09:30:00Z",
  ...overrides,
});

type Call = { method: string; path: string; search: string };

function installApi(handler: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const call = { method: (init?.method ?? "GET").toUpperCase(), path: url.pathname, search: url.search };
      calls.push(call);
      return handler(call);
    }),
  );
  return calls;
}

/** فایل ساختگی با حجم دقیق: حجم `File` از محتوا می‌آید، پس بایت واقعی می‌سازیم. */
function file(name: string, type: string, bytes: number): File {
  return new File([new Uint8Array(bytes)], name, { type });
}

function uploadTo(container: HTMLElement, value: File) {
  // فیلد فایل از `Upload` کتابخانه‌ای antd می‌آید (Q11)، پس input خام در src نیست.
  const input = container.querySelector('input[type="file"]');
  expect(input).toBeTruthy();
  fireEvent.change(input as HTMLInputElement, { target: { files: [value] } });
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("member payments (MEM-12)", () => {
  it("lists the member's own payments with the server amount, unit and source", async () => {
    const calls = installApi(({ path }) => {
      if (path === "/api/v1/payments") return reply(200, [payment()]);
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberPayments />);

    expect(await screen.findByText(/آپلود فیش ≠ تأیید بانک/)).toBeTruthy();
    expect(container.querySelector('[data-payment-id="9"]')).toBeTruthy();
    expect(screen.getByText(/۳٬۵۰۰٬۰۰۰ ریال/)).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/payments/)).toBeTruthy();
    // دامنه با سرور است: کلاینت شناسهٔ عضو را در query نمی‌گذارد.
    expect(calls).toEqual([expect.objectContaining({ method: "GET", path: "/api/v1/payments" })]);
    expect(calls[0].search).toBe("");
  });

  it("opens the receipt input only for a pending card-to-card row", async () => {
    installApi(({ path }) => {
      if (path !== "/api/v1/payments") throw new Error(`unexpected API path: ${path}`);
      return reply(200, [
        payment(),
        payment({ id: 10, status: "paid", paid_at: "2026-10-01T08:00:00Z" }),
        payment({ id: 11, method: "cash", status: "pending" }),
        payment({ id: 12, status: "in_review" }),
      ]);
    });

    const { container } = render(<MemberPayments />);
    await screen.findByText(/آپلود فیش ≠ تأیید بانک/);

    expect(container.querySelector('[data-payment-id="9"] [data-upload-enabled="yes"]')).toBeTruthy();
    for (const id of ["10", "11", "12"]) {
      expect(container.querySelector(`[data-payment-id="${id}"] [data-upload-enabled="yes"]`)).toBeNull();
      expect(container.querySelector(`[data-payment-id="${id}"] [data-upload-enabled="no"]`)).toBeTruthy();
    }
    expect(screen.getByText(/فقط پرداخت کارت‌به‌کارت فیش می‌پذیرد/)).toBeTruthy();
  });

  it("rejects a wrong type and an oversized file before any request leaves the client", async () => {
    const calls = installApi(({ path }) => {
      if (path !== "/api/v1/payments") throw new Error(`unexpected API path: ${path}`);
      return reply(200, [payment()]);
    });

    const { container } = render(<MemberPayments />);
    await screen.findByText(/آپلود فیش ≠ تأیید بانک/);

    uploadTo(container, file("receipt.pdf", "application/pdf", 2048));
    expect(await screen.findByText(/فقط تصویر JPEG\/PNG\/WebP پذیرفته می‌شود/)).toBeTruthy();

    uploadTo(container, file("receipt.jpg", "image/jpeg", 6 * 1024 * 1024));
    expect(await screen.findByText(/حجم فیش بیش از سقف ۵ مگابایت است/)).toBeTruthy();

    // هیچ درخواستی جز خواندن فهرست نرفت.
    expect(calls.every((call) => call.method === "GET")).toBe(true);
  });

  it("posts the receipt and reports the server's in_review state instead of claiming payment", async () => {
    const calls = installApi(({ path, method }) => {
      if (path === "/api/v1/payments" && method === "GET") return reply(200, [payment()]);
      if (path === "/api/v1/payments/9/receipt" && method === "POST")
        return reply(202, {
          receipt_id: 3,
          review_id: "rev_abc123",
          payment_id: 9,
          status: "in_review",
          expires_at: "2026-11-29T09:30:00Z",
          size_bytes: 4096,
          mime: "image/jpeg",
        });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberPayments />);
    await screen.findByText(/آپلود فیش ≠ تأیید بانک/);
    uploadTo(container, file("receipt.jpg", "image/jpeg", 4096));

    await waitFor(() => expect(container.querySelector('[data-receipt-status="in_review"]')).toBeTruthy());
    expect(container.querySelector("[data-review-id]")?.textContent).toBe("rev_abc123");
    // وضعیت ردیف از پاسخ سرور می‌آید و «paid» نمی‌شود.
    expect(container.querySelector('[data-payment-id="9"]')?.getAttribute("data-payment-status")).toBe(
      "in_review",
    );
    expect(screen.getByText(/آپلود فیش ≠ تأیید بانک، و اشتراک تا تأیید فرد مجاز فعال نمی‌شود/)).toBeTruthy();
    expect(screen.getByText(/در حال ارسال فیش به سرور…|آخرین ارسال/)).toBeTruthy();
    expect(calls.filter((call) => call.method === "POST")).toEqual([
      { method: "POST", path: "/api/v1/payments/9/receipt", search: "" },
    ]);
  });

  it("surfaces the server's error code when the upload is refused", async () => {
    installApi(({ path, method }) => {
      if (path === "/api/v1/payments" && method === "GET") return reply(200, [payment()]);
      if (path === "/api/v1/payments/9/receipt" && method === "POST")
        return reply(409, {
          error: { code: "already_processed", message: "این پرداخت قبلاً پردازش شده است" },
        });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberPayments />);
    await screen.findByText(/آپلود فیش ≠ تأیید بانک/);
    uploadTo(container, file("receipt.png", "image/png", 2048));

    expect(
      await screen.findByText(/این پرداخت قبلاً پردازش شده است؛ فیش تازه‌ای لازم نیست/),
    ).toBeTruthy();
    expect(container.querySelector("[data-receipt-status]")).toBeNull();
  });

  it("never calls an approval, rejection, verification, wallet or checkout path", async () => {
    const calls = installApi(({ path, method }) => {
      if (path === "/api/v1/payments" && method === "GET") return reply(200, [payment()]);
      if (path === "/api/v1/payments/9/receipt" && method === "POST")
        return reply(202, {
          receipt_id: 3,
          review_id: "rev_abc123",
          payment_id: 9,
          status: "in_review",
          expires_at: "2026-11-29T09:30:00Z",
          size_bytes: 4096,
          mime: "image/jpeg",
        });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberPayments />);
    await screen.findByText(/آپلود فیش ≠ تأیید بانک/);
    uploadTo(container, file("receipt.jpg", "image/jpeg", 4096));
    await waitFor(() => expect(container.querySelector('[data-receipt-status="in_review"]')).toBeTruthy());

    const forbidden = /approve|reject|verify|refund|wallet|checkout|cart|\/start|callback/;
    expect(calls.some((call) => forbidden.test(call.path))).toBe(false);
    // هیچ دکمه‌ای برای تأیید فیش در صفحهٔ عضو نیست.
    expect(screen.queryByRole("button", { name: /تأیید|رد/ })).toBeNull();
  });

  it("fails closed on 403 with no rows and no values", async () => {
    installApi(() => reply(403, { error: { code: "forbidden", message: "دسترسی ندارید" } }));

    const { container } = render(<MemberPayments />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/دسترسی به پرداخت‌های این عضو مجاز نیست/);
    expect(container.querySelectorAll("[data-payment-id]").length).toBe(0);
    expect(screen.queryByText(/۳٬۵۰۰٬۰۰۰ ریال/)).toBeNull();
  });
});
