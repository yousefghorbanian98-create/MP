import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PaymentPanel } from "../src/components/PaymentPanel";

/**
 * Q6 — پنل پرداخت.
 *
 * باگ «کد بی‌مصرف»: کل اداپتور درگاه (Mock + زرین‌پال + HMAC) بدون هیچ
 * مصرف‌کننده‌ای در مخزن بود. این تست‌ها جریان واقعی سه‌مرحله‌ای را
 * می‌سنجند: ساخت → start (authority) → callback با امضا.
 */

const created = {
  id: 7,
  member_id: 41,
  amount_rial: 500000,
  method: "zarinpal",
  status: "pending",
  reference_id: "",
  description: "",
  paid_at: null,
};

const started = {
  payment_id: 7,
  authority: "MOCK-abc123def456",
  redirect_url: "mock://gateway/pay/MOCK-abc123def456",
  amount_rial: 500000,
  callback_token: "a".repeat(32),
};

const paid = { ...created, status: "paid", reference_id: "MOCKREF-abc123def456" };

function router(seen: string[]) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    seen.push(`${init?.method ?? "GET"} ${url}`);
    if (url.endsWith("/payments")) return new Response(JSON.stringify(created), { status: 200 });
    if (url.endsWith("/start")) return new Response(JSON.stringify(started), { status: 200 });
    if (url.endsWith("/callback")) return new Response(JSON.stringify(paid), { status: 200 });
    return new Response("{}", { status: 200 });
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("PaymentPanel (Q6)", () => {
  it("جریان کامل: ساخت → start → callback با authority و امضا", async () => {
    localStorage.setItem("mp_token", "t");
    const seen: string[] = [];
    vi.stubGlobal("fetch", router(seen));
    const user = userEvent.setup();
    render(<PaymentPanel />);

    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));

    await waitFor(() => expect(screen.getByText(/تراکنش #7/)).toBeTruthy());
    expect(screen.getByText("۵۰۰٬۰۰۰")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "آغاز پرداخت در درگاه" }));
    await waitFor(() => expect(screen.getByText(/MOCK-abc123def456/)).toBeTruthy());
    const link = screen.getByRole("link", { name: /رفتن به صفحهٔ درگاه/ });
    expect(link.getAttribute("href")).toBe("mock://gateway/pay/MOCK-abc123def456");

    await user.click(screen.getByRole("button", { name: /تأیید/ }));
    await waitFor(() => expect(screen.getByText(/وضعیت:/)).toBeTruthy());
    expect(screen.getByText("paid")).toBeTruthy();
    expect(screen.getByText(/MOCKREF-abc123def456/)).toBeTruthy();

    expect(seen).toEqual([
      "POST /api/v1/payments",
      "POST /api/v1/payments/7/start",
      "POST /api/v1/payments/7/callback",
    ]);
  });

  it("تأیید بدون start رد می‌شود — دکمهٔ تشریفاتی نیست", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", router([]));
    const user = userEvent.setup();
    render(<PaymentPanel />);

    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));
    await waitFor(() => expect(screen.getByText(/تراکنش #7/)).toBeTruthy());

    // دکمهٔ تأیید اصلاً رندر نمی‌شود تا start انجام شود
    expect(screen.queryByRole("button", { name: /بازگشت از درگاه/ })).toBeNull();
  });

  it("مبلغ کمتر از حد مجاز قبل از ارسال رد می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = router([]);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<PaymentPanel />);

    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    const amount = screen.getByLabelText("مبلغ (ریال)");
    await user.clear(amount);
    await user.type(amount, "100");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));

    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      expect.stringContaining("حداقل ۱۰۰۰ ریال"),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("خطای درگاه (امضای نامعتبر) به کاربر نشان داده می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/payments")) return new Response(JSON.stringify(created), { status: 200 });
        if (url.endsWith("/start")) return new Response(JSON.stringify(started), { status: 200 });
        return new Response(
          JSON.stringify({
            error: { code: "bad_signature", message: "امضای callback نامعتبر است", details: [] },
          }),
          { status: 400 },
        );
      }),
    );
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));
    await user.click(await screen.findByRole("button", { name: "آغاز پرداخت در درگاه" }));
    await user.click(await screen.findByRole("button", { name: /تأیید/ }));

    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain("امضای callback نامعتبر است"),
    );
    // وضعیت تراکنش عوض نشده
    expect(screen.getByText("pending")).toBeTruthy();
  });
});

describe("PaymentPanel — شکست و رسید", () => {
  it("ثبت شکست تراکنش وضعیت را failed می‌کند", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/payments")) return new Response(JSON.stringify(created), { status: 200 });
        if (url.endsWith("/fail"))
          return new Response(JSON.stringify({ ...created, status: "failed" }), { status: 200 });
        return new Response("{}", { status: 200 });
      }),
    );
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));
    await user.click(await screen.findByRole("button", { name: "ثبت شکست تراکنش" }));
    await waitFor(() => expect(screen.getByText("failed")).toBeTruthy());
  });

  it("رسید پرداخت‌شده از سرور خوانده می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    const receipt = {
      payment_id: 7,
      member_id: 41,
      amount_rial: 500000,
      paid_at: "2026-11-15T10:00:00Z",
      reference_id: "MOCKREF-abc",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/payments")) return new Response(JSON.stringify(created), { status: 200 });
        if (url.endsWith("/start")) return new Response(JSON.stringify(started), { status: 200 });
        if (url.endsWith("/callback")) return new Response(JSON.stringify(paid), { status: 200 });
        if (url.endsWith("/receipt")) return new Response(JSON.stringify(receipt), { status: 200 });
        return new Response("{}", { status: 200 });
      }),
    );
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ عضو"), "41");
    await user.click(screen.getByRole("button", { name: "ساخت تراکنش" }));
    await user.click(await screen.findByRole("button", { name: "آغاز پرداخت در درگاه" }));
    await user.click(await screen.findByRole("button", { name: /تأیید/ }));
    await user.click(await screen.findByRole("button", { name: "نمایش رسید" }));
    await waitFor(() => expect(screen.getByText(/رسید پرداخت #7/)).toBeTruthy());
  });
});

describe("PaymentPanel — refund", () => {
  it("loads an existing payment, confirms refund and displays its server receipt", async () => {
    localStorage.setItem("mp_token", "t");
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const paidGateway = { ...paid, gateway_authority: "AUTH-1" };
    const refunded = { ...paidGateway, status: "refunded", refund_reference: "REFUND-1" };
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/payments")) return new Response(JSON.stringify([paidGateway]));
      if (url.endsWith("/refund")) return new Response(JSON.stringify(refunded));
      if (url.endsWith("/receipt")) return new Response(JSON.stringify({
        payment_id: 7, member_id: 41, amount_rial: 500000,
        paid_at: null, reference_id: paid.reference_id, status: "refunded", refund_reference: "REFUND-1",
      }));
      return new Response("{}", { status: 404 });
    }));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ پرداخت موجود"), "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    await user.click(await screen.findByRole("button", { name: "بازگشت وجه" }));
    expect(await screen.findByText("refunded")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "نمایش رسید" }));
    expect(await screen.findByText(/رسید بازگشت وجه #7/)).toBeTruthy();
    expect(screen.getByText(/مرجع بازگشت: REFUND-1/)).toBeTruthy();
  });
});

describe("PaymentPanel — fail-closed payment lookup", () => {
  const gatewayPaid = { ...paid, gateway_authority: "AUTH-1" };

  it("clears the selection immediately when the lookup id changes", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify([gatewayPaid]))));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    const input = screen.getByLabelText("شناسهٔ پرداخت موجود");
    await user.type(input, "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
    await user.clear(input);
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
    expect(screen.queryByText(/تراکنش #7/)).toBeNull();
    await user.type(input, "999");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByText("پرداخت یافت نشد")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
    await user.clear(input);
    await user.type(input, "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
  });

  it("invalid ids cannot retain or request a previous payment", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify([gatewayPaid])));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<PaymentPanel />);
    const input = screen.getByLabelText("شناسهٔ پرداخت موجود");
    await user.type(input, "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
    await user.clear(input);
    await user.type(input, "0");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByText("شناسهٔ پرداخت نامعتبر است")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("a failed repeated lookup clears the old payment and receipt", async () => {
    let failLookup = false;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/receipt")) return new Response(JSON.stringify({
        payment_id: 7, member_id: 41, amount_rial: 500000,
        paid_at: null, reference_id: "ref", status: "paid",
      }));
      if (failLookup) throw new Error("شبکه قطع است");
      return new Response(JSON.stringify([gatewayPaid]));
    }));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ پرداخت موجود"), "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    await user.click(await screen.findByRole("button", { name: "نمایش رسید" }));
    expect(await screen.findByText(/رسید پرداخت #7/)).toBeTruthy();
    failLookup = true;
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent", expect.stringContaining("اتصال به سرور برقرار نشد"),
    );
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
    expect(screen.queryByText(/رسید پرداخت #7/)).toBeNull();
  });

  it("clears the selection when a repeated lookup gets an HTTP error", async () => {
    let calls = 0;
    vi.stubGlobal("fetch", vi.fn(async () => {
      calls += 1;
      return calls === 1
        ? new Response(JSON.stringify([gatewayPaid]))
        : new Response(JSON.stringify({ error: { message: "خطای سرور" } }), { status: 500 });
    }));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    await user.type(screen.getByLabelText("شناسهٔ پرداخت موجود"), "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(await screen.findByText("خطای سرور")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "بازگشت وجه" })).toBeNull();
  });

  it("locks lookup input while a request is pending and selects only its result", async () => {
    let resolveFetch!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { resolveFetch = resolve; })));
    const user = userEvent.setup();
    render(<PaymentPanel />);
    const input = screen.getByLabelText("شناسهٔ پرداخت موجود") as HTMLInputElement;
    await user.type(input, "7");
    await user.click(screen.getByRole("button", { name: "بارگذاری پرداخت" }));
    expect(input.disabled).toBe(true);
    await user.type(input, "99");
    expect(input.value).toBe("7");
    resolveFetch(new Response(JSON.stringify([gatewayPaid])));
    expect(await screen.findByRole("button", { name: "بازگشت وجه" })).toBeTruthy();
    expect(input.disabled).toBe(false);
  });
});
