import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchConversations,
  fetchMessages,
  markConversationRead,
  openConversation,
  sendMessage,
  type ChatConversation,
  type ChatMessage,
} from "../lib/api";
import { useAppStore } from "../stores/appStore";
import { fa } from "../lib/useApi";

/**
 * G8 — چت مربی–شاگرد.
 *
 * تصمیم‌های UI:
 *   • خوانده‌نشده از سرور می‌آید، نه از یک شمارندهٔ محلی که با refresh گم شود
 *   • بعد از خواندن پیام‌ها، `read` صدا زده می‌شود و شمارنده واقعاً صفر می‌شود
 *   • ارسال ناموفق ⇒ متن در کادر می‌ماند تا کاربر داده‌اش را از دست ندهد
 *   • پیام خالی هرگز فرستاده نمی‌شود (هم UI هم سرور)
 */

function timeFa(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit" });
}

export function Chat() {
  const selectedMemberId = useAppStore((s) => s.selectedMemberId);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [unread, setUnread] = useState(0);
  const [draft, setDraft] = useState("");
  const [subject, setSubject] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await fetchConversations(
        selectedMemberId === null ? undefined : selectedMemberId,
      );
      setConversations(rows);
      setActiveId((cur) => cur ?? rows[0]?.id ?? null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedMemberId]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  const loadMessages = useCallback(async (id: number) => {
    try {
      const data = await fetchMessages(id);
      setMessages(data.messages);
      setUnread(data.unread_count);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (activeId === null) {
      setMessages([]);
      setUnread(0);
      return;
    }
    void loadMessages(activeId);
  }, [activeId, loadMessages]);

  useEffect(() => {
    // optional-call: محیط‌های بدون scrollIntoView (jsdom، مرورگرهای قدیمی)
    // نباید کل صفحهٔ چت را با استثنا از کار بیندازند.
    bottomRef.current?.scrollIntoView?.({ block: "end" });
  }, [messages]);

  async function startConversation() {
    if (selectedMemberId === null) {
      setError("برای شروع گفتگو، اول یک عضو را از صفحهٔ «اعضا» انتخاب کنید.");
      return;
    }
    setError(null);
    try {
      const conv = await openConversation(selectedMemberId, subject.trim());
      setSubject("");
      await loadConversations();
      setActiveId(conv.id);
      setNotice("گفتگوی جدید ساخته شد.");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function submit() {
    const text = draft.trim();
    if (!text || activeId === null) return;
    setSending(true);
    setError(null);
    try {
      const msg = await sendMessage(activeId, text);
      setMessages((prev) => [...prev, msg]);
      setDraft("");
      setNotice(null);
      void loadConversations();
    } catch (e) {
      // متن پاک نمی‌شود — کاربر نباید چیزی را از دست بدهد
      setError((e as Error).message);
    } finally {
      setSending(false);
    }
  }

  async function markRead() {
    if (activeId === null || unread === 0) return;
    try {
      const res = await markConversationRead(activeId);
      setUnread(0);
      setNotice(`${fa(res.marked_read)} پیام خوانده‌شده علامت خورد.`);
      await loadMessages(activeId);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const active = conversations.find((c) => c.id === activeId) ?? null;

  return (
    <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
      <aside className="glass-card flex max-h-[36rem] flex-col gap-3 p-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">گفتگوها</h3>
          <button onClick={() => void loadConversations()} className="btn-ghost px-2 py-1 text-[11px]">
            بازخوانی
          </button>
        </div>

        <div className="flex gap-1">
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="موضوع گفتگوی جدید"
            className="focus-ring min-w-0 flex-1 rounded-lg bg-surface/70 px-2 py-1.5 text-xs"
          />
          <button onClick={() => void startConversation()} className="btn-primary px-2 py-1.5 text-[11px]">
            شروع
          </button>
        </div>

        {loading && <p className="text-xs text-ink-dim">در حال بارگذاری…</p>}
        {!loading && conversations.length === 0 && (
          <p className="rounded-lg bg-surface/50 p-3 text-xs text-ink-dim">
            هیچ گفتگویی نیست. گفتگو با موضوع مشخص شروع می‌شود — گفتگوی خالی ساخته نمی‌شود.
          </p>
        )}

        <div className="flex-1 space-y-1 overflow-auto">
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                setActiveId(c.id);
                setNotice(null);
              }}
              className={`w-full rounded-lg px-3 py-2 text-right text-xs transition-colors ${
                c.id === activeId ? "bg-primary/20 text-white" : "bg-surface/50 hover:bg-surface/80"
              }`}
            >
              <span className="block truncate">{c.subject || `گفتگو #${c.id}`}</span>
              <span className="text-[10px] text-ink-dim">
                {c.last_message_at
                  ? `آخرین پیام ${timeFa(c.last_message_at)}`
                  : "بدون پیام"}
                {c.status === "closed" && " · بسته"}
              </span>
            </button>
          ))}
        </div>
      </aside>

      <section className="glass-card flex max-h-[36rem] flex-col gap-3 p-4">
        {error && (
          <p className="rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger" role="alert">
            {error}
          </p>
        )}
        {notice && <p className="text-[11px] text-emerald-300">{notice}</p>}

        {active === null ? (
          <p className="m-auto text-sm text-ink-dim">
            یک گفتگو را از فهرست انتخاب کنید یا گفتگوی جدیدی شروع کنید.
          </p>
        ) : (
          <>
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <div>
                <p className="text-sm font-medium">{active.subject || `گفتگو #${active.id}`}</p>
                <p className="text-[10px] text-ink-dim">
                  عضو #{fa(active.member_id)} · مربی #{fa(active.coach_id)}
                </p>
              </div>
              {unread > 0 && (
                <button onClick={() => void markRead()} className="btn-ghost px-2 py-1 text-[11px]">
                  {fa(unread)} خوانده‌نشده — علامت بزن
                </button>
              )}
            </div>

            <div className="flex-1 space-y-2 overflow-auto">
              {messages.length === 0 && (
                <p className="p-4 text-center text-xs text-ink-dim">
                  هنوز پیامی نیست. اولین پیام را بنویسید.
                </p>
              )}
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`max-w-[80%] rounded-xl px-3 py-2 text-xs ${
                    m.sender_role === "coach"
                      ? "ml-auto bg-primary/20"
                      : "mr-auto bg-surface/70"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.body}</p>
                  <p className="mt-1 text-[10px] text-ink-dim">
                    {m.sender_role === "coach" ? "مربی" : "عضو"} · {timeFa(m.created_at)}
                    {m.read_at === null && " · خوانده نشده"}
                  </p>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className="flex gap-2 border-t border-white/10 pt-2">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void submit();
                  }
                }}
                rows={2}
                placeholder="پیام… (Enter برای ارسال، Shift+Enter خط جدید)"
                className="focus-ring min-w-0 flex-1 resize-none rounded-lg bg-surface/70 px-3 py-2 text-xs"
              />
              <button
                onClick={() => void submit()}
                disabled={sending || draft.trim().length === 0}
                className="btn-primary self-end px-4 py-2 text-xs disabled:opacity-50"
              >
                {sending ? "…" : "ارسال"}
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
