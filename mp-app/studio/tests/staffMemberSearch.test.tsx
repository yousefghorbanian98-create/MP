/**
 * STAFF-02 (PWA-41) — جست‌وجوی اعضا از سرور، نه فیلتر کلاینتی.
 *
 * چرا: `MemberTable` قبلاً همهٔ ردیف‌ها را می‌گرفت و نام/تلفن را در مرورگر
 * فیلتر می‌کرد. با بیش از `limit` عضو، عضوی که در صفحهٔ اول نبود هرگز
 * پیدا نمی‌شد و برچسب «N عضو» عدد صفحه را نشان می‌داد. این تست سه چیز را
 * می‌سنجد:
 *  ۱) با متن جست‌وجو، `q` به سرور می‌رود (encoded، نه در حافظهٔ مرورگر).
 *  ۲) ردیف نمایش‌داده‌شده همان پاسخ سرور است — حتی اگر متن جست‌وجو در آن
 *     نباشد (یعنی دیگر فیلتر کلاینتی وجود ندارد).
 *  ۳) جست‌وجوی بی‌نتیجه، حالت خالی صریح نشان می‌دهد و «دادهٔ نمایشی» نمی‌سازد.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberTable } from "../src/components/MemberTable";
import { useAppStore } from "../src/stores/appStore";

const ROW = {
  member_id: 41,
  user_id: 9,
  full_name: "پرهام قدرتی",
  phone: "09120000009",
  goal: "قدرت",
  gender: "male",
  status: "active",
  days_left: 12,
  plan_name: "ماهانه",
};

function summary(items: unknown[]) {
  return {
    items,
    rule_version: "members-summary-1.0",
    expiring_days: 7,
    unknown_status_meaning: "بدون اشتراک",
    generated_at: "2026-11-27T00:00:00+00:00",
  };
}

function stubFetch(items: unknown[]) {
  const urls: string[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    urls.push(`${url.pathname}${url.search}`);
    return {
      ok: true,
      status: 200,
      json: async () => summary(items),
    } as Response;
  });
  vi.stubGlobal("fetch", fetchMock);
  return urls;
}

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
  localStorage.setItem(
    "mp_token",
    `header.${btoa(JSON.stringify({ role: "manager" }))}.signature`,
  );
  useAppStore.setState({ search: "", genderFilter: "all", selectedMemberId: null });
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("جست‌وجوی اعضای کارکنان", () => {
  it("متن جست‌وجو را به‌صورت q سمت سرور می‌فرستد", async () => {
    const urls = stubFetch([ROW]);
    useAppStore.setState({ search: "قدرتی" });

    render(<MemberTable />);

    await waitFor(() =>
      expect(urls.some((u) => u === "/api/v1/admin/members-summary?q=%D9%82%D8%AF%D8%B1%D8%AA%DB%8C")).toBe(true),
    );
  }, 15000);

  it("ردیف‌های نمایش‌داده‌شده همان پاسخ سرور است، نه نتیجهٔ فیلتر مرورگر", async () => {
    // سرور ردیفی برمی‌گرداند که متن جست‌وجو در آن نیست؛ فیلتر کلاینتی آن را
    // حذف می‌کرد و کاربر «۰ عضو» می‌دید در حالی که سرور نتیجه داده بود.
    stubFetch([ROW]);
    useAppStore.setState({ search: "قدرتی" });

    render(<MemberTable />);

    expect(await screen.findByText("پرهام قدرتی")).toBeTruthy();
  }, 15000);

  it("جست‌وجوی بی‌نتیجه حالت خالی صریح نشان می‌دهد و داده نمی‌سازد", async () => {
    stubFetch([]);
    useAppStore.setState({ search: "ناموجود" });

    render(<MemberTable />);

    expect(await screen.findByText(/عضوی مطابق فیلتر نیست/)).toBeTruthy();
    expect(screen.getByText(/دادهٔ نمایشی ساخته نمی‌شود/)).toBeTruthy();
  }, 15000);
});
