import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Chat } from "../src/pages/Chat";
import { useAppStore } from "../src/stores/appStore";

/**
 * G8 — چت باید واقعاً پیام بفرستد، خوانده‌نشده را از سرور بخواند و
 * روی خطا متن کاربر را نگه دارد.
 */

const conv = {
  id: 7,
  member_id: 1,
  coach_id: 2,
  subject: "درد زانو",
  status: "open",
  last_message_at: "2026-11-15T10:00:00Z",
  created_at: "2026-11-14T09:00:00Z",
};

const incoming = {
  id: 11,
  conversation_id: 7,
  sender_id: 1,
  sender_role: "member",
  body: "سلام، زانویم درد می‌کند.",
  is_system: false,
  read_at: null,
  created_at: "2026-11-15T10:00:00Z",
};

const outgoing = {
  id: 12,
  conversation_id: 7,
  sender_id: 2,
  sender_role: "coach",
  body: "اسکوات را با پرس پا عوض کن.",
  is_system: false,
  read_at: null,
  created_at: "2026-11-15T10:05:00Z",
};

type Route = { match: RegExp; body: unknown; status?: number };

function stub(routes: Route[]) {
  const calls: string[] = [];
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method ?? "GET").toUpperCase();
    calls.push(`${method} ${url}`);
    const hit = routes.find((r) => r.match.test(`${method} ${url}`));
    if (!hit) throw new Error(`unexpected ${method} ${url}`);
    return new Response(JSON.stringify(hit.body), { status: hit.status ?? 200 });
  });
  vi.stubGlobal("fetch", fn);
  return calls;
}

beforeEach(() => {
  useAppStore.setState({ selectedMemberId: 1 });
  localStorage.setItem("mp_token", "t");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  useAppStore.setState({ selectedMemberId: null });
});

describe("Chat (G8)", () => {
  it("lists conversations and loads the first one's messages", async () => {
    stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [conv] },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [incoming], unread_count: 1, rule_version: "chat-1.0" },
      },
    ]);
    render(<Chat />);

    // فهرست و سرصفحه هر دو موضوع را نشان می‌دهند؛ مهم رسیدن پیام‌هاست.
    await waitFor(() => expect(screen.getByText(/زانویم درد می‌کند/)).toBeTruthy());
    expect(screen.getAllByText("درد زانو").length).toBeGreaterThan(0);
    expect(screen.getByText(/۱ خوانده‌نشده/)).toBeTruthy();
  });

  it("sends a message and shows it without a reload", async () => {
    stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [conv] },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [incoming], unread_count: 0, rule_version: "chat-1.0" },
      },
      { match: /POST .*\/chat\/conversations\/7\/messages(\?|$)/, body: outgoing },
    ]);
    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/زانویم درد می‌کند/)).toBeTruthy());

    const box = screen.getByPlaceholderText(/پیام…/);
    fireEvent.change(box, { target: { value: "اسکوات را عوض کنم؟" } });
    fireEvent.click(screen.getByRole("button", { name: "ارسال" }));

    await waitFor(() => expect(screen.getByText("اسکوات را با پرس پا عوض کن.")).toBeTruthy());
    expect((box as HTMLTextAreaElement).value).toBe("");
  });

  it("keeps the draft when sending fails", async () => {
    stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [conv] },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [], unread_count: 0, rule_version: "chat-1.0" },
      },
      {
        match: /POST .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { error: { code: "conversation_closed", message: "این گفتگو بسته شده است" } },
        status: 400,
      },
    ]);
    render(<Chat />);
    await waitFor(() => expect(screen.getAllByText("درد زانو").length).toBeGreaterThan(0));

    const box = screen.getByPlaceholderText(/پیام…/);
    fireEvent.change(box, { target: { value: "متن مهم" } });
    fireEvent.click(screen.getByRole("button", { name: "ارسال" }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect((box as HTMLTextAreaElement).value).toBe("متن مهم");
  });

  it("disables send on an empty or whitespace-only draft", async () => {
    stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [conv] },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [], unread_count: 0, rule_version: "chat-1.0" },
      },
    ]);
    render(<Chat />);
    await waitFor(() => expect(screen.getAllByText("درد زانو").length).toBeGreaterThan(0));

    const send = screen.getByRole("button", { name: "ارسال" }) as HTMLButtonElement;
    expect(send.disabled).toBe(true);

    fireEvent.change(screen.getByPlaceholderText(/پیام…/), { target: { value: "   " } });
    expect(send.disabled).toBe(true);

    fireEvent.change(screen.getByPlaceholderText(/پیام…/), { target: { value: "سلام" } });
    expect(send.disabled).toBe(false);
  });

  it("marks messages read and clears the counter", async () => {
    const calls = stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [conv] },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [incoming], unread_count: 1, rule_version: "chat-1.0" },
      },
      { match: /POST .*\/chat\/conversations\/7\/read(\?|$)/, body: { marked_read: 1, rule_version: "chat-1.0" } },
    ]);
    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/۱ خوانده‌نشده/)).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: /خوانده‌نشده — علامت بزن/ }));

    await waitFor(() => expect(screen.getByText(/۱ پیام خوانده‌شده علامت خورد/)).toBeTruthy());
    expect(calls.some((c) => c.startsWith("POST") && c.includes("/read"))).toBe(true);
  });

  it("asks for a member before starting a conversation", async () => {
    stub([{ match: /GET .*\/chat\/conversations(\?|$)/, body: [] }]);
    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/هیچ گفتگویی نیست/)).toBeTruthy());

    useAppStore.setState({ selectedMemberId: null });
    fireEvent.change(screen.getByPlaceholderText("موضوع گفتگوی جدید"), {
      target: { value: "سوال" },
    });
    fireEvent.click(screen.getByRole("button", { name: "شروع" }));

    await waitFor(() =>
      expect(screen.getByText(/اول یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy(),
    );
  });

  it("starts a conversation and selects it", async () => {
    stub([
      { match: /GET .*\/chat\/conversations(\?|$)/, body: [] },
      { match: /POST .*\/chat\/conversations(\?|$)/, body: conv },
      {
        match: /GET .*\/chat\/conversations\/7\/messages(\?|$)/,
        body: { conversation_id: 7, messages: [], unread_count: 0, rule_version: "chat-1.0" },
      },
    ]);
    render(<Chat />);
    await waitFor(() => expect(screen.getByText(/هیچ گفتگویی نیست/)).toBeTruthy());

    fireEvent.change(screen.getByPlaceholderText("موضوع گفتگوی جدید"), {
      target: { value: "درد زانو" },
    });
    fireEvent.click(screen.getByRole("button", { name: "شروع" }));

    await waitFor(() => expect(screen.getByText(/گفتگوی جدید ساخته شد/)).toBeTruthy());
  });
});
