/**
 * دستگاه‌های فعال — فاز ۴ (QF-01)، سمت Studio.
 *
 * تست با `fetch` واقعیِ stub‌شده کار می‌کند تا مسیرهای تازه (`GET /auth/sessions`
 * و `DELETE /auth/sessions/{id}`) در URL دیده شوند؛ ماک‌کردن ماژول api این
 * شکاف را می‌پوشاند.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeviceSessions } from "../src/components/DeviceSessions";
import { clearSession, storeTokenPair } from "../src/lib/session";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

interface Call {
  method: string;
  path: string;
  authorization: string | null;
}

const ROWS = [
  {
    id: 9,
    device_info: "iPhone 15 — Safari",
    created_at: "2026-11-18T08:00:00+00:00",
    expires_at: "2026-12-18T08:00:00+00:00",
    current: true,
  },
  {
    id: 7,
    device_info: "Pixel 7 — Chrome",
    created_at: "2026-11-17T08:00:00+00:00",
    expires_at: "2026-12-17T08:00:00+00:00",
    current: false,
  },
];

function stubFetch(handler: (call: Call) => Response) {
  const calls: Call[] = [];
  const mock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const call: Call = {
      method: (init?.method ?? "GET").toUpperCase(),
      path: new URL(raw, window.location.href).pathname,
      authorization: new Headers(init?.headers).get("Authorization"),
    };
    calls.push(call);
    return handler(call);
  });
  vi.stubGlobal("fetch", mock);
  return calls;
}

beforeEach(() => {
  localStorage.clear();
  storeTokenPair({ access_token: "current-access", refresh_token: "current-refresh" });
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSession();
});

describe("دستگاه‌های فعال (فاز ۴)", () => {
  it("فهرست را با توکن از GET /auth/sessions می‌خواند و نشست جاری را علامت می‌زند", async () => {
    const calls = stubFetch(() => reply(200, ROWS));
    render(<DeviceSessions />);

    expect(await screen.findByText("iPhone 15 — Safari")).toBeTruthy();
    expect(screen.getByText("Pixel 7 — Chrome")).toBeTruthy();
    expect(screen.getByText("این دستگاه")).toBeTruthy();
    expect(calls[0]?.path).toBe("/api/v1/auth/sessions");
    expect(calls[0]?.method).toBe("GET");
    expect(calls[0]?.authorization).toBe("Bearer current-access");
    // نشست جاری دکمهٔ ابطال ندارد؛ فقط دستگاه دیگر دارد.
    expect(screen.getAllByText("خروج دستگاه")).toHaveLength(1);
  });

  it("ابطال دستگاه دیگر را با DELETE می‌فرستد و فهرست را از سرور بازخوانی می‌کند", async () => {
    let rows = ROWS;
    const calls = stubFetch((call) => {
      if (call.method === "DELETE" && call.path === "/api/v1/auth/sessions/7") {
        rows = ROWS.filter((r) => r.id !== 7);
        return reply(200, { status: "revoked", session_id: 7 });
      }
      return reply(200, rows);
    });
    render(<DeviceSessions />);

    fireEvent.click(await screen.findByText("خروج دستگاه"));
    fireEvent.click(await screen.findByText("خارج کن"));

    await waitFor(() => expect(screen.queryByText("Pixel 7 — Chrome")).toBeNull());
    expect(calls.filter((c) => c.method === "DELETE")).toEqual([
      { method: "DELETE", path: "/api/v1/auth/sessions/7", authorization: "Bearer current-access" },
    ]);
    // پس از ابطال، فهرست دوباره از سرور خوانده شده (نه حذف خوش‌بینانه در UI).
    expect(calls.filter((c) => c.method === "GET").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("iPhone 15 — Safari")).toBeTruthy();
  });

  it("خطای سرور را بدون ساختن ردیف جعلی نشان می‌دهد", async () => {
    stubFetch(() =>
      reply(500, { error: { message: "خواندن نشست‌ها ناموفق بود" } }),
    );
    render(<DeviceSessions />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("خواندن نشست‌ها ناموفق بود");
    expect(screen.queryByText("دستگاه ناشناس")).toBeNull();
  });

  it("ناوبری نشست (۴۰۱) را به پیام ورود دوباره ترجمه می‌کند", async () => {
    stubFetch(() => reply(401, { error: { message: "توکن منقضی" } }));
    render(<DeviceSessions />);

    expect(
      await screen.findByText("نشست معتبر نیست؛ با کد یک‌بارمصرف دوباره وارد شوید."),
    ).toBeTruthy();
  });
});
