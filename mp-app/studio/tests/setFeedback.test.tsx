/**
 * MEM-05 / PWA-34 — ثبت بازخورد ست: idempotency، timeout صریح، بازخوانی از API.
 *
 * آنچه این تست‌ها ثابت می‌کنند (نه بیشتر):
 * - نوشتن فقط به `POST /api/v1/programs/sync/set-feedback` می‌رود (قرارداد idempotent واقعی)،
 *   چون `POST /programs/set-feedback` کلید ندارد و هر ارسال یک ردیف تازه می‌سازد.
 * - بدنه شامل `client_id`، `device_id`، `updated_at` و `program_id` واقعی است.
 * - مهلت تمام‌شده = شکست صریح، تلاش دوباره همان `client_id`/`updated_at` را می‌فرستد.
 * - پاسخ `unchanged` به «قبلاً ثبت شده» ترجمه می‌شود، نه «ثبت شد».
 * - پس از ثبت، آمادگی/حجم **از API** دوباره خوانده می‌شود و شمارش سرور تغییر می‌کند.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberTodayProgram } from "../src/components/MemberTodayProgram";
import { SetFeedbackForm } from "../src/components/SetFeedbackForm";
import { DEVICE_ID_KEY } from "../src/lib/feedbackQueue";
import { setClock } from "../src/lib/clock";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const memberProfile = {
  id: 17,
  user_id: 41,
  full_name: "مریم عضو واقعی",
  phone: "09121234567",
  role: "member",
  goal: "hypertrophy",
  gender: "female",
  height_cm: 165,
  constraints: "[]",
};

const program = {
  id: 512,
  member_id: 17,
  coach_id: 9,
  status: "approved",
  goal: "hypertrophy",
  engine_version: "rules-2.3.0",
  llm_explanation: "",
  reject_reason: "",
  approved_at: "2026-11-20T09:30:00",
  approved_by: 9,
  // MEM-06: فرم ثبت ست فقط برای برنامه‌ای رندر می‌شود که گیت ایمنی آن را اجرایی کرده
  // باشد (`clear` + `safe_to_generate=true`). پس فیکسچر باید همان پرچم واقعی را داشته باشد.
  safety_flags: JSON.stringify({
    status: "clear",
    headline: "برنامه با محدودیت‌های ثبت‌شده ناسازگاری ندارد",
    blocked: [],
    high_risk_patterns: [],
    notes: [],
    safe_to_generate: true,
    disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
    rule_version: "screening-1.0",
  }),
  weeks: [{ id: 71, week_number: 1, focus: "پایه", exercises: [] }],
};

function readinessWith(feedbackRows: number) {
  return {
    member_id: 17,
    program_id: 512,
    readiness: {
      score: 62,
      band: "monitor",
      recommendation: "keep",
      volume_delta_sets: 0,
      signals: [],
      missing_signals: [],
      reason: "",
      weights: {},
      thresholds: { deload_below: 40, recovery_below: 60, rir_tolerance: 1, volume_spike_ratio: 1.5 },
      rule_version: "readiness-1.4.0",
    },
    data_counts: { feedback_rows: feedbackRows, sets_last_7_days: feedbackRows, sets_prior_7_days: 0 },
    reason: "",
    rule_version: "readiness-1.4.0",
  };
}

interface Call {
  path: string;
  method: string;
  body: Record<string, unknown> | null;
}

function installApi(handler: (path: string, body: Record<string, unknown> | null) => Response | Promise<Response>) {
  const calls: Call[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
    calls.push({ path: url.pathname, method: init?.method ?? "GET", body });
    return handler(url.pathname, body);
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
  setClock("2026-11-23T12:00:00Z");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  setClock(null);
});

async function mountWithProgram(handler: (path: string, body: Record<string, unknown> | null) => Response | Promise<Response>) {
  const api = installApi((path, body) => {
    if (path === "/api/v1/members/me") return reply(200, memberProfile);
    if (path === "/api/v1/programs/member/17") return reply(200, [program]);
    if (path === "/api/v1/programs/member/17/readiness") {
      const writes = api.calls.filter((call) => call.path === "/api/v1/programs/sync/set-feedback").length;
      return reply(200, readinessWith(writes > 0 ? 1 : 0));
    }
    if (path === "/api/v1/programs/sync/set-feedback") return handler(path, body);
    throw new Error(`unexpected API path: ${path}`);
  });
  render(<MemberTodayProgram />);
  await screen.findByText("rules-2.3.0");
  return api;
}

function fillSet(movement = "bench_press", reps = "10") {
  fireEvent.change(screen.getByLabelText("شناسهٔ حرکت"), { target: { value: movement } });
  fireEvent.change(screen.getByLabelText("بار"), { target: { value: "80" } });
  fireEvent.change(screen.getByLabelText("تکرار انجام‌شده"), { target: { value: reps } });
}

describe("set feedback write (MEM-05 / PWA-34)", () => {
  it("posts the idempotent sync payload with a real program id and re-reads readiness from the API", async () => {
    const api = await mountWithProgram(() =>
      reply(200, {
        member_id: 17,
        counts: { applied: 1 },
        results: [{ entity_key: "device:set-1", action: "inserted", winner: "client" }],
        applied_keys: ["device:set-1"],
        unchanged_keys: [],
        rule_version: "sync-lww-1.0",
      }),
    );

    expect(screen.getByText(/بازخوردهای ثبت‌شده در سرور: ۰/)).toBeTruthy();
    fillSet();
    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));

    expect(await screen.findByText(/ثبت شد: ۱ نوشته روی سرور اعمال شد/)).toBeTruthy();

    const write = api.calls.find((call) => call.path === "/api/v1/programs/sync/set-feedback");
    expect(write?.method).toBe("POST");
    const items = (write?.body as { items: Array<Record<string, unknown>> }).items;
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({
      program_id: 512,
      movement_id: "bench_press",
      weight: 80,
      reps_done: 10,
    });
    expect(typeof items[0].client_id).toBe("string");
    expect(String(items[0].client_id).length).toBeGreaterThan(8);
    expect(items[0].device_id).toBe(localStorage.getItem(DEVICE_ID_KEY));
    expect(String(items[0].updated_at)).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    // عمداً مسیر بدون idempotency صدا زده نمی‌شود
    expect(api.calls.some((call) => call.path === "/api/v1/programs/set-feedback")).toBe(false);

    // منبع حقیقت سرور است: شمارش بازخورد پس از reload از API می‌آید، نه از state محلی.
    await waitFor(() => expect(screen.getByText(/بازخوردهای ثبت‌شده در سرور: ۱/)).toBeTruthy());
  });

  it("treats an ambiguous timeout as an explicit failure and retries with the same idempotency key", async () => {
    let attempt = 0;
    const calls: Call[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null;
      calls.push({ path: url.pathname, method: init?.method ?? "GET", body });
      attempt += 1;
      if (attempt === 1) {
        // پاسخ هرگز نمی‌آید؛ فقط abort در سقف مهلت رخ می‌دهد (مهلت واقعی، نه شبیه‌سازی).
        // fetch واقعی هم با abort همان AbortError را می‌دهد؛ stub باید همان قرارداد را
        // رعایت کند وگرنه تست، خودِ منطق را سنجیده نیست.
        return new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () =>
            reject(new DOMException("The operation was aborted.", "AbortError")),
          );
        });
      }
      return reply(200, {
        member_id: 17,
        counts: { unchanged: 1 },
        results: [{ entity_key: "device:set-1", action: "conflict_resolved", winner: "server" }],
        applied_keys: [],
        unchanged_keys: ["device:set-1"],
        rule_version: "sync-lww-1.0",
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const onRecorded = vi.fn();
    render(<SetFeedbackForm memberId={17} program={program} onRecorded={onRecorded} timeoutMs={15} />);

    fillSet("squat", "8");
    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));

    expect((await screen.findByRole("alert")).textContent).toContain("زمان پاسخ سرور گذشت — ثبت نشد");
    expect(screen.queryByText(/ثبت شد/)).toBeNull();
    // نتیجه نامعلوم است: والد نباید بازخوانی «ثبت شد» کند.
    expect(onRecorded).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));
    expect(await screen.findByText(/قبلاً در سرور ثبت شده بود/)).toBeTruthy();
    expect(onRecorded).toHaveBeenCalledTimes(1);

    const writes = calls.filter((call) => call.path === "/api/v1/programs/sync/set-feedback");
    expect(writes).toHaveLength(2);
    const first = (writes[0].body as { items: Array<Record<string, unknown>> }).items[0];
    const second = (writes[1].body as { items: Array<Record<string, unknown>> }).items[0];
    // همان کلید و همان مهر زمانی ⇒ سرور رکورد تکراری نمی‌سازد.
    expect(second.client_id).toBe(first.client_id);
    expect(second.updated_at).toBe(first.updated_at);
  });

  it("uses a fresh key only after the form values change", async () => {
    const api = await mountWithProgram(() =>
      reply(200, {
        member_id: 17,
        counts: { applied: 1 },
        results: [{ entity_key: "device:set-1", action: "inserted", winner: "client" }],
        applied_keys: ["device:set-1"],
        unchanged_keys: [],
        rule_version: "sync-lww-1.0",
      }),
    );

    fillSet("row", "12");
    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));
    await screen.findByText(/نوشته روی سرور اعمال شد/);

    fireEvent.change(screen.getByLabelText("تکرار انجام‌شده"), { target: { value: "11" } });
    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));
    await waitFor(() =>
      expect(api.calls.filter((call) => call.path === "/api/v1/programs/sync/set-feedback")).toHaveLength(2),
    );

    const writes = api.calls.filter((call) => call.path === "/api/v1/programs/sync/set-feedback");
    const first = (writes[0].body as { items: Array<Record<string, unknown>> }).items[0];
    const second = (writes[1].body as { items: Array<Record<string, unknown>> }).items[0];
    expect(second.client_id).not.toBe(first.client_id);
  });

  it("refuses to submit without a movement id and never posts", async () => {
    const api = await mountWithProgram(() => reply(500, { error: { message: "unexpected" } }));

    fireEvent.click(screen.getByRole("button", { name: "ثبت ست" }));
    expect((await screen.findByRole("alert")).textContent).toContain("شناسهٔ حرکت لازم است");
    expect(api.calls.some((call) => call.path === "/api/v1/programs/sync/set-feedback")).toBe(false);
  });
});
