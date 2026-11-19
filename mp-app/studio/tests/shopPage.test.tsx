import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { Shop } from "../src/pages/Shop";
import { ToastViewport, useToastStore } from "../src/components/Feedback";

/**
 * M59 — رگرسیون صفحهٔ فروشگاه.
 *
 * چرا این تست‌ها: صفحهٔ «فروشگاه» در اپ Dart چهار محصول hardcode داشت و
 * هیچ‌کدام از این قواعد را نداشت. تست‌ها همان قواعد را قفل می‌کنند:
 *
 * 1) تب «مدیریت کاتالوگ» برای admin **دیده نمی‌شود** (فقط super_admin)
 * 2) admin تب «درخواست‌ها» را می‌بیند (مسیر مجازش)
 * 3) فهرست محصولات از API می‌آید، نه از آرایهٔ ثابت
 * 4) تسویه از کیف‌پول یک دیالوگ تأیید می‌خواهد و بعد POST می‌زند
 * 5) شمارهٔ کارت ماسک‌شده نمایش داده می‌شود
 */

type Call = { url: string; method: string; body: unknown };

function stub(role: string) {
  const calls: Call[] = [];
  const token = `h.${btoa(JSON.stringify({ role }))}.s`;
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => (k === "mp_token" ? token : null),
    setItem: () => undefined,
    removeItem: () => undefined,
  });
  const products = [
    {
      id: 7,
      sku: "WHEY-1",
      title: "پروتئین وی ۲ کیلو",
      subtitle: "شکلاتی",
      description: "",
      price_rial: 2_500_000,
      compare_at_rial: 3_000_000,
      image_url: "/static/shop/whey.jpg",
      gallery: [],
      category_id: 1,
      stock_qty: 4,
      is_active: true,
      variants: [],
    },
  ];
  const cart = {
    member_id: 1,
    items: [
      {
        id: 11,
        product_id: 7,
        variant_id: null,
        title: "پروتئین وی ۲ کیلو",
        variant_label: "",
        image_url: "",
        unit_price_rial: 2_500_000,
        qty: 1,
        line_total_rial: 2_500_000,
      },
    ],
    total_rial: 2_500_000,
    count: 1,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = (init?.method ?? "GET").toUpperCase();
      calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : null });
      const json = (b: unknown) => new Response(JSON.stringify(b), { status: 200 });
      if (url.includes("/shop/products") && method === "GET") return json(products);
      if (url.includes("/shop/categories")) return json([{ id: 1, slug: "supplements", title: "مکمل", kind: "supplement", sort_order: 0, is_active: true }]);
      if (url.includes("/shop/cart") && method === "GET") return json(cart);
      if (url.includes("/shop/cart") && method === "POST") return json(cart);
      if (url.includes("/receipt"))
        return json({
          receipt_no: "O-000091",
          order_id: 91,
          member_id: 1,
          member_name: "سارا محمدی",
          status: "paid",
          note: "",
          created_at: "2026-11-15T10:00:00Z",
          lines: [
            {
              product_id: 7,
              title: "پروتئین وی ۲ کیلو",
              variant: "شکلاتی",
              unit_price_rial: 2_500_000,
              qty: 1,
              line_total_rial: 2_500_000,
            },
          ],
          items_total_rial: 2_500_000,
          total_rial: 2_500_000,
          payment: {
            id: 55,
            method: "wallet",
            status: "paid",
            reference_id: "ref-1",
            paid_at: "2026-11-15T10:00:00Z",
          },
          issued_at: "2026-11-15T10:01:00Z",
          branch: "Muscle Paradise",
        });
      if (url.includes("/shop/orders"))
        return json([
          {
            id: 91,
            member_id: 1,
            status: "paid",
            total_rial: 2_500_000,
            payment_id: 55,
            note: "",
            created_at: "2026-11-15T10:00:00Z",
            items: [{ product_id: 7, title: "پروتئین وی ۲ کیلو", unit_price_rial: 2_500_000, qty: 1 }],
          },
        ]);
      if (url.includes("/shop/gateways"))
        return json([
          {
            id: 3,
            kind: "card_to_card",
            title: "کارت به کارت ملت",
            is_enabled: true,
            card_number_masked: "6104-****-****-5678",
            card_holder: "باشگاه",
            bank_name: "ملت",
            public_key: "",
            instructions: "",
            secret_configured: true,
          },
        ]);
      if (url.includes("/shop/prices")) return json([]);
      if (url.includes("/shop/change-requests")) return json([]);
      if (url.includes("/shop/checkout"))
        return json({ order_id: 91, status: "paid", total_rial: 2_500_000, payment_id: 55 });
      return json({});
    }),
  );
  return calls;
}

describe("صفحهٔ فروشگاه — سطوح دسترسی و جریان خرید", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    useToastStore.setState({ toasts: [] });
  });

  it("عضو عادی تنها تب‌های خرید را می‌بیند", async () => {
    stub("member");
    render(<Shop />);
    await waitFor(() => expect(screen.getByText("پروتئین وی ۲ کیلو")).toBeTruthy());
    expect(screen.queryByText("مدیریت کاتالوگ")).toBeNull();
    expect(screen.queryByText("درخواست‌ها")).toBeNull();
    expect(screen.getByText("سبد (۱)")).toBeTruthy();
  });

  it("ادمین تب درخواست‌ها را دارد ولی کنسول مالک را ندارد", async () => {
    stub("admin");
    render(<Shop />);
    await waitFor(() => expect(screen.getByText("درخواست‌ها")).toBeTruthy());
    expect(screen.queryByText("مدیریت کاتالوگ")).toBeNull();
  });

  it("مالک کنسول کامل (محصول/قیمت/درگاه) را می‌بیند", async () => {
    stub("super_admin");
    render(<Shop />);
    await waitFor(() => expect(screen.getByText("مدیریت کاتالوگ")).toBeTruthy());
    screen.getByText("مدیریت کاتالوگ").click();
    await waitFor(() => expect(screen.getByText("محصول جدید (فقط مالک)")).toBeTruthy());
    expect(screen.getByText("دفتر قیمت خدمات")).toBeTruthy();
    expect(screen.getByText("درگاه و شمارهٔ کارت (فقط مالک)")).toBeTruthy();
  });

  it("تسویه دیالوگ تأیید می‌خواهد و سپس POST /shop/checkout می‌زند", async () => {
    const calls = stub("member");
    render(
      <>
        <Shop />
        <ToastViewport />
      </>,
    );
    await waitFor(() => expect(screen.getByText("سبد (۱)")).toBeTruthy());
    screen.getByText("سبد (۱)").click();
    await waitFor(() => expect(screen.getByText("تسویه از کیف‌پول")).toBeTruthy());
    screen.getByText("تسویه از کیف‌پول").click();

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/کسر می‌شود/)).toBeTruthy();
    within(dialog).getByText("پرداخت").click();

    await waitFor(() =>
      expect(calls.some((c) => c.method === "POST" && c.url.includes("/shop/checkout"))).toBe(true),
    );
    await waitFor(() => expect(screen.getByRole("status")).toBeTruthy());
  });

  it("شمارهٔ کارت فقط ماسک‌شده روی صفحه می‌آید", async () => {
    stub("member");
    render(<Shop />);
    await waitFor(() => expect(screen.getByText("سبد (۱)")).toBeTruthy());
    screen.getByText("سبد (۱)").click();
    await waitFor(() => expect(screen.getByText(/6104-\*\*\*\*-\*\*\*\*-5678/)).toBeTruthy());
    expect(document.body.textContent).not.toContain("6104337712345678");
  });

  /**
   * M60/R5 — رسید سفارش.
   *
   * چرا این تست: مسیر `/shop/orders/{id}/receipt` فقط زمانی «مصرف‌کنندهٔ
   * واقعی» دارد که دکمه‌اش در UI کار کند؛ وگرنه دوباره یک endpoint دکوراتیو
   * است (همان ردهٔ باگی که گیت apiCoverage برایش نوشته شد).
   */
  it("دکمهٔ رسید، رسید واقعی سفارش را باز می‌کند", async () => {
    const calls = stub("member");
    render(<Shop />);
    await waitFor(() => expect(screen.getByText("سبد (۱)")).toBeTruthy());
    screen.getByText("سفارش‌ها").click();

    const receiptBtn = await screen.findByText("رسید");
    receiptBtn.click();

    // نام دسترس‌پذیر دیالوگ حالا از عنوان کتابخانه‌ای می‌آید (Q11): «رسید O-000091».
    const dialog = await screen.findByRole("dialog", { name: /رسید O-000091/ });
    expect(within(dialog).getByText("رسید O-000091")).toBeTruthy();
    expect(within(dialog).getByText("سارا محمدی · وضعیت paid · Muscle Paradise")).toBeTruthy();
    // واریانت در همان سطر کالا می‌آید
    expect(within(dialog).getByText("پروتئین وی ۲ کیلو (شکلاتی)")).toBeTruthy();
    // جمع از سرور می‌آید، نه محاسبهٔ سمت کلاینت
    expect(within(dialog).getAllByText(/۲٬۵۰۰٬۰۰۰/).length).toBeGreaterThan(0);
    expect(calls.some((c) => c.url.includes("/shop/orders/91/receipt"))).toBe(true);
  });
});
