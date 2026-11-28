/**
 * MEM-13 / PWA-3C — فروشگاه عضو، **فقط نمایش**.
 *
 * معیار پذیرش TODO: «فهرست/تصویر/توضیح/قیمت/موجودی صرفاً برای نمایش؛ API و UI عضو
 * cart/order/checkout نداشته باشند یا fail-closed باشند. خرید حضوری است.»
 *
 * قرارداد واقعی (با `grep -n`):
 * - `modules/shop/router.py:119-149` → `GET /shop/status` و `GET /shop/products`
 *   (با `kind`/`category`/`search`/`limit`).
 * - `modules/shop/router.py:171-216` → `POST /shop/cart` و `POST /shop/checkout`
 *   هر دو **اول** `service.assert_online_purchase_open()` را صدا می‌زنند؛ یعنی
 *   fail-closed قبل از هر نوشتن.
 * - آزمون backend موجود: `tests/integration/test_phase2_shop_display.py:144`
 *   (`test_cart_write_is_fail_closed`) و `:157` (تغییر/حذف سبد). پس این کامپوننت
 *   هیچ‌گاه `cart`/`checkout` را صدا نمی‌زند و تست UI همین را قفل می‌کند.
 *
 * قاعده‌ها:
 * - هیچ دکمهٔ «افزودن به سبد/خرید» وجود ندارد؛ خرید حضوری است.
 * - قیمت و موجودی از سرور می‌آید؛ موجودی صفر ⇒ «ناموجود»، نه «موجود».
 * - `online_purchase: false` در وضعیت فروشگاه ⇒ متن صریح که خرید آنلاین بسته است.
 * - هیچ `image_url` جعلی ساخته نمی‌شود؛ اگر سرور تصویر نداشت، همان را می‌گوید.
 */
import { useEffect, useState } from "react";
import {
  ApiError,
  ForbiddenError,
  fetchMe,
  fetchShopProducts,
  fetchShopStatus,
  type ShopProduct,
  type ShopStatus,
} from "../lib/api";

const PRODUCTS_SOURCE = "منبع: GET /api/v1/shop/products";
const STATUS_SOURCE = "منبع: GET /api/v1/shop/status";

type Load =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; products: ShopProduct[]; status: ShopStatus };

function rial(value: number): string {
  return `${value.toLocaleString("fa-IR")} ریال`;
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return "دسترسی به فروشگاه مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "فروشگاه از سرور دریافت نشد";
}

export function MemberShop({ memberId: _memberId }: { memberId?: number } = {}) {
  const [load, setLoad] = useState<Load>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    // شناسهٔ عضو لازم نیست: هر دو مسیر بر اساس توکن نشست کار می‌کنند و
    // `memberId` صرفاً برای هم‌شکلی با بقیهٔ کامپوننت‌های عضو پذیرفته می‌شود.
    void fetchMe(undefined, controller.signal).catch(() => null);
    setLoad({ kind: "loading" });
    Promise.all([fetchShopProducts({}, undefined, controller.signal), fetchShopStatus(undefined, controller.signal)])
      .then(([products, status]) => setLoad({ kind: "ready", products, status }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoad({ kind: "error", message: failureMessage(error) });
      });
    return () => controller.abort();
  }, []);

  if (load.kind === "error") {
    return (
      <section aria-labelledby="member-shop-title" className="space-y-3">
        <h3 id="member-shop-title" className="text-base font-semibold">
          فروشگاه
        </h3>
        <p role="alert" className="text-sm text-danger">
          {load.message}
        </p>
      </section>
    );
  }

  if (load.kind === "loading") {
    return (
      <section aria-labelledby="member-shop-title" className="space-y-3">
        <h3 id="member-shop-title" className="text-base font-semibold">
          فروشگاه
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت محصولات از سرور…
        </p>
      </section>
    );
  }

  const { products, status } = load;

  return (
    <section aria-labelledby="member-shop-title" className="space-y-4">
      <div>
        <h3 id="member-shop-title" className="text-base font-semibold">
          فروشگاه
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          این فهرست فقط برای نمایش است. خرید حضوری است؛ سبد خرید و تسویهٔ آنلاین در حساب عضو وجود ندارد
          و سمت سرور هم بسته است.
        </p>
      </div>

      <div className="rounded-xl border border-primary/10 px-4 py-3 text-xs" data-shop-open={status.is_open ? "yes" : "no"}>
        <p className="font-semibold">
          وضعیت فروشگاه: {status.is_open ? "باز" : "بسته"} ({status.reason}) · حالت: {status.mode}
        </p>
        <p className="mt-1 text-ink-dim">
          ساعت کاری: {status.opens_at} تا {status.closes_at} ({status.timezone}) · خرید آنلاین:{" "}
          {status.online_purchase ? "فعال" : "بسته"}
        </p>
        <p className="mt-1 text-ink-dim">{STATUS_SOURCE}</p>
      </div>

      {products.length === 0 ? (
        <p role="status" className="text-sm text-ink-dim">
          سرور هیچ محصولی برنگرداند.
        </p>
      ) : (
        <ul className="space-y-2">
          {products.map((product) => (
            <li
              key={product.id}
              data-product-id={product.id}
              data-stock-qty={product.stock_qty}
              className="rounded-xl border border-primary/10 px-4 py-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h4 className="text-sm font-semibold">{product.title}</h4>
                <span className="text-xs font-semibold">{rial(product.price_rial)}</span>
              </div>
              {product.subtitle ? <p className="mt-1 text-xs text-ink-dim">{product.subtitle}</p> : null}
              {product.description ? <p className="mt-1 text-xs text-ink-dim">{product.description}</p> : null}
              <p className="mt-1 text-[11px] text-ink-dim">
                موجودی: {product.stock_qty > 0 ? `${product.stock_qty.toLocaleString("fa-IR")} عدد` : "ناموجود"}
                {product.image_url ? " · تصویر از سرور" : " · تصویری برای این محصول ثبت نشده"}
                {product.is_active ? "" : " · غیرفعال"}
              </p>
            </li>
          ))}
        </ul>
      )}

      <p className="text-[11px] text-ink-dim">{PRODUCTS_SOURCE}</p>
    </section>
  );
}
