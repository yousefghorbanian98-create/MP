/**
 * امنیت حساب عضو (MEM-03 / PWA-32) — کارت نشست‌ها و «خروج از همهٔ دستگاه‌ها».
 *
 * این تست با `fetch` واقعیِ stub‌شده کار می‌کند تا مسیرهای تازه در URL دیده
 * شوند و ادعای «سرور انجام داد» بدون فراخوانی واقعی قابل قبول نباشد.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../src/auth/AuthContext";
import { MemberSecurity } from "../src/components/MemberSecurity";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  clearSession,
  storeTokenPair,
} from "../src/lib/session";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function jwtFor(userId: number, role = "member"): string {
  return `header.${btoa(JSON.stringify({ sub: String(userId), role }))}.signature`;
}

const TOKEN = jwtFor(41);

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

/** AuthProvider restores the session through /members/me; every other path is the test's business. */
function baseHandler(overrides: (call: Call) => Response | null) {
  return (call: Call): Response => {
    if (call.path === "/api/v1/members/me") {
      return reply(200, { id: 17, user_id: 41, role: "member", phone: "09121234567" });
    }
    const overridden = overrides(call);
    if (overridden) return overridden;
    throw new Error(`unexpected request: ${call.method} ${call.path}`);
  };
}

function renderSecurity() {
  return render(
    <AuthProvider>
      <MemberSecurity />
    </AuthProvider>,
  );
}

beforeEach(() => {
  localStorage.clear();
  storeTokenPair({ access_token: TOKEN, refresh_token: "member-41-refresh" });
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSession();
});

describe("امنیت حساب عضو (MEM-03)", () => {
  it("lists the member's own sessions from GET /auth/sessions", async () => {
    const calls = stubFetch(
      baseHandler((call) =>
        call.path === "/api/v1/auth/sessions" ? reply(200, ROWS) : null,
      ),
    );

    renderSecurity();

    expect(await screen.findByText("iPhone 15 — Safari")).toBeTruthy();
    expect(screen.getByText("Pixel 7 — Chrome")).toBeTruthy();
    const sessionCall = calls.find((call) => call.path === "/api/v1/auth/sessions");
    expect(sessionCall?.method).toBe("GET");
    expect(sessionCall?.authorization).toBe(`Bearer ${TOKEN}`);
  });

  it("only signs out everywhere after the server confirms, then clears local credentials", async () => {
    const calls = stubFetch(
      baseHandler((call) => {
        if (call.path === "/api/v1/auth/sessions") return reply(200, ROWS);
        if (call.path === "/api/v1/auth/logout-all") {
          return reply(200, { status: "all_sessions_revoked" });
        }
        return null;
      }),
    );

    renderSecurity();
    await screen.findByText("Pixel 7 — Chrome");
    fireEvent.click(screen.getByRole("button", { name: "خروج از همهٔ دستگاه‌ها" }));
    fireEvent.click(await screen.findByText("خارج شو"));

    await waitFor(() => expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull());
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
    const logoutAll = calls.filter((call) => call.path === "/api/v1/auth/logout-all");
    expect(logoutAll).toHaveLength(1);
    expect(logoutAll[0].method).toBe("POST");
    expect(logoutAll[0].authorization).toBe(`Bearer ${TOKEN}`);
  });

  it("keeps the session and reports failure when the server does not confirm logout-all", async () => {
    stubFetch(
      baseHandler((call) => {
        if (call.path === "/api/v1/auth/sessions") return reply(200, ROWS);
        if (call.path === "/api/v1/auth/logout-all") {
          return reply(503, { error: { message: "سرویس نشست در دسترس نیست" } });
        }
        return null;
      }),
    );

    renderSecurity();
    await screen.findByText("Pixel 7 — Chrome");
    fireEvent.click(screen.getByRole("button", { name: "خروج از همهٔ دستگاه‌ها" }));
    fireEvent.click(await screen.findByText("خارج شو"));

    expect((await screen.findByRole("alert")).textContent).toContain(
      "سرور خروج از همهٔ دستگاه‌ها را تأیید نکرد",
    );
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe(TOKEN);
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("member-41-refresh");
  });
});
