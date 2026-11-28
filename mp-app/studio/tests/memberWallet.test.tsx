/**
 * MEM-11 / PWA-3A — کیف پول.
 *
 * قفل‌ها:
 * - موجودی از `balance_rial` سرور می‌آید، نه جمع ردیف‌ها (کلاینت محاسبه نمی‌کند).
 * - `reconcile.matches === false` ⇒ هشدار قرمز با اختلاف؛ پنهان نمی‌شود.
 * - مبلغ عدد صحیح ریال است و با «ریال» نمایش داده می‌شود؛ بدون اعشار/گرد کردن.
 * - صفحه‌بندی جعلی ساخته نمی‌شود (سرور offset ندارد).
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberWallet } from "../src/components/MemberWallet";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const entry = (overrides: Record<string, unknown> = {}) => ({
  id: 11,
  member_id: 17,
  amount_rial: 2500000,
  kind: "pay",
  source_type: "payment",
  source_id: 4,
  reverses_entry_id: null,
  reversed_by_entry_id: null,
  note: "",
  created_at: "2026-11-20T10:00:00Z",
  ...overrides,
});

const ledger = (overrides: Record<string, unknown> = {}) => ({
  member_id: 17,
  balance_rial: 12500000,
  reconcile: {
    member_id: 17,
    wallet_balance_rial: 12500000,
    ledger_balance_rial: 12500000,
    matches: true,
    difference_rial: 0,
  },
  entries: [entry()],
  ...overrides,
});

function installApi(handler: (path: string) => Response) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      calls.push(url.pathname);
      return handler(url.pathname);
    }),
  );
  return calls;
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

describe("member wallet (MEM-11)", () => {
  it("renders the server balance with its unit and source, without client-side summing", async () => {
    installApi((path) => {
      if (path === "/api/v1/payments/ledger/17") return reply(200, ledger());
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberWallet memberId={17} />);

    expect(await screen.findByText(/موجودی \(از سرور\)/)).toBeTruthy();
    expect(screen.getAllByText(/۱۲٬۵۰۰٬۰۰۰ ریال/).length).toBeGreaterThan(0);
    // عددِ موجودی همان مقدار سرور است، نه جمع ردیف‌ها (۲٬۵۰۰٬۰۰۰).
    expect(container.querySelector('[data-balance-rial="12500000"]')).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/payments\/ledger\/\{member_id\}/)).toBeTruthy();
  });

  it("shows each event with kind, source and reversal state", async () => {
    installApi((path) => {
      if (path === "/api/v1/payments/ledger/17")
        return reply(
          200,
          ledger({
            entries: [
              entry({ id: 12, kind: "reversal", amount_rial: -2500000, reverses_entry_id: 11 }),
              entry({ id: 11, reversed_by_entry_id: 12 }),
            ],
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberWallet memberId={17} />);

    expect(await screen.findByText(/معکوس‌سازی/)).toBeTruthy();
    expect(screen.getByText(/پرداخت/)).toBeTruthy();
    expect(screen.getByText(/این ردیف معکوس‌کنندهٔ #۱۱ است/)).toBeTruthy();
    expect(screen.getByText(/توسط #۱۲ معکوس شده/)).toBeTruthy();
    expect(container.querySelectorAll('[data-reversed="yes"]').length).toBe(1);
    expect(screen.getAllByText(/منبع: payment #۴/).length).toBeGreaterThan(0);
  });

  it("surfaces a wallet/ledger mismatch instead of hiding it", async () => {
    installApi((path) => {
      if (path === "/api/v1/payments/ledger/17")
        return reply(
          200,
          ledger({
            reconcile: {
              member_id: 17,
              wallet_balance_rial: 10000000,
              ledger_balance_rial: 12500000,
              matches: false,
              difference_rial: 2500000,
            },
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberWallet memberId={17} />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("کیف پول و دفتر مالی نمی‌خوانند");
    expect(alert.textContent).toContain("۲٬۵۰۰٬۰۰۰ ریال");
  });

  it("states that the server has no pagination instead of inventing pages", async () => {
    installApi((path) => {
      if (path === "/api/v1/payments/ledger/17") return reply(200, ledger({ entries: [] }));
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberWallet memberId={17} />);

    expect(await screen.findByText(/این «پرداخت صفر» نیست/)).toBeTruthy();
    expect(screen.getByText(/سرور صفحه‌بندی \(offset\) ندارد/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /صفحهٔ بعد/ })).toBeNull();
  });

  it("fails closed on 403", async () => {
    installApi((path) => {
      if (path === "/api/v1/payments/ledger/17") return reply(403, { error: { message: "forbidden" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberWallet memberId={17} />);
    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به کیف پول این عضو مجاز نیست");
    expect(screen.queryByText(/ریال/)).toBeNull();
  });
});
