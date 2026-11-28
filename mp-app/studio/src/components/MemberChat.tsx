/**
 * MEM-14 / PWA-3D — چت عضو با مربی.
 *
 * معیار پذیرش TODO (`TODO-PWA-RELEASE-2026-11-23.fa.md:242`): «طرفین مجاز،
 * ownership، retry/duplicate، empty state و disconnect؛ پیام عضو دیگر یا متن
 * ساختگی نمایش داده نشود.»
 *
 * قرارداد واقعی (با `grep -n`):
 * - `modules/notification/chat_router.py:24-53` → پنج مسیر: فهرست گفتگوها، شروع
 *   گفتگو، پیام‌های گفتگو، ارسال پیام، علامت خوانده‌شده.
 * - `chat_service.py:26-44` (`_load_conversation`) → عضو فقط گفتگوی خودش را
 *   می‌بیند؛ در غیر این صورت `ForbiddenError` «این گفتگو متعلق به شما نیست».
 * - `chat_service.py:99-125` → فرستنده از توکن، پیام خالی رد، سقف طول، گفتگوی
 *   بسته رد (`conversation_closed`).
 * - `chat_service.py:127-148` → پیام‌ها `id desc` گرفته و معکوس می‌شوند (صعودی)،
 *   `unread_count` و `rule_version` از سرور.
 * - `chat_service.py:150-169` → `read` فقط پیام‌های طرف مقابلِ خوانده‌نشده را
 *   علامت می‌زند و تعداد واقعی را برمی‌گرداند.
 *
 * قاعده‌ها:
 * - هیچ realtime/WebSocket ادعا نمی‌شود: سرور فقط REST دارد؛ صفحه می‌گوید پیام
 *   تازه با «بازخوانی» می‌آید. ارسال هم بعد از موفقیت **بازخوانی** می‌کند و پیام
 *   فقط از پاسخ سرور نمایش داده می‌شود (بدون افزودن خوش‌بینانه).
 * - `status=closed` ⇒ ورودی پیام غیرفعال با دلیل؛ تصمیم بستن سمت سرور است.
 * - ۴۰۳ ⇒ fail-closed، صفر ردیف، صفر پیام.
 */
import { Button, Empty, Input, Spin, Tag } from "antd";
import { useCallback, useEffect, useState } from "react";
import { toDate } from "../lib/clock";
import {
  ApiError,
  ForbiddenError,
  fetchConversations,
  fetchMessages,
  markConversationRead,
  sendMessage,
  type ChatConversation,
  type ChatMessages,
} from "../lib/api";

const SOURCE = "منبع: GET /api/v1/chat/conversations";

function stamp(iso: string | null): string {
  if (!iso) return "بدون زمان";
  const date = toDate(iso);
  if (Number.isNaN(date.getTime())) return "زمان نامعتبر";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return error.message;
  if (error instanceof ApiError) return error.message;
  return "چت از سرور دریافت نشد";
}

export function MemberChat() {
  const [conversations, setConversations] = useState<ChatConversation[] | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [thread, setThread] = useState<ChatMessages | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadConversations = useCallback(async (signal?: AbortSignal) => {
    try {
      const rows = await fetchConversations(undefined, undefined, signal);
      setConversations(Array.isArray(rows) ? rows : []);
      setError(null);
    } catch (err) {
      setConversations([]);
      setError(failureMessage(err));
    }
  }, []);

  const loadThread = useCallback(
    async (conversationId: number, signal?: AbortSignal, markRead = false) => {
      try {
        const data = await fetchMessages(conversationId, undefined, signal);
        setThread(data);
        setError(null);
        if (markRead) {
          // خوانده‌شدن از سرور تأیید و سپس بازخوانی می‌شود؛ از کلیک ساخته نمی‌شود.
          const result = await markConversationRead(conversationId);
          const fresh = await fetchMessages(conversationId, undefined, signal);
          setThread(fresh);
          setNotice(`سرور ${result.marked_read.toLocaleString("fa-IR")} پیام را خوانده‌شده ثبت کرد.`);
        }
      } catch (err) {
        setThread(null);
        setError(failureMessage(err));
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadConversations(controller.signal);
    return () => controller.abort();
  }, [loadConversations]);

  const active = (conversations ?? []).find((row) => row.id === activeId) ?? null;

  async function select(row: ChatConversation) {
    setActiveId(row.id);
    setThread(null);
    setDraft("");
    setNotice(null);
    await loadThread(row.id, undefined, true);
  }

  async function submit() {
    const body = draft.trim();
    if (activeId === null || body === "") return;
    setBusy(true);
    setError(null);
    try {
      await sendMessage(activeId, body);
      setDraft("");
      // بازخوانی از سرور: پیام فقط اگر واقعاً ثبت شده باشد دیده می‌شود.
      await loadThread(activeId);
    } catch (err) {
      setError(failureMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const heading = (
    <h3 id="member-chat-title" className="text-base font-semibold">
      گفتگو با مربی
    </h3>
  );

  if (error && conversations !== null && conversations.length === 0) {
    return (
      <section aria-labelledby="member-chat-title" className="space-y-3">
        {heading}
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      </section>
    );
  }

  if (conversations === null) {
    return (
      <section aria-labelledby="member-chat-title" className="space-y-3">
        {heading}
        <Spin /> <span className="text-sm text-ink-dim">در حال دریافت گفتگوها از سرور…</span>
      </section>
    );
  }

  return (
    <section aria-labelledby="member-chat-title" className="space-y-4">
      <div>
        {heading}
        <p className="mt-1 text-xs text-ink-dim">
          پیام‌ها ذخیره‌شده روی سرورند و فقط با «بازخوانی» تازه می‌شوند؛ این صفحه realtime/WebSocket
          ندارد و ادعای رسیدن فوری پیام نمی‌کند.
        </p>
        <p className="text-[11px] text-ink-dim">{SOURCE}</p>
      </div>

      {error ? (
        <p role="alert" className="text-xs text-danger" data-chat-error>
          {error}
        </p>
      ) : null}
      {notice ? (
        <p role="status" className="text-[11px] text-ink-dim" data-chat-notice>
          {notice}
        </p>
      ) : null}

      {conversations.length === 0 ? (
        <Empty description="سرور هیچ گفتگویی برای این حساب برنگرداند — یعنی گفتگویی باز نشده است." />
      ) : (
        <ul className="space-y-2" data-conversation-list>
          {conversations.map((row) => (
            <li key={row.id}>
              <button
                type="button"
                className={`w-full rounded-lg border px-3 py-2 text-start text-xs ${
                  row.id === activeId ? "border-primary/60 bg-primary/10" : "border-primary/10"
                }`}
                onClick={() => void select(row)}
                data-conversation-id={row.id}
                data-conversation-status={row.status}
              >
                <span className="font-semibold">{row.subject || "بدون موضوع"}</span>
                <span className="ms-2 text-ink-dim">
                  <Tag color={row.status === "open" ? "green" : "default"}>{row.status}</Tag>
                  آخرین پیام: {stamp(row.last_message_at)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {active ? (
        <div className="space-y-2" data-active-conversation={active.id}>
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <h4 className="font-semibold">{active.subject || "بدون موضوع"}</h4>
            <Button size="small" onClick={() => void loadThread(active.id)} data-refresh-thread>
              بازخوانی پیام‌ها
            </Button>
          </div>

          {thread === null ? (
            <Spin /> 
          ) : (
            <>
              <p className="text-[11px] text-ink-dim" data-thread-meta>
                {thread.messages.length.toLocaleString("fa-IR")} پیام · خوانده‌نشده:{" "}
                {thread.unread_count.toLocaleString("fa-IR")} · قاعدهٔ سرور: {thread.rule_version}
              </p>
              {thread.messages.length === 0 ? (
                <p role="status" className="text-xs text-ink-dim">
                  این گفتگو هیچ پیامی ندارد؛ «صفر پیام» یعنی هنوز پیامی ثبت نشده است.
                </p>
              ) : (
                <ul className="space-y-2" data-message-list>
                  {thread.messages.map((message) => (
                    <li
                      key={message.id}
                      className="rounded-lg border border-primary/10 px-3 py-2 text-xs"
                      data-message-id={message.id}
                      data-sender-role={message.sender_role}
                      data-read={message.read_at === null ? "no" : "yes"}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 text-ink-dim">
                        <span>{message.sender_role === "member" ? "شما" : "مربی"}</span>
                        <span>{stamp(message.created_at)}</span>
                      </div>
                      <p>{message.body}</p>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}

          <div className="space-y-1">
            <Input.TextArea
              rows={2}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="پیام تازه…"
              disabled={active.status === "closed" || busy}
              data-message-input
            />
            <div className="flex items-center gap-2">
              <Button
                type="primary"
                size="small"
                loading={busy}
                disabled={active.status === "closed" || draft.trim() === ""}
                onClick={() => void submit()}
                data-send-message
              >
                ارسال
              </Button>
              {active.status === "closed" ? (
                <span className="text-[11px] text-ink-dim">
                  این گفتگو بسته است؛ سرور پیام تازه را رد می‌کند.
                </span>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
