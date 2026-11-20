import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { LedgerPanel } from "../src/components/LedgerPanel";

/**
 * QF-05 — پنل دفتر پول عضو.
 *
 * چه چیزی را قفل می‌کند:
 * - پنل هنگام mount درخواستی نمی‌فرستد (صفحهٔ مالی بی‌دلیل شلوغ نمی‌شود).
 * - خواندن دفتر با هدر نشست و شناسهٔ عضو درست انجام می‌شود.
 * - معکوس‌سازی فقط با دلیل به سرور می‌رود؛ ردیف معکوس‌شده/جبرانی دکمهٔ فعال ندارد.
 * - اختلاف تطبیق به‌عنوان هشدار دیده می‌شود، نه «منطبق» سبز.
 */

type Call = { url: string; method: string; auth: string | null; body: unknown };

function stub(routes: { match: RegExp; body: unknown; status?: number }[]) {
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

const entry = (over: Record<string, unknown> = {}) => ({
  id: 11,
  member_id: 7,
  amount_rial: 500_000,
  kind: "charge",
  source_type: "wallet",
  source_id: null,
  reverses_entry_id: null,
  reversed_by_entry_id: null,
  note: "",
  created_at: "2026-03-15T08:00:00Z",
  ...over,
});

const ledger = (entries: ReturnType<typeof entry>[], matches = true) => ({
  member_id: 7,
  balance_rial: 500_000,
  reconcile: {
    wallet_balance_rial: 500_000,
    ledger_balance_rial: matches ? 500_000 : 400_000,
    matches,
    difference_rial: matches ? 0 : 100_000,
  },
  entries,
});

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

describe("LedgerPanel (QF-05)", () => {
  it("sends no request on mount", async () => {
    const calls = stub([]);
    render(<LedgerPanel />);
    await new Promise((r) => setTimeout(r, 50));
    expect(calls).toHaveLength(0);
    expect(screen.getByText(/فقط-افزودنی/)).toBeTruthy();
  }, 20000);

  it("loads the ledger for the given member with the auth header", async () => {
    const calls = stub([
      { match: /GET .*\/payments\/ledger\/7/, body: ledger([entry()]) },
    ]);
    render(<LedgerPanel />);

    fireEvent.change(screen.getByLabelText("شناسهٔ عضو برای دفتر"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "نمایش دفتر" }));

    await waitFor(() => expect(screen.getAllByText(/۵۰۰٬۰۰۰ ریال/).length).toBeGreaterThan(0));
    expect(calls[0].auth).toBe("Bearer tok-123");
    expect(calls[0].url).toContain("/payments/ledger/7");
    expect(screen.getByText("منطبق")).toBeTruthy();
  }, 30000);

  it("shows a mismatch as an alert-worthy difference, not as matched", async () => {
    stub([{ match: /GET .*\/payments\/ledger\/7/, body: ledger([entry()], false) }]);
    render(<LedgerPanel />);

    fireEvent.change(screen.getByLabelText("شناسهٔ عضو برای دفتر"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "نمایش دفتر" }));

    await waitFor(() => expect(screen.getByText(/اختلاف/)).toBeTruthy());
    expect(screen.queryByText("منطبق")).toBeNull();
  }, 30000);

  it("requires a reason before reversing an entry", async () => {
    const calls = stub([
      { match: /GET .*\/payments\/ledger\/7/, body: ledger([entry()]) },
    ]);
    render(<LedgerPanel />);

    fireEvent.change(screen.getByLabelText("شناسهٔ عضو برای دفتر"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "نمایش دفتر" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "معکوس‌سازی" })).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "معکوس‌سازی" }));
    fireEvent.click(screen.getByRole("button", { name: "ثبت معکوس" }));

    await waitFor(() => expect(screen.getByText(/دلیل معکوس‌سازی اجباری است/)).toBeTruthy());
    expect(calls.some((c) => c.method === "POST")).toBe(false);
  }, 30000);

  it("reverses with the reason and reloads the ledger", async () => {
    const calls = stub([
      {
        match: /GET .*\/payments\/ledger\/7/,
        body: ledger([entry({ id: 11, reverses_entry_id: null })]),
      },
      {
        match: /POST .*\/payments\/ledger\/11\/reverse/,
        body: { original_entry_id: 11, reversal_entry: entry({ id: 12, kind: "reversal" }) },
      },
    ]);
    render(<LedgerPanel />);

    fireEvent.change(screen.getByLabelText("شناسهٔ عضو برای دفتر"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "نمایش دفتر" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "معکوس‌سازی" })).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "معکوس‌سازی" }));
    fireEvent.change(screen.getByLabelText("دلیل معکوس‌سازی"), {
      target: { value: "شارژ اشتباه" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ثبت معکوس" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const post = calls.find((c) => c.method === "POST");
    expect(post?.auth).toBe("Bearer tok-123");
    expect(post?.body).toEqual({ reason: "شارژ اشتباه" });
    await waitFor(() =>
      expect(
        calls.filter((c) => c.method === "GET" && c.url.includes("/payments/ledger/7")).length,
      ).toBeGreaterThan(1),
    );
  }, 30000);

  it("offers no reverse button for already reversed or compensating rows", async () => {
    stub([
      {
        match: /GET .*\/payments\/ledger\/7/,
        body: ledger([
          entry({ id: 11, reversed_by_entry_id: 12 }),
          entry({ id: 12, kind: "reversal", reverses_entry_id: 11, amount_rial: -500_000 }),
        ]),
      },
    ]);
    render(<LedgerPanel />);

    fireEvent.change(screen.getByLabelText("شناسهٔ عضو برای دفتر"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "نمایش دفتر" }));

    await waitFor(() => expect(screen.getByText("معکوس‌شده")).toBeTruthy());
    expect(screen.getByText("جبرانی")).toBeTruthy();
    const buttons = screen.getAllByRole("button", { name: "معکوس‌سازی" });
    expect(buttons.every((b) => (b as HTMLButtonElement).disabled)).toBe(true);
  }, 30000);
});
