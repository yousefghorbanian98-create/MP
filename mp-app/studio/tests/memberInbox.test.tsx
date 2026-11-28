/**
 * MEM-15 / PWA-3E — جعبهٔ اعلان عضو.
 *
 * قفل‌ها:
 * - فهرست از `GET /notifications/member/{id}` می‌آید و شناسهٔ عضو از پروفایل سرور
 *   (`/auth/me`) خوانده می‌شود، نه از URL یا ورودی کاربر.
 * - کانال هر ردیف نمایش داده می‌شود و `inapp` هرگز به «پیامک/push تحویل شد» ترجمه نمی‌شود.
 * - «خوانده شد» فقط پس از تأیید سرور و **بازخوانی** فهرست اعمال می‌شود.
 * - هیچ مسیر ارسال اعلان (`POST /notifications`) صدا زده نمی‌شود.
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberInbox } from "../src/components/MemberInbox";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const note = (overrides: Record<string, unknown> = {}) => ({
  id: 5,
  member_id: 17,
  channel: "inapp",
  title: "تمدید اشتراک",
  body: "اشتراک شما ۳ روز دیگر تمام می‌شود.",
  kind: "renewal",
  read_at: null,
  created_at: "2026-11-27T07:00:00Z",
  ...overrides,
});

type Call = { method: string; path: string };

function installApi(handler: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const call = { method: (init?.method ?? "GET").toUpperCase(), path: url.pathname };
      calls.push(call);
      return handler(call);
    }),
  );
  return calls;
}

const me = {
  id: 17,
  user_id: 31,
  full_name: "عضو آزمون",
  phone: "09120000000",
  role: "member",
  goal: "",
  gender: "",
  height_cm: null,
  constraints: "[]",
};

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("member inbox (MEM-15)", () => {
  it("lists the server's notifications with channel, kind and a visible source", async () => {
    const calls = installApi(({ path }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      if (path === "/api/v1/notifications/member/17") return reply(200, [note()]);
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberInbox />);

    expect(await screen.findByText("تمدید اشتراک")).toBeTruthy();
    expect(container.querySelector('[data-channel="inapp"]')).toBeTruthy();
    expect(screen.getByText(/کانال: درون‌برنامه‌ای/)).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/notifications\/member\/\{member_id\}/)).toBeTruthy();
    // شناسهٔ عضو از پروفایل سرور می‌آید.
    expect(calls.some((c) => c.path === "/api/v1/members/me")).toBe(true);
    expect(calls.some((c) => c.method !== "GET")).toBe(false);
  });

  it("never claims push or SMS delivery when the channel is inapp", async () => {
    installApi(({ path }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      if (path === "/api/v1/notifications/member/17") return reply(200, [note()]);
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberInbox />);
    await screen.findByText("تمدید اشتراک");

    expect(screen.getByText(/به معنای ارسال\s+push\/SMS یا تحویل و مشاهدهٔ آن روی دستگاه نیست/)).toBeTruthy();
    expect(screen.queryByText(/پیامک ارسال شد/)).toBeNull();
    expect(screen.queryByText(/تحویل شد ✅/)).toBeNull();
  });

  it("marks a notification read only after the server confirms, then re-reads the list", async () => {
    let readAccepted = false;
    const calls = installApi(({ path, method }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      if (path === "/api/v1/notifications/member/17")
        return reply(200, [note({ read_at: readAccepted ? "2026-11-27T09:00:00Z" : null })]);
      if (path === "/api/v1/notifications/5/read" && method === "POST") {
        readAccepted = true;
        return reply(200, note({ read_at: "2026-11-27T09:00:00Z" }));
      }
      throw new Error(`unexpected API call: ${method} ${path}`);
    },);

    const { container } = render(<MemberInbox />);
    await screen.findByText("تمدید اشتراک");
    expect(container.querySelector('[data-read="no"]')).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /علامت‌گذاری/ }));

    await waitFor(() => expect(container.querySelector('[data-read="yes"]')).toBeTruthy());
    const reads = calls.filter((c) => c.path === "/api/v1/notifications/member/17");
    // یک خواندن اولیه + یک بازخوانی پس از تأیید سرور.
    expect(reads.length).toBe(2);
    expect(calls.some((c) => c.method === "POST" && c.path === "/api/v1/notifications/5/read")).toBe(true);
  });

  it("keeps the row unread when the server refuses the read call", async () => {
    installApi(({ path, method }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      if (path === "/api/v1/notifications/member/17") return reply(200, [note()]);
      if (path === "/api/v1/notifications/5/read" && method === "POST")
        return reply(404, { error: { message: "اعلان یافت نشد" } });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberInbox />);
    await screen.findByText("تمدید اشتراک");
    fireEvent.click(screen.getByRole("button", { name: /علامت‌گذاری/ }));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(container.querySelector('[data-read="no"]')).toBeTruthy();
  });

  it("shows an empty state that distinguishes 'no notification' from 'no SMS sent'", async () => {
    installApi(({ path }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      if (path === "/api/v1/notifications/member/17") return reply(200, []);
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberInbox />);

    expect(await screen.findByText(/هیچ اعلانی برای این حساب برنگرداند/)).toBeTruthy();
    expect(container.querySelectorAll("[data-notification-id]").length).toBe(0);
    expect(container.querySelector("[data-unread-count]")?.getAttribute("data-unread-count")).toBe("0");
  });

  it("never sends a notification and fails closed on 403", async () => {
    const calls = installApi(({ path }) => {
      if (path === "/api/v1/members/me") return reply(200, me);
      return reply(403, { error: { message: "دسترسی ندارید" } });
    });

    const { container } = render(<MemberInbox />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/دسترسی به اعلان‌های این حساب مجاز نیست/);
    expect(container.querySelectorAll("[data-notification-id]").length).toBe(0);
    expect(calls.some((c) => c.method === "POST")).toBe(false);
    expect(calls.some((c) => c.path === "/api/v1/notifications")).toBe(false);
  });
});
