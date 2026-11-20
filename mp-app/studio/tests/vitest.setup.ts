/**
 * بستر jsdom برای همهٔ تست‌ها.
 *
 * jsdom کلاس `ResizeObserver` ندارد. کتابخانهٔ نمودار (recharts) برای
 * `ResponsiveContainer` به آن نیاز دارد؛ بدون این پلی‌فیل، هر صفحه‌ای که نمودار
 * را رندر کند در CI (با `CI=true`) خطای خارج‌ازتست می‌دهد. این فقط محیط تست است
 * و هیچ گیتی را شُل نمی‌کند.
 */
if (typeof globalThis.ResizeObserver === "undefined") {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  Object.defineProperty(globalThis, "ResizeObserver", {
    value: ResizeObserverStub,
    writable: true,
    configurable: true,
  });
}
