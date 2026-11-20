/**
 * ماتریس مجوز شخصی ادمین — فاز ۵ (QF-03/QF-04)، سمت Studio.
 *
 * تست با `fetch` واقعیِ stub‌شده کار می‌کند تا مسیر، متد و بدنهٔ درخواست‌ها
 * دیده شوند و ادعای «سرور منبع حقیقت است» قابل بازرسی باشد:
 *   • بدون بازخوانی بعد از POST/DELETE هیچ ردیفی در UI اضافه/حذف نمی‌شود.
 *   • برای نقش غیرمالک هیچ درخواستی فرستاده نمی‌شود.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AdminPermissions } from "../src/components/AdminPermissions";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function tokenFor(role: string): string {
  return `header.${btoa(JSON.stringify({ role }))}.signature`;
}

interface Call {
  method: string;
  path: string;
  body: string | null;
}

const USERS = [
  { id: 1, phone: "09120000001", full_name: "مالک", role: "super_admin", is_active: true, created_at: null },
  { id: 5, phone: "09120000005", full_name: "ادمین فروش", role: "admin", is_active: true, created_at: null },
];

const KEYS = [
  { key: "finance.write", description: "تأیید دستی پرداخت" },
  { key: "reports.confidential", description: "گزارش محرمانه" },
];

function grant(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: 11,
    user_id: 5,
    permission: "finance.write",
    note: "",
    granted_by: 1,
    granted_at: "2026-11-19T08:00:00+00:00",
    expires_at: "2026-11-26T08:00:00+00:00",
    revoked_at: null,
    revoked_by: null,
    active: true,
    status: "active",
    ...overrides,
  };
}

function stubApi(state: { grants: unknown[]; keysStatus?: number }) {
  const calls: Call[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    const method = (init?.method ?? "GET").toUpperCase();
    calls.push({
      method,
      path: `${url.pathname}${url.search}`,
      body: typeof init?.body === "string" ? init.body : null,
    });

    if (url.pathname === "/api/v1/admin/users") return reply(200, USERS);
    if (url.pathname === "/api/v1/admin/permissions/known") {
      if (state.keysStatus === 403) {
        return reply(403, { error: { message: "فقط مالک سیستم (super_admin)" } });
      }
      return reply(200, KEYS);
    }
    if (url.pathname === "/api/v1/admin/permissions" && method === "GET") {
      return reply(200, state.grants);
    }
    if (url.pathname === "/api/v1/admin/permissions" && method === "POST") {
      const created = grant({ id: 12, status: "active", note: "از UI" });
      state.grants = [...state.grants, created];
      return reply(200, created);
    }
    if (url.pathname.startsWith("/api/v1/admin/permissions/") && method === "DELETE") {
      state.grants = state.grants.map((row) =>
        (row as { id: number }).id === 11 ? grant({ status: "revoked", active: false, revoked_at: "2026-11-19T09:00:00+00:00" }) : row,
      );
      return reply(200, { status: "revoked", grant_id: 11 });
    }
    throw new Error(`Unexpected request: ${method} ${url.pathname}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

// jsdom این API را ندارد و antd (Table/Select) هنگام mount صدایش می‌زند.
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
  localStorage.setItem("mp_token", tokenFor("super_admin"));
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("مجوز شخصی ادمین", () => {
  it("مجوزهای موجود را با وضعیت مؤثر از سرور می‌خواند و کاربر مالک را در فهرست هدف نمی‌آورد", async () => {
    const state = { grants: [grant(), grant({ id: 12, permission: "reports.confidential", status: "expired", active: false })] };
    const calls = stubApi(state);

    render(<AdminPermissions />);

    expect(await screen.findByText("finance.write")).toBeTruthy();
    expect(screen.getByText("reports.confidential")).toBeTruthy();
    expect(screen.getByText("فعال")).toBeTruthy();
    expect(screen.getByText("منقضی")).toBeTruthy();
    expect(calls.some((c) => c.path === "/api/v1/admin/permissions?user_id=5")).toBe(true);
    // مالک در گزینه‌های هدف نیست (مجوز برای او معنا ندارد) — فقط ادمین.
    expect(screen.queryByText("مالک — super_admin")).toBeNull();
  });

  it("اعطای مجوز را با کلید، مدت و شناسهٔ کاربر می‌فرستد و بعد از آن از سرور بازخوانی می‌کند", async () => {
    const state = { grants: [] as unknown[] };
    const calls = stubApi(state);

    render(<AdminPermissions />);
    // اولین کاربر غیرمالک به‌طور پیش‌فرض انتخاب است؛ فهرست از سرور آمده.
    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/v1/admin/permissions?user_id=5")).toBe(true),
    );

    // انتخاب کلید از Select کتابخانه‌ای antd (نه کنترل دست‌ساز).
    fireEvent.mouseDown(screen.getByTestId("permission-key").querySelector(".ant-select-selector")!);
    // گزینهٔ داخل dropdown با کلاس ant-select-item انتخاب می‌شود (کلید در فهرست هم دیده می‌شود).
    const option = await waitFor(() => {
      const found = document.querySelector(".ant-select-item-option[title='finance.write']");
      if (!found) throw new Error("option not open");
      return found as HTMLElement;
    });
    fireEvent.click(option);

    fireEvent.click(screen.getByRole("button", { name: "اعطای مجوز" }));

    await waitFor(() =>
      expect(calls.some((c) => c.method === "POST" && c.path === "/api/v1/admin/permissions")).toBe(true),
    );
    const post = calls.find((c) => c.method === "POST")!;
    expect(JSON.parse(post.body!)).toEqual({
      user_id: 5,
      permission: "finance.write",
      expires_in_hours: null,
      note: "",
    });
    // بازخوانی پس از اعطا: ردیف از پاسخ سرور آمده، نه از state محلی.
    await waitFor(() =>
      expect(calls.filter((c) => c.path === "/api/v1/admin/permissions?user_id=5").length).toBeGreaterThanOrEqual(2),
    );
    expect(await screen.findByText("فعال")).toBeTruthy();
  });

  it("سلب مجوز را با DELETE می‌فرستد و وضعیت تازه را از سرور می‌گیرد", async () => {
    const state = { grants: [grant()] as unknown[] };
    const calls = stubApi(state);

    render(<AdminPermissions />);
    fireEvent.click(await screen.findByRole("button", { name: "سلب" }));
    fireEvent.click(await screen.findByRole("button", { name: "سلب کن" }));

    await waitFor(() =>
      expect(calls.some((c) => c.method === "DELETE" && c.path === "/api/v1/admin/permissions/11")).toBe(true),
    );
    expect(await screen.findByText("سلب‌شده")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "سلب" })).toBeNull();
  });

  it("برای غیرمالک هیچ درخواستی نمی‌فرستد و بخش را نشان نمی‌دهد", async () => {
    localStorage.setItem("mp_token", tokenFor("admin"));
    const calls = stubApi({ grants: [] });

    const { container } = render(<AdminPermissions />);

    await waitFor(() => expect(calls).toEqual([]));
    expect(container.textContent).toBe("");
    expect(screen.queryByRole("button", { name: "اعطای مجوز" })).toBeNull();
  });
});
