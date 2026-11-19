/**
 * فروشگاه و کیف‌پول — صفحهٔ کامل (M59).
 *
 * سه لایه در یک صفحه، به‌ترتیب نقش:
 *
 * | نقش | چه می‌بیند |
 * |---|---|
 * | member | کاتالوگ، سبد، تسویه از کیف‌پول/درگاه، سفارش‌های خودش |
 * | admin | همان + تب «درخواست‌ها» (پیشنهاد قیمت/محصول ← منتظر تأیید مالک) |
 * | super_admin | همان + تب «مدیریت»: ساخت محصول با تصویر، قیمت، درگاه و شمارهٔ کارت |
 *
 * قاعدهٔ نمایش ≠ قاعدهٔ امنیت: پنهان‌کردن دکمه برای admin، امنیت نیست —
 * سرور هم ۴۰۳ می‌دهد (`ensure_owner`). UI فقط جلوی سرخوردگی را می‌گیرد.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useMotionPreset } from "../lib/motion";
import { ConfirmDialog, SkeletonCards, toast } from "../components/Feedback";
import { fa } from "../lib/useApi";
import {
  addCartItem,
  askChangeRequest,
  checkoutCart,
  createProduct,
  fetchCart,
  fetchChangeRequests,
  fetchGateways,
  fetchPrices,
  fetchShopCategories,
  fetchShopOrders,
  fetchShopProducts,
  removeCartItem,
  reviewChangeRequest,
  savePrice,
  updateCartItem,
  upsertGateway,
  type CartLine,
  type ChangeRequest,
  type PriceRow,
  type ShopCart,
  type ShopCategory,
  type ShopGateway,
  type ShopOrder,
  type ShopProduct,
  type OrderReceipt,
} from "../lib/api";

import { roleFromToken } from "../lib/roleNav";

/** InputNumber با stringMode مقدار رشته‌ای می‌دهد؛ stateها رشته‌ای می‌مانند. */
const asText = (value: string | number | null | undefined): string =>
  value === null || value === undefined ? "" : String(value);
import { Input, InputNumber, Modal, Select } from "antd";

const rial = (n: number) => `${fa(n)} ریال`;

type Tab = "store" | "cart" | "orders" | "manage" | "requests";

export function Shop() {
  const motionPreset = useMotionPreset();
  // M60/R3: منبع حقیقت مشترک (lib/roleNav) — قبلاً هر صفحه نسخهٔ خودش را داشت.
  const role = roleFromToken();
  const isOwner = role === "super_admin";
  const isAdmin = isOwner || role === "admin";

  const [tab, setTab] = useState<Tab>("store");
  const [products, setProducts] = useState<ShopProduct[]>([]);
  const [categories, setCategories] = useState<ShopCategory[]>([]);
  const [cart, setCart] = useState<ShopCart | null>(null);
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [gateways, setGateways] = useState<ShopGateway[]>([]);
  const [prices, setPrices] = useState<PriceRow[]>([]);
  const [requests, setRequests] = useState<ChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [confirmCheckout, setConfirmCheckout] = useState(false);
  const [pendingApproval, setPendingApproval] = useState<ChangeRequest | null>(null);
  // رسید باز (R5) — چاپ سفارش برای تحویل
  const [receipt, setReceipt] = useState<OrderReceipt | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    const results = await Promise.allSettled([
      fetchShopProducts(filter ? { category: filter } : {}),
      fetchShopCategories(),
      fetchCart(),
      fetchShopOrders(),
      fetchGateways(),
      fetchPrices(),
      isAdmin ? fetchChangeRequests() : Promise.resolve([] as ChangeRequest[]),
    ]);
    const [p, c, k, o, g, pr, rq] = results;
    if (p.status === "fulfilled") setProducts(p.value);
    if (c.status === "fulfilled") setCategories(c.value);
    if (k.status === "fulfilled") setCart(k.value);
    if (o.status === "fulfilled") setOrders(o.value);
    if (g.status === "fulfilled") setGateways(g.value);
    if (pr.status === "fulfilled") setPrices(pr.value);
    if (rq.status === "fulfilled") setRequests(rq.value);
    const failed = results.find((r) => r.status === "rejected");
    if (failed && failed.status === "rejected") {
      const msg = failed.reason instanceof Error ? failed.reason.message : "دریافت داده ناموفق";
      toast.error(msg);
    }
    setLoading(false);
  }, [filter, isAdmin]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const visible = useMemo(
    () =>
      products.filter(
        (p) =>
          !search ||
          p.title.includes(search) ||
          p.sku.toLowerCase().includes(search.toLowerCase()),
      ),
    [products, search],
  );

  const act = async (fn: () => Promise<void>, okMessage?: string) => {
    try {
      await fn();
      if (okMessage) toast.success(okMessage);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "عملیات ناموفق بود");
    }
  };

  const tabs: { id: Tab; label: string; show: boolean }[] = [
    { id: "store", label: "فروشگاه", show: true },
    { id: "cart", label: `سبد${cart?.count ? ` (${fa(cart.count)})` : ""}`, show: true },
    { id: "orders", label: "سفارش‌ها", show: true },
    { id: "manage", label: "مدیریت کاتالوگ", show: isOwner },
    { id: "requests", label: "درخواست‌ها", show: isAdmin },
  ];

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">فروشگاه و کیف‌پول</h2>
          <p className="mt-1 text-sm text-ink-dim">
            تجهیزات، مکمل و پوشاک — قیمت‌گذاری و افزودن محصول فقط با مالک سیستم
          </p>
        </div>
        <div className="flex flex-wrap gap-1 rounded-2xl bg-surface/70 p-1">
          {tabs
            .filter((t) => t.show)
            .map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`focus-ring relative rounded-xl px-3 py-1.5 text-sm transition-colors ${
                  tab === t.id ? "text-white" : "text-ink-dim hover:text-ink"
                }`}
              >
                {tab === t.id && (
                  <motion.span
                    layoutId="shop-tab"
                    className="absolute inset-0 rounded-xl bg-primary/20 ring-1 ring-primary/40"
                    transition={
                      motionPreset.reduced
                        ? { duration: 0 }
                        : { type: "spring", stiffness: 380, damping: 32 }
                    }
                  />
                )}
                <span className="relative z-10">{t.label}</span>
              </button>
            ))}
        </div>
      </header>

      {loading && <SkeletonCards count={3} />}

      {!loading && tab === "store" && (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="جست‌وجوی محصول…"
              aria-label="جست‌وجوی محصول"
              className="focus-ring w-56 rounded-xl bg-surface/70 px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => setFilter("")}
              className={`rounded-xl px-3 py-2 text-sm ${!filter ? "bg-primary/20 text-ink" : "bg-surface/70 text-ink-dim"}`}
            >
              همه
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setFilter(c.slug)}
                className={`rounded-xl px-3 py-2 text-sm ${
                  filter === c.slug ? "bg-primary/20 text-ink" : "bg-surface/70 text-ink-dim"
                }`}
              >
                {c.title}
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <div className="glass-card p-8 text-center text-sm text-ink-dim">
              هنوز محصولی ثبت نشده است.
              {isOwner && " از تب «مدیریت کاتالوگ» اولین محصول را با تصویر بسازید."}
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {visible.map((p) => (
                <motion.article
                  key={p.id}
                  layout
                  {...motionPreset.rise}
                  className="glass-card group overflow-hidden"
                >
                  {p.image_url ? (
                    <img
                      src={p.image_url}
                      alt={p.title}
                      loading="lazy"
                      className="h-40 w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
                    />
                  ) : (
                    <div className="flex h-40 items-center justify-center bg-surface/60 text-ink-dim">
                      بدون تصویر
                    </div>
                  )}
                  <div className="space-y-2 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-bold leading-6">{p.title}</h3>
                      <span className="pill shrink-0">{p.stock_qty >= 0 ? `${fa(p.stock_qty)} عدد` : "نامحدود"}</span>
                    </div>
                    {p.subtitle && <p className="text-xs text-ink-dim">{p.subtitle}</p>}
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-primary-light">{rial(p.price_rial)}</span>
                      {p.compare_at_rial && p.compare_at_rial > p.price_rial && (
                        <span className="text-xs text-ink-dim line-through">{rial(p.compare_at_rial)}</span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        act(async () => {
                          const next = await addCartItem(p.id, 1);
                          setCart(next);
                          toast.success("به سبد اضافه شد");
                        })
                      }
                      disabled={p.stock_qty === 0}
                      className="focus-ring w-full rounded-xl bg-primary px-3 py-2 text-sm font-medium text-white transition-transform active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {p.stock_qty === 0 ? "ناموجود" : "افزودن به سبد"}
                    </button>
                  </div>
                </motion.article>
              ))}
            </div>
          )}
        </section>
      )}

      <Modal
        centered
        footer={null}
        open={Boolean(receipt)}
        title={receipt ? `رسید ${receipt.receipt_no}` : undefined}
        onCancel={() => setReceipt(null)}
      >
        {receipt && (
          <div className="space-y-3">
            <p className="text-xs text-ink-dim">
              {receipt.member_name ?? `عضو #${fa(receipt.member_id)}`} · وضعیت {receipt.status} ·{" "}
              {receipt.branch}
            </p>
            <table className="mt-3 w-full text-xs">
              <thead className="text-ink-dim">
                <tr>
                  <th className="text-right">کالا</th>
                  <th className="text-right">تعداد</th>
                  <th className="text-right">جمع</th>
                </tr>
              </thead>
              <tbody>
                {receipt.lines.map((l, i) => (
                  <tr key={i}>
                    <td>{l.variant ? `${l.title} (${l.variant})` : l.title}</td>
                    <td>{fa(l.qty)}</td>
                    <td>{rial(l.line_total_rial)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-3 flex items-center justify-between border-t border-white/10 pt-2 text-sm">
              <span>جمع کل</span>
              <span className="font-bold">{rial(receipt.total_rial)}</span>
            </div>
            {receipt.payment && (
              <p className="mt-2 text-xs text-ink-dim">
                پرداخت {receipt.payment.method} · {receipt.payment.status}
                {receipt.payment.reference_id ? ` · ${receipt.payment.reference_id}` : ""}
              </p>
            )}
            <button
              type="button"
              onClick={() => window.print()}
              className="focus-ring mt-4 w-full rounded-xl bg-primary px-4 py-2 text-sm text-white"
            >
              چاپ
            </button>
          </div>
        )}
      </Modal>

      {!loading && tab === "cart" && (
        <section className="glass-card space-y-4 p-5">
          {!cart || cart.count === 0 ? (
            <p className="text-sm text-ink-dim">سبد خالی است.</p>
          ) : (
            <>
              <ul className="divide-y divide-white/10">
                {cart.items.map((line: CartLine) => (
                  <li key={line.id} className="flex flex-wrap items-center gap-3 py-3">
                    <span className="min-w-40 flex-1 text-sm">
                      {line.title}
                      {line.variant_label && <span className="text-ink-dim"> — {line.variant_label}</span>}
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        aria-label="کاهش تعداد"
                        onClick={() =>
                          act(async () => setCart(await updateCartItem(line.id, line.qty - 1)))
                        }
                        className="focus-ring h-8 w-8 rounded-lg bg-surface/70"
                      >
                        −
                      </button>
                      <span className="w-8 text-center text-sm">{fa(line.qty)}</span>
                      <button
                        type="button"
                        aria-label="افزایش تعداد"
                        onClick={() =>
                          act(async () => setCart(await updateCartItem(line.id, line.qty + 1)))
                        }
                        className="focus-ring h-8 w-8 rounded-lg bg-surface/70"
                      >
                        +
                      </button>
                    </div>
                    <span className="w-32 text-left text-sm">{rial(line.line_total_rial)}</span>
                    <button
                      type="button"
                      onClick={() => act(async () => setCart(await removeCartItem(line.id)), "حذف شد")}
                      className="focus-ring rounded-lg px-2 text-xs text-danger"
                    >
                      حذف
                    </button>
                  </li>
                ))}
              </ul>
              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-3">
                <span className="text-sm">
                  مبلغ قابل پرداخت: <b className="text-primary-light">{rial(cart.total_rial)}</b>
                </span>
                <div className="flex gap-2">
                  {gateways
                    .filter((g) => g.is_enabled)
                    .map((g) => (
                      <span key={g.id} className="pill">
                        {g.title}
                        {g.card_number_masked && ` · ${g.card_number_masked}`}
                      </span>
                    ))}
                  <button
                    type="button"
                    onClick={() => setConfirmCheckout(true)}
                    className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white"
                  >
                    تسویه از کیف‌پول
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      )}

      {!loading && tab === "orders" && (
        <section className="space-y-3">
          {orders.length === 0 ? (
            <p className="text-sm text-ink-dim">سفارشی ثبت نشده است.</p>
          ) : (
            orders.map((o) => (
              <article key={o.id} className="glass-card p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-bold">سفارش #{fa(o.id)}</span>
                  <span className="pill">{o.status}</span>
                  <span className="text-sm">{rial(o.total_rial)}</span>
                </div>
                <ul className="mt-2 space-y-1 text-xs text-ink-dim">
                  {o.items.map((it, i) => (
                    <li key={i}>
                      {it.title} × {fa(it.qty)} — {rial(it.unit_price_rial)}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() =>
                    act(async () => {
                      const { fetchOrderReceipt } = await import("../lib/api");
                      setReceipt(await fetchOrderReceipt(o.id));
                    }, "")
                  }
                  className="focus-ring mt-3 rounded-xl border border-white/15 px-3 py-1.5 text-xs"
                >
                  رسید
                </button>
                {isAdmin && o.status === "paid" && (
                  <button
                    type="button"
                    onClick={() =>
                      act(async () => {
                        await import("../lib/api").then((m) => m.markOrderStatus(o.id, "delivered"));
                        await reload();
                      }, "تحویل ثبت شد")
                    }
                    className="focus-ring mt-3 rounded-xl bg-primary/20 px-3 py-1.5 text-xs"
                  >
                    ثبت تحویل
                  </button>
                )}
              </article>
            ))
          )}
        </section>
      )}

      {!loading && tab === "manage" && isOwner && (
        <OwnerConsole
          categories={categories}
          products={products}
          gateways={gateways}
          prices={prices}
          onDone={reload}
        />
      )}

      {!loading && tab === "requests" && isAdmin && (
        <section className="space-y-3">
          <AdminRequestForm categories={categories} products={products} onDone={reload} />
          {requests.length === 0 ? (
            <p className="text-sm text-ink-dim">درخواستی وجود ندارد.</p>
          ) : (
            requests.map((r) => (
              <article key={r.id} className="glass-card p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-bold">
                    {r.kind_label} — #{fa(r.id)}
                  </span>
                  <span
                    className={`pill ${
                      r.status === "approved"
                        ? "text-success"
                        : r.status === "rejected"
                          ? "text-danger"
                          : "text-accent"
                    }`}
                  >
                    {r.status === "pending" ? "منتظر تأیید مالک" : r.status}
                  </span>
                </div>
                <pre className="mt-2 overflow-x-auto rounded-xl bg-black/30 p-3 text-[11px] text-ink-dim" dir="ltr">
                  {JSON.stringify(r.payload, null, 2)}
                </pre>
                {isOwner && r.status === "pending" && r.requested_by !== undefined && (
                  <button
                    type="button"
                    onClick={() => setPendingApproval(r)}
                    className="focus-ring mt-3 rounded-xl bg-accent/20 px-3 py-1.5 text-xs text-accent"
                  >
                    بررسی و تأیید
                  </button>
                )}
              </article>
            ))
          )}
        </section>
      )}

      <ConfirmDialog
        open={confirmCheckout}
        title="تسویه از کیف‌پول"
        body={cart ? `مبلغ ${rial(cart.total_rial)} از موجودی کیف‌پول کسر می‌شود.` : undefined}
        confirmLabel="پرداخت"
        onCancel={() => setConfirmCheckout(false)}
        onConfirm={() => {
          setConfirmCheckout(false);
          void act(async () => {
            const res = await checkoutCart("wallet");
            toast.success(`سفارش #${fa(res.order_id)} ثبت شد`);
            setTab("orders");
            await reload();
          });
        }}
      />

      <ConfirmDialog
        open={pendingApproval !== null}
        title="تأیید درخواست تغییر"
        body="با تأیید، تغییر همین حالا اعمال و در لاگ ممیزی ثبت می‌شود."
        confirmLabel="تأیید و اعمال"
        onCancel={() => setPendingApproval(null)}
        onConfirm={() => {
          const req = pendingApproval;
          setPendingApproval(null);
          if (!req) return;
          void act(async () => {
            await reviewChangeRequest(req.id, true, "تأیید مالک");
            toast.success("تغییر اعمال شد");
            await reload();
          });
        }}
      />
    </div>
  );
}

/** کنسول مالک: محصول جدید (با تصویر)، قیمت خدمات، درگاه/کارت. */
function OwnerConsole({
  categories,
  products,
  gateways,
  prices,
  onDone,
}: {
  categories: ShopCategory[];
  products: ShopProduct[];
  gateways: ShopGateway[];
  prices: PriceRow[];
  onDone: () => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [sku, setSku] = useState("");
  const [price, setPrice] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [stock, setStock] = useState("10");
  const [categoryId, setCategoryId] = useState<number | "">(categories[0]?.id ?? "");

  const [priceCode, setPriceCode] = useState("");
  const [priceTitle, setPriceTitle] = useState("");
  const [priceValue, setPriceValue] = useState("");
  const [priceCategory, setPriceCategory] = useState<PriceRow["category"]>("membership");

  const [cardKind, setCardKind] = useState<ShopGateway["kind"]>("card_to_card");
  const [cardTitle, setCardTitle] = useState("کارت به کارت");
  const [cardNumber, setCardNumber] = useState("");
  const [cardHolder, setCardHolder] = useState("");

  const need = (value: string, label: string) => {
    if (!value.trim()) throw new Error(`${label} را پر کنید`);
  };

  const run = async (fn: () => Promise<void>, msg: string) => {
    try {
      await fn();
      toast.success(msg);
      await onDone();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "عملیات ناموفق");
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <form
        className="glass-card space-y-3 p-5"
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            if (!categoryId) throw new Error("ابتدا یک دسته بسازید");
            need(title, "نام محصول");
            need(sku, "SKU");
            need(price, "قیمت");
            await createProduct({
              title,
              sku,
              category_id: Number(categoryId),
              price_rial: Number(price || 0),
              image_url: imageUrl,
              stock_qty: Number(stock || 0),
            });
            setTitle("");
            setSku("");
            setPrice("");
            setImageUrl("");
          }, "محصول ساخته شد");
        }}
      >
        <h3 className="text-sm font-bold">محصول جدید (فقط مالک)</h3>
        <Input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="نام محصول" aria-label="نام محصول" className="focus-ring w-full rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        <Input required value={sku} onChange={(e) => setSku(e.target.value)} placeholder="SKU (یکتا)" aria-label="SKU (یکتا)" className="focus-ring w-full rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        <div className="grid grid-cols-2 gap-2">
          <InputNumber stringMode value={price} onChange={(v) => setPrice(asText(v))} placeholder="قیمت (ریال)" aria-label="قیمت (ریال)" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
          <InputNumber stringMode value={stock} onChange={(v) => setStock(asText(v))} placeholder="موجودی" aria-label="موجودی" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        </div>
        <Input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder="آدرس تصویر (مثلاً /static/shop/whey.jpg)" aria-label="آدرس تصویر (مثلاً /static/shop/whey.jpg)" className="focus-ring w-full rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        {imageUrl && <img src={imageUrl} alt="پیش‌نمایش" className="h-28 w-full rounded-xl object-cover" />}
        <Select
          aria-label="دستهٔ محصول"
          className="w-full"
          options={categories.map((c) => ({ value: c.id, label: `${c.title} (${c.kind})` }))}
          value={categoryId}
          onChange={(value) => setCategoryId(Number(value))}
        />
        <button type="submit" className="focus-ring w-full rounded-xl bg-primary px-3 py-2 text-sm font-medium text-white">
          ساخت محصول
        </button>
        <p className="text-[11px] text-ink-dim">
          {fa(products.length)} محصول در کاتالوگ — تغییر قیمت از همین فرم با SKU تکراری پیام خطا می‌دهد
        </p>
      </form>

      <form
        className="glass-card space-y-3 p-5"
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            need(priceCode, "کد");
            need(priceTitle, "عنوان");
            need(priceValue, "مبلغ");
            await savePrice({
              category: priceCategory,
              code: priceCode,
              title: priceTitle,
              price_rial: Number(priceValue || 0),
            });
            setPriceCode("");
            setPriceTitle("");
            setPriceValue("");
          }, "قیمت ثبت شد");
        }}
      >
        <h3 className="text-sm font-bold">دفتر قیمت خدمات</h3>
        <Select
          aria-label="دستهٔ قیمت"
          className="w-full"
          options={[
            { value: "membership", label: "اشتراک" },
            { value: "coach_fee", label: "شهریهٔ مربی" },
            { value: "program_fee", label: "هزینهٔ برنامه" },
          ]}
          value={priceCategory}
          onChange={(value) => setPriceCategory(value as PriceRow["category"])}
        />
        <div className="grid grid-cols-2 gap-2">
          <Input required value={priceCode} onChange={(e) => setPriceCode(e.target.value)} placeholder="کد (gold-3m)" aria-label="کد (gold-3m)" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
          <InputNumber stringMode value={priceValue} onChange={(v) => setPriceValue(asText(v))} placeholder="مبلغ (ریال)" aria-label="مبلغ (ریال)" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        </div>
        <Input required value={priceTitle} onChange={(e) => setPriceTitle(e.target.value)} placeholder="عنوان قیمت" aria-label="عنوان قیمت" className="focus-ring w-full rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        <button type="submit" className="focus-ring w-full rounded-xl bg-primary px-3 py-2 text-sm font-medium text-white">
          ثبت / به‌روزرسانی قیمت
        </button>
        <ul className="space-y-1 text-xs text-ink-dim">
          {prices.map((p) => (
            <li key={p.id}>
              {p.title} — {rial(p.price_rial)}
            </li>
          ))}
        </ul>
      </form>

      <form
        className="glass-card space-y-3 p-5 lg:col-span-2"
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            await upsertGateway({
              kind: cardKind,
              title: cardTitle,
              is_enabled: true,
              card_number: cardNumber.replace(/\D/g, ""),
              card_holder: cardHolder,
            });
            setCardNumber("");
          }, "درگاه/کارت ثبت شد");
        }}
      >
        <h3 className="text-sm font-bold">درگاه و شمارهٔ کارت (فقط مالک)</h3>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Select
            aria-label="نوع درگاه"
            options={[
              { value: "card_to_card", label: "کارت به کارت" },
              { value: "zarinpal", label: "زرین‌پال" },
              { value: "idpay", label: "آیدی‌پی" },
              { value: "cash", label: "نقدی" },
            ]}
            value={cardKind}
            onChange={(value) => setCardKind(value as ShopGateway["kind"])}
          />
          <Input required value={cardTitle} onChange={(e) => setCardTitle(e.target.value)} placeholder="عنوان کارت" aria-label="عنوان کارت" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
          <InputNumber stringMode value={cardNumber} onChange={(v) => setCardNumber(asText(v))} placeholder="شمارهٔ کارت (۱۶ رقم)" aria-label="شمارهٔ کارت (۱۶ رقم)" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
          <Input value={cardHolder} onChange={(e) => setCardHolder(e.target.value)} placeholder="نام صاحب کارت" aria-label="نام صاحب کارت" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        </div>
        <button type="submit" className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white">
          ثبت درگاه
        </button>
        <ul className="space-y-1 text-xs text-ink-dim">
          {gateways.map((g) => (
            <li key={g.id}>
              {g.title} — {g.is_enabled ? "فعال" : "غیرفعال"}
              {g.card_number_masked && ` · ${g.card_number_masked}`}
              {g.secret_configured && " · کلید تنظیم شده"}
            </li>
          ))}
        </ul>
        <p className="text-[11px] text-ink-dim">
          شمارهٔ کارت ماسک‌شده نمایش داده می‌شود؛ کلید خصوصی درگاه هرگز از سرور برنمی‌گردد.
        </p>
      </form>
    </div>
  );
}

/** فرم ادمین: پیشنهاد قیمت/محصول ← منتظر تأیید مالک. */
function AdminRequestForm({
  categories,
  products,
  onDone,
}: {
  categories: ShopCategory[];
  products: ShopProduct[];
  onDone: () => Promise<void>;
}) {
  const [kind, setKind] = useState("product_price");
  const [productId, setProductId] = useState<number | "">(products[0]?.id ?? "");
  const [newPrice, setNewPrice] = useState("");
  const [note, setNote] = useState("");

  return (
    <form
      className="glass-card space-y-3 p-5"
      onSubmit={(e) => {
        e.preventDefault();
        void (async () => {
          try {
            const payload =
              kind === "product_price"
                ? { product_id: Number(productId), price_rial: Number(newPrice || 0) }
                : { code: note, title: note, price_rial: Number(newPrice || 0) };
            await askChangeRequest(kind, payload);
            toast.success("درخواست ثبت شد — منتظر تأیید مالک");
            await onDone();
          } catch (err) {
            toast.error(err instanceof Error ? err.message : "ثبت درخواست ناموفق");
          }
        })();
      }}
    >
      <h3 className="text-sm font-bold">درخواست تغییر قیمت (ادمین) — منتظر تأیید مالک</h3>
      <div className="grid gap-2 sm:grid-cols-4">
        <Select
          aria-label="نوع تغییر قیمت"
          options={[
            { value: "product_price", label: "قیمت محصول" },
            { value: "membership_price", label: "قیمت اشتراک" },
            { value: "coach_fee", label: "شهریهٔ مربی" },
            { value: "program_fee", label: "هزینهٔ برنامه" },
          ]}
          value={kind}
          onChange={(value) => setKind(value)}
        />
        {kind === "product_price" ? (
          <Select
            aria-label="محصول"
            options={products.map((p) => ({ value: p.id, label: p.title }))}
            value={productId}
            onChange={(value) => setProductId(Number(value))}
          />
        ) : (
          <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="کد/عنوان" aria-label="کد/عنوان" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        )}
        <InputNumber stringMode value={newPrice} onChange={(v) => setNewPrice(asText(v))} placeholder="قیمت پیشنهادی (ریال)" aria-label="قیمت پیشنهادی (ریال)" className="focus-ring rounded-xl bg-surface/70 px-3 py-2 text-sm" />
        <button type="submit" className="focus-ring rounded-xl bg-accent/20 px-3 py-2 text-sm text-accent">
          ارسال برای تأیید
        </button>
      </div>
      {categories.length === 0 && <p className="text-[11px] text-ink-dim">دسته‌ای وجود ندارد؛ مالک باید ابتدا دسته بسازد.</p>}
    </form>
  );
}
