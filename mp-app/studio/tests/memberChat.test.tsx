/**
 * MEM-14 / PWA-3D — چت عضو.
 *
 * قفل‌ها:
 * - فهرست از `GET /chat/conversations` می‌آید و کلاینت `member_id` نمی‌فرستد
 *   (دامنه سمت سرور است: `chat_service.py:26-44`).
 * - پیام‌ها فقط از پاسخ سرور رندر می‌شوند؛ ارسال بدون بازخوانی نمی‌تواند پیام بسازد.
 * - خوانده‌شدن با تأیید سرور و بازخوانی اعمال می‌شود (تعداد از `marked_read`).
 * - `status=closed` ⇒ ورودی و ارسال غیرفعال با دلیل سرور.
 * - هیچ WebSocket/realtime ساخته نمی‌شود؛ صفحه خودش همین را می‌گوید.
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberChat } from "../src/components/MemberChat";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const conversation = (overrides: Record<string, unknown> = {}) => ({
  id: 4,
  member_id: 17,
  coach_id: 9,
  subject: "برنامهٔ تمرین",
  status: "open",
  last_message_at: "2026-11-27T08:00:00Z",
  created_at: "2026-11-26T08:00:00Z",
  ...overrides,
});

const message = (overrides: Record<string, unknown> = {}) => ({
  id: 41,
  conversation_id: 4,
  sender_id: 9,
  sender_role: "coach",
  body: "ست چهارم را سبک‌تر بزن.",
  is_system: false,
  read_at: null,
  created_at: "2026-11-27T08:00:00Z",
  ...overrides,
});

type Call = { method: string; path: string; search: string; body?: string };

function installApi(handler: (call: Call) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const call: Call = {
        method: (init?.method ?? "GET").toUpperCase(),
        path: url.pathname,
        search: url.search,
        body: typeof init?.body === "string" ? init.body : undefined,
      };
      calls.push(call);
      return handler(call);
    }),
  );
  return calls;
}

const thread = (messages: unknown[] = [message()], unread = 1) => ({
  conversation_id: 4,
  messages,
  unread_count: unread,
  rule_version: "chat-1.0",
});

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("member chat (MEM-14)", () => {
  it("lists the server's conversations without sending a member_id filter", async () => {
    const calls = installApi(({ path }) => {
      if (path === "/api/v1/chat/conversations") return reply(200, [conversation()]);
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberChat />);

    expect(await screen.findByText("برنامهٔ تمرین")).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/chat\/conversations/)).toBeTruthy();
    expect(calls[0]).toEqual(
      expect.objectContaining({ method: "GET", path: "/api/v1/chat/conversations", search: "" }),
    );
  });

  it("renders messages only from the server and states there is no realtime", async () => {
    installApi(({ path, method }) => {
      if (path === "/api/v1/chat/conversations" && method === "GET") return reply(200, [conversation()]);
      if (path === "/api/v1/chat/conversations/4/messages" && method === "GET")
        return reply(200, thread([message({ id: 41, body: "ست چهارم سبک‌تر." })]));
      if (path === "/api/v1/chat/conversations/4/read" && method === "POST")
        return reply(200, { marked_read: 1, rule_version: "chat-1.0" });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberChat />);
    fireEvent.click(await screen.findByText("برنامهٔ تمرین"));

    expect(await screen.findByText("ست چهارم سبک‌تر.")).toBeTruthy();
    expect(screen.getByText(/realtime\/WebSocket\s*ندارد/)).toBeTruthy();
    expect(container.querySelector('[data-message-id="41"]')).toBeTruthy();
    expect(screen.getByText(/قاعدهٔ سرور: chat-1\.0/)).toBeTruthy();
  });

  it("marks read through the server and reports the server's own count", async () => {
    const calls = installApi(({ path, method }) => {
      if (path === "/api/v1/chat/conversations" && method === "GET") return reply(200, [conversation()]);
      if (path === "/api/v1/chat/conversations/4/messages" && method === "GET")
        return reply(200, thread());
      if (path === "/api/v1/chat/conversations/4/read" && method === "POST")
        return reply(200, { marked_read: 2, rule_version: "chat-1.0" });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    render(<MemberChat />);
    fireEvent.click(await screen.findByText("برنامهٔ تمرین"));

    expect(await screen.findByText(/سرور ۲ پیام را خوانده‌شده ثبت کرد/)).toBeTruthy();
    const messageReads = calls.filter(
      (c) => c.method === "GET" && c.path === "/api/v1/chat/conversations/4/messages",
    );
    // یک خواندن اولیه + یک بازخوانی پس از تأیید خوانده‌شدن.
    expect(messageReads.length).toBe(2);
  });

  it("does not invent a sent message: it re-reads and shows only what the server stores", async () => {
    const stored: unknown[] = [message()];
    const calls = installApi(({ path, method, body }) => {
      if (path === "/api/v1/chat/conversations" && method === "GET") return reply(200, [conversation()]);
      if (path === "/api/v1/chat/conversations/4/messages" && method === "GET")
        return reply(200, thread(stored, 0));
      if (path === "/api/v1/chat/conversations/4/read" && method === "POST")
        return reply(200, { marked_read: 0, rule_version: "chat-1.0" });
      if (path === "/api/v1/chat/conversations/4/messages" && method === "POST") {
        // سرور پیام را می‌پذیرد ولی در این سناریو **ذخیره نمی‌کند**.
        expect(body).toContain("سلام مربی");
        return reply(201, message({ id: 99, sender_role: "member", body: "سلام مربی" }));
      }
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberChat />);
    fireEvent.click(await screen.findByText("برنامهٔ تمرین"));
    await screen.findByText("ست چهارم را سبک‌تر بزن.");

    fireEvent.change(container.querySelector("textarea") as HTMLTextAreaElement, {
      target: { value: "سلام مربی" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ارسال" }));

    await waitFor(() =>
      expect(calls.filter((c) => c.method === "POST" && c.path.endsWith("/messages")).length).toBe(1),
    );
    // پاسخ 201 آمد، ولی سرور در بازخوانی همان پیام قدیمی را می‌دهد ⇒ پیام تازه نمایش داده نمی‌شود.
    await waitFor(() =>
      expect(
        calls.filter((c) => c.method === "GET" && c.path === "/api/v1/chat/conversations/4/messages").length,
      ).toBeGreaterThanOrEqual(3),
    );
    expect(container.querySelector('[data-message-id="99"]')).toBeNull();
  });

  it("surfaces the server's refusal and keeps the draft when the conversation is closed", async () => {
    installApi(({ path, method }) => {
      if (path === "/api/v1/chat/conversations" && method === "GET")
        return reply(200, [conversation({ status: "closed" })]);
      if (path === "/api/v1/chat/conversations/4/messages" && method === "GET")
        return reply(200, thread([], 0));
      // خواندن گفتگوی بسته از نظر سرور مجاز است؛ فقط ارسال پیام رد می‌شود.
      if (path === "/api/v1/chat/conversations/4/read" && method === "POST")
        return reply(200, { marked_read: 0, rule_version: "chat-1.0" });
      throw new Error(`unexpected API call: ${method} ${path}`);
    });

    const { container } = render(<MemberChat />);
    fireEvent.click(await screen.findByText("برنامهٔ تمرین"));

    expect(await screen.findByText(/این گفتگو بسته است؛ سرور پیام تازه را رد می‌کند/)).toBeTruthy();
    expect((container.querySelector("textarea") as HTMLTextAreaElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "ارسال" }) as HTMLButtonElement).disabled).toBe(true);
    expect(container.querySelector('[data-thread-meta]')?.textContent).toMatch(/خوانده‌نشده: ۰/);
  });

  it("fails closed on 403 with no conversations and no messages", async () => {
    installApi(({ path }) =>
      path === "/api/v1/chat/conversations"
        ? reply(403, { error: { message: "این گفتگو متعلق به شما نیست" } })
        : reply(404, {}),
    );

    const { container } = render(<MemberChat />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/این گفتگو متعلق به شما نیست/);
    expect(container.querySelectorAll("[data-conversation-id]").length).toBe(0);
    expect(container.querySelectorAll("[data-message-id]").length).toBe(0);
  });
});
