/**
 * MEM-13 / PWA-3C — فروشگاه عضو، فقط نمایش.
 *
 * قفل‌ها:
 * - هیچ درخواستی به `/shop/cart` یا `/shop/checkout` نمی‌رود و هیچ دکمهٔ خرید
 *   وجود ندارد (خرید حضوری است؛ سرور هم fail-closed است:
 *   `tests/integration/test_phase2_shop_display.py:144`).
 * - قیمت و موجودی از سرور؛ `stock_qty = 0` ⇒ «ناموجود».
 * - وضعیت فروشگاه (باز/بسته + خرید آنلاین) از `/shop/status` می‌آید.
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberShop } from "../src/components/MemberShop";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const status = (overrides: Record<string, unknown> = {}) => ({
  mode: "in_person",
  is_open: true,
  reason: "open",
  opens_at: "08:00",
  closes_at: "22:00",
  timezone: "Asia/Tehran",
  closed_weekdays: [5],
  online_purchase: false,
  checked_at: "2026-11-27T10:00:00Z",
  ...overrides,
});

const product = (overrides: Record<string, unknown> = {}) => ({
  id: 3,
  sku: "WHEY-1KG",
  title: "پروتئین وی",
  subtitle: "۱ کیلوگرم",
  description: "طعم وانیل",
  price_rial: 3200000,
  compare_at_rial: null,
  image_url: "",
  gallery: [],
  category_id: 1,
  stock_qty: 4,
  is_active: true,
  variants: [],
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

describe("member shop, display only (MEM-13)", () => {
  it("lists products with server price and stock, and never calls cart or checkout", async () => {
    const calls = installApi((path) => {
      if (path === "/api/v1/shop/products") return reply(200, [product()]);
      if (path === "/api/v1/shop/status") return reply(200, status());
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberShop />);

    expect(await screen.findByText("پروتئین وی")).toBeTruthy();
    expect(screen.getByText("۳٬۲۰۰٬۰۰۰ ریال")).toBeTruthy();
    expect(screen.getByText(/موجودی: ۴ عدد/)).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/shop\/products/)).toBeTruthy();
    expect(screen.getByText(/خرید حضوری است/)).toBeTruthy();
    // مهم‌ترین قفل: هیچ نوشتنی در فروشگاه وجود ندارد.
    expect(calls.some((path) => path.includes("/shop/cart"))).toBe(false);
    expect(calls.some((path) => path.includes("/shop/checkout"))).toBe(false);
    expect(screen.queryByRole("button", { name: /افزودن به سبد|خرید|تسویه/ })).toBeNull();
  });

  it("marks an out-of-stock product as unavailable, not available", async () => {
    installApi((path) => {
      if (path === "/api/v1/shop/products") return reply(200, [product({ stock_qty: 0 })]);
      if (path === "/api/v1/shop/status") return reply(200, status());
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberShop />);

    expect(await screen.findByText(/موجودی: ناموجود/)).toBeTruthy();
    expect(container.querySelector('[data-stock-qty="0"]')).toBeTruthy();
  });

  it("reports the shop's own closed state and that online purchase is off", async () => {
    installApi((path) => {
      if (path === "/api/v1/shop/products") return reply(200, [product()]);
      if (path === "/api/v1/shop/status")
        return reply(200, status({ is_open: false, reason: "outside_hours", online_purchase: false }));
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberShop />);

    expect(await screen.findByText(/وضعیت فروشگاه: بسته \(outside_hours\)/)).toBeTruthy();
    expect(screen.getByText(/خرید آنلاین: بسته/)).toBeTruthy();
    expect(container.querySelector('[data-shop-open="no"]')).toBeTruthy();
  });

  it("says an image is missing instead of inventing one", async () => {
    installApi((path) => {
      if (path === "/api/v1/shop/products") return reply(200, [product({ image_url: "" })]);
      if (path === "/api/v1/shop/status") return reply(200, status());
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberShop />);

    expect(await screen.findByText(/تصویری برای این محصول ثبت نشده/)).toBeTruthy();
    expect(container.querySelector("img")).toBeNull();
  });

  it("fails closed on 403", async () => {
    installApi((path) => {
      if (path === "/api/v1/shop/products") return reply(403, { error: { message: "forbidden" } });
      if (path === "/api/v1/shop/status") return reply(200, status());
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberShop />);
    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به فروشگاه مجاز نیست");
  });
});
