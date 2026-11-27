/**
 * MEM-04 / PWA-33 — برنامهٔ عضو روی قرارداد واقعی API.
 *
 * آنچه این تست‌ها ثابت می‌کنند:
 * - شناسهٔ عضو از پاسخ سرور (`/members/me → id`) می‌آید، نه از کلاینت.
 * - فقط برنامهٔ `approved` نمایش داده می‌شود؛ draft/rejected برنامهٔ اجرایی نیست.
 * - هیچ عددی بدون منبع رندر نمی‌شود و حالت تهی، صفر جعلی نمی‌سازد.
 * - خطای آمادگی، امتیاز نمایش نمی‌دهد (fail-closed).
 * - MEM-06: وضعیت ایمنی در مسیر عضو واقعاً تفکیک می‌شود؛ چهار وضعیت چهار متن
 *   دارند و فقط `clear` + `safe_to_generate=true` فهرست حرکات و فرم ثبت را باز می‌کند.
 */
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberTodayProgram } from "../src/components/MemberTodayProgram";
import { setClock } from "../src/lib/clock";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
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

const approvedProgram = {
  id: 512,
  member_id: 17,
  coach_id: 9,
  status: "approved",
  goal: "hypertrophy",
  engine_version: "rules-2.3.0",
  llm_explanation: "توضیح سرور",
  reject_reason: "",
  approved_at: "2026-11-20T09:30:00",
  approved_by: 9,
  safety_flags: "{}",
  weeks: [
    {
      id: 71,
      week_number: 1,
      focus: "پایه",
      exercises: [
        {
          id: 900,
          exercise_id: 33,
          day: 1,
          order: 0,
          sets: 3,
          reps: "8-12",
          load_pct: 70,
          rest_seconds: 90,
          notes: "",
        },
      ],
    },
  ],
};

const readinessReady = {
  member_id: 17,
  program_id: 512,
  readiness: {
    score: 78,
    band: "ready",
    recommendation: "keep",
    volume_delta_sets: 0,
    signals: [],
    missing_signals: ["soreness"],
    reason: "",
    weights: {},
    thresholds: { deload_below: 40, recovery_below: 60, rir_tolerance: 1, volume_spike_ratio: 1.5 },
    rule_version: "readiness-1.4.0",
  },
  reason: "",
  rule_version: "readiness-1.4.0",
};

interface FetchCall {
  path: string;
  authorization: string | null;
}

function installApi(handler: (path: string) => Response | Promise<Response>) {
  const calls: FetchCall[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    calls.push({
      path: `${url.pathname}${url.search}`,
      authorization: new Headers(init?.headers).get("Authorization"),
    });
    return handler(`${url.pathname}${url.search}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
  window.history.replaceState({}, "", "/");
  setClock("2026-11-23T12:00:00Z");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  setClock(null);
});

describe("member today program (MEM-04 / PWA-33)", () => {
  it("renders the approved program's version, approval date and readiness with their sources", async () => {
    const { calls } = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/programs/member/17") return reply(200, [approvedProgram]);
      if (path === "/api/v1/programs/member/17/readiness") return reply(200, readinessReady);
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberTodayProgram />);

    expect(await screen.findByText("rules-2.3.0")).toBeTruthy();
    expect(screen.getByText(/۲۹ آبان ۱۴۰۵/)).toBeTruthy();
    expect(screen.getByText("hypertrophy")).toBeTruthy();
    // امتیاز آمادگی و نسخهٔ قاعده هر دو از سرور می‌آیند.
    expect(screen.getByText(/آمادگی: ۷۸ · آماده/)).toBeTruthy();
    expect(screen.getByText(/نسخهٔ قاعده: readiness-1\.4\.0/)).toBeTruthy();
    // منبع هر عدد روی صفحه نوشته شده است.
    expect(screen.getAllByText(/منبع: GET \/api\/v1\/programs\/member\/\{member_id\}/).length).toBeGreaterThan(0);
    // هیچ KPI/کالری/ادعای پزشکی بی‌منبع ساخته نمی‌شود.
    expect(screen.queryByText(/کالری/)).toBeNull();
    expect(screen.queryByText(/۱RM|1RM/)).toBeNull();

    await waitFor(() =>
      expect(calls.map((call) => call.path)).toEqual([
        "/api/v1/members/me",
        "/api/v1/programs/member/17",
        "/api/v1/programs/member/17/readiness",
      ]),
    );
    expect(calls.every((call) => call.authorization === "Bearer member-access-token")).toBe(true);
    // شناسه از پاسخ سرور است، نه انتخاب کلاینت.
    expect(calls.some((call) => call.path.includes("/programs/member/41"))).toBe(false);
  });

  it("shows an honest empty state when only a draft exists, with no program numbers", async () => {
    installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/programs/member/17") {
        return reply(200, [{ ...approvedProgram, id: 600, status: "draft", approved_at: null }]);
      }
      if (path === "/api/v1/programs/member/17/readiness") {
        return reply(200, { ...readinessReady, readiness: null, reason: "هیچ بازخورد ستی ثبت نشده" });
      }
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberTodayProgram />);

    expect(await screen.findByText(/هیچ برنامهٔ تأییدشده‌ای برای شما از سرور دریافت نشد/)).toBeTruthy();
    // draft فقط به‌عنوان شمارش وضعیت می‌آید؛ نه نسخه، نه ست، نه تکرار.
    expect(screen.getByText("برنامه‌های در انتظار تأیید: ۱")).toBeTruthy();
    expect(screen.queryByText("rules-2.3.0")).toBeNull();
    expect(screen.queryByText(/ست ×/)).toBeNull();
    expect(screen.queryByText(/آمادگی:/)).toBeNull();
  });

  it("keeps the readiness score hidden when the server reports no measured readiness", async () => {
    installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/programs/member/17") return reply(200, [approvedProgram]);
      if (path === "/api/v1/programs/member/17/readiness") {
        return reply(200, {
          ...readinessReady,
          readiness: null,
          reason: "هیچ بازخورد ستی برای این برنامه ثبت نشده — آمادگی سنجیده نمی‌شود",
        });
      }
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberTodayProgram />);

    expect(await screen.findByText("آمادگی: سنجیده نشد")).toBeTruthy();
    expect(screen.getByText(/آمادگی سنجیده نمی‌شود/)).toBeTruthy();
    expect(screen.queryByText(/آمادگی: ۷۸/)).toBeNull();
  });

  it("fails closed on a 403 and renders no program data", async () => {
    installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/programs/member/17") {
        return reply(403, { error: { message: "دسترسی فقط به دادهٔ خودتان مجاز است" } });
      }
      if (path === "/api/v1/programs/member/17/readiness") return reply(403, { error: { message: "forbidden" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberTodayProgram />);

    expect((await screen.findByRole("alert")).textContent).toContain("هیچ برنامه‌ای نمایش داده نمی‌شود");
    expect(screen.queryByText("rules-2.3.0")).toBeNull();
  });
});

/**
 * MEM-06 — دروازهٔ ایمنی روی مسیر عضو.
 *
 * ادعای پذیرش: «هیچ safety flag صرفاً برای ثبت یا warning دور زده نشود». بنابراین
 * تست باید ثابت کند که هر چهار وضعیت متن متفاوت دارند و برنامهٔ غیرمجاز **قابل اجرا
 * ارائه نمی‌شود** (فهرست حرکات و فرم ثبت رندر نمی‌شوند، دکمهٔ شروع غیرفعال است و
 * دلیلش متن دیده‌شدنی است).
 */
const blockedFlags = JSON.stringify({
  status: "blocked",
  headline: "۱ محدودیت با برنامهٔ پیشنهادی ناسازگار است",
  blocked: [
    {
      constraint: "knee_injury",
      label_fa: "آسیب زانو",
      blocked_exercises: ["squat", "lunge"],
      alternatives: ["leg_press_light"],
      advice_fa: "از اسکوات عمیق پرهیز شود.",
    },
  ],
  high_risk_patterns: [],
  notes: [],
  safe_to_generate: false,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
});

const needsReviewFlags = JSON.stringify({
  status: "needs_review",
  headline: "تأییدیهٔ پزشک ثبت نشده — نیازمند بازبینی",
  blocked: [],
  high_risk_patterns: [],
  notes: ["تأییدیهٔ پزشک ثبت نشده است."],
  safe_to_generate: false,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
});

const clearFlags = JSON.stringify({
  status: "clear",
  headline: "برنامه با محدودیت‌های ثبت‌شده ناسازگاری ندارد",
  blocked: [],
  high_risk_patterns: [],
  notes: [],
  safe_to_generate: true,
  disclaimer_fa: "این غربالگری جای تشخیص پزشک را نمی‌گیرد.",
  rule_version: "screening-1.0",
});

function renderWithSafety(flags: string, program: Record<string, unknown> = {}) {
  installApi((path) => {
    if (path === "/api/v1/members/me") return reply(200, memberProfile);
    if (path === "/api/v1/programs/member/17") {
      return reply(200, [{ ...approvedProgram, safety_flags: flags, ...program }]);
    }
    if (path === "/api/v1/programs/member/17/readiness") return reply(200, readinessReady);
    throw new Error(`unexpected API path: ${path}`);
  });
  return render(<MemberTodayProgram />);
}

const startButton = () => screen.queryByRole("button", { name: "شروع تمرین" }) as HTMLButtonElement | null;

describe("member safety gate (MEM-06)", () => {
  it("blocked: red alert with the constraint, no exercises, disabled start with a visible reason", async () => {
    renderWithSafety(blockedFlags);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("این برنامه برای شما ناسازگار است");
    expect(alert.textContent).toContain("آسیب زانو");
    expect(alert.textContent).toContain("squat");
    expect(alert.textContent).toContain("leg_press_light");
    // برنامه به‌عنوان «قابل اجرا» ارائه نمی‌شود.
    expect(screen.queryByText(/ست ×/)).toBeNull();
    expect(screen.queryByText(/هفتهٔ/)).toBeNull();
    expect(screen.queryByRole("button", { name: /ثبت بازخورد|ثبت/ })).toBeNull();
    // دکمهٔ شروع وجود دارد ولی غیرفعال است و دلیلش متن دیده‌شدنی است، نه tooltip.
    expect(startButton()?.disabled).toBe(true);
    expect(screen.getByText(/دلیل غیرفعال بودن دکمه:/).textContent).toContain("ناسازگار");
    // «بی‌خطر» هرگز برای برنامهٔ blocked گفته نمی‌شود.
    expect(screen.queryByText(/بدون ناسازگاری با محدودیت‌های ثبت‌شده/)).toBeNull();
  });

  it("needs_review: different text, still not executable", async () => {
    renderWithSafety(needsReviewFlags);

    expect((await screen.findAllByText(/نیازمند بازبینی مربی/)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/این برنامه برای شما ناسازگار است/)).toBeNull();
    expect(screen.queryByText(/بدون ناسازگاری با محدودیت‌های ثبت‌شده/)).toBeNull();
    expect(screen.queryByText(/ست ×/)).toBeNull();
    expect(startButton()?.disabled).toBe(true);
    expect(screen.getByText(/دلیل غیرفعال بودن دکمه:/).textContent).toContain("بازبینی");
  });

  it("unknown ({}): says 'not screened', never 'safe', and blocks execution", async () => {
    renderWithSafety("{}");

    expect(await screen.findByText(/غربالگری نشده — نه «بی‌خطر»/)).toBeTruthy();
    expect(screen.queryByText(/بدون ناسازگاری/)).toBeNull();
    expect(screen.queryByText(/ست ×/)).toBeNull();
    expect(startButton()?.disabled).toBe(true);
    expect(screen.getByText(/دلیل غیرفعال بودن دکمه:/).textContent).toContain("انجام نشده");
  });

  it("clear: the only status that renders the plan, with no dead start button", async () => {
    renderWithSafety(clearFlags);

    expect(await screen.findByText(/بدون ناسازگاری با محدودیت‌های ثبت‌شده/)).toBeTruthy();
    // فهرست حرکات از سرور نمایش داده می‌شود (قابل اجرا).
    expect(await screen.findByText(/ست ×/)).toBeTruthy();
    expect(screen.getByText(/هفتهٔ/)).toBeTruthy();
    // هیچ دکمهٔ شروع غیرفعالی برای برنامهٔ مجاز ساخته نمی‌شود: کنترل مرده نداریم.
    expect(startButton()).toBeNull();
  });

  it("a corrupt safety payload fails closed (not screened), not open", async () => {
    renderWithSafety("{not-json");

    expect(await screen.findByText(/غربالگری نشده — نه «بی‌خطر»/)).toBeTruthy();
    expect(screen.queryByText(/ست ×/)).toBeNull();
    expect(startButton()?.disabled).toBe(true);
  });
});
