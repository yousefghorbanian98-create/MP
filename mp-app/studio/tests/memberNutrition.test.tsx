/**
 * MEM-08 / PWA-37 — تغذیهٔ عضو.
 *
 * قفل‌هایی که این تست‌ها می‌سازند:
 * - برنامه، وعده و ثبت روزانه از هم جدا هستند و هر عدد واحد + منبع دارد.
 * - `meals: []` ⇒ «برنامهٔ کامل نیست» (نه برنامهٔ سالمِ خالی).
 * - `data_state: nothing_logged` ⇒ هیچ عدد مصرفی (۰) نمایش داده نمی‌شود.
 * - `target_source: none` ⇒ مقایسهٔ «مصرف با هدف» ساخته نمی‌شود.
 * - ۴۰۳ ⇒ fail-closed بدون عدد.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberNutrition } from "../src/components/MemberNutrition";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const memberProfile = { id: 17, user_id: 41, full_name: "مریم", phone: "09121234567", role: "member" };

const plan = (overrides: Record<string, unknown> = {}) => ({
  id: 88,
  member_id: 17,
  coach_id: 9,
  status: "approved",
  daily_kcal: 2100,
  protein_g: 140,
  carbs_g: 210,
  fat_g: 60,
  engine_version: "nutrition-2.1.0",
  llm_explanation: "",
  meals: [
    { id: 1, meal_slot: "breakfast", name_fa: "املت", kcal: 420, protein_g: 24, carbs_g: 8, fat_g: 30 },
  ],
  ...overrides,
});

const log = (overrides: Record<string, unknown> = {}) => ({
  member_id: 17,
  date: "2026-11-27",
  items: [
    {
      id: 5,
      food_id: 3,
      name_fa: "مرغ",
      grams: 150,
      meal_slot: "lunch",
      kcal: 250,
      protein_g: 45,
      carbs_g: 0,
      fat_g: 6,
      warning: "",
    },
  ],
  totals: { kcal: 250, protein_g: 45, carbs_g: 0, fat_g: 6 },
  by_slot: { lunch: { kcal: 250, protein_g: 45, count: 1 } },
  target: { kcal: 2100, protein_g: 140, carbs_g: 210, fat_g: 60 },
  target_source: "approved_plan",
  plan_id: 88,
  data_state: "logged",
  reason: "۱ وعده در 2026-11-27 ثبت شده",
  rule_version: "food-log-1.0",
  ...overrides,
});

function installApi(handler: (path: string) => Response) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      calls.push(`${url.pathname}${url.search}`);
      return handler(`${url.pathname}${url.search}`);
    }),
  );
  return calls;
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("member nutrition (MEM-08)", () => {
  it("separates plan, meals and the daily log, with units and sources", async () => {
    const calls = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/nutrition/plans/member/17") return reply(200, [plan()]);
      if (path.startsWith("/api/v1/nutrition/food-logs/member/17/daily")) return reply(200, log());
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberNutrition />);

    expect(await screen.findByText(/برنامه‌های تغذیه/)).toBeTruthy();
    // واحد در همهٔ اعداد
    expect(screen.getAllByText(/کیلوکالری/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/گرم/).length).toBeGreaterThan(0);
    // منبع هر دو قرارداد روی صفحه
    expect(screen.getAllByText(/GET \/api\/v1\/nutrition\/plans\/member\/\{member_id\}/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/GET \/api\/v1\/nutrition\/food-logs\/member\/\{member_id\}\/daily/).length).toBeGreaterThan(0);
    // وعده‌های برنامه و ثبت روزانه دو بخش جدا هستند.
    expect(screen.getByText(/املت/)).toBeTruthy();
    expect(screen.getByText(/مرغ/)).toBeTruthy();
    expect(calls).toContain("/api/v1/nutrition/plans/member/17");
    expect(calls.some((path) => path.includes("/programs/member/41"))).toBe(false);
  });

  it("calls an empty meals[] an incomplete plan, not a healthy one", async () => {
    installApi((path) => {
      if (path === "/api/v1/nutrition/plans/member/17") return reply(200, [plan({ meals: [] })]);
      if (path.startsWith("/api/v1/nutrition/food-logs/member/17/daily")) return reply(200, log());
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberNutrition memberId={17} />);

    expect(await screen.findByText(/برنامهٔ کامل نیست/)).toBeTruthy();
    expect(container.querySelector('[data-plan-complete="no"]')).toBeTruthy();
  });

  it("shows no consumption numbers when nothing is logged", async () => {
    installApi((path) => {
      if (path === "/api/v1/nutrition/plans/member/17") return reply(200, [plan()]);
      if (path.startsWith("/api/v1/nutrition/food-logs/member/17/daily"))
        return reply(
          200,
          log({
            items: [],
            totals: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
            data_state: "nothing_logged",
            reason: "برای 2026-11-27 هیچ وعده‌ای ثبت نشده — صفر یعنی «ثبت نشده»، نه «نخورده»",
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberNutrition memberId={17} />);

    expect(await screen.findByText(/هیچ وعده‌ای ثبت نشده/)).toBeTruthy();
    expect(screen.queryByText(/جمع ثبت‌شده/)).toBeNull();
    expect(screen.getByText(/«۰» اینجا یعنی «ثبت نشده»، نه «نخورده»/)).toBeTruthy();
    expect(container.querySelector('[data-log-state="nothing_logged"]')).toBeTruthy();
  });

  it("does not build a comparison when the target does not come from an approved plan", async () => {
    installApi((path) => {
      if (path === "/api/v1/nutrition/plans/member/17") return reply(200, []);
      if (path.startsWith("/api/v1/nutrition/food-logs/member/17/daily"))
        return reply(
          200,
          log({
            target: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
            target_source: "none",
            plan_id: null,
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberNutrition memberId={17} />);

    expect(await screen.findByText(/هیچ «درصد رسیدن به هدف» یا مقایسه‌ای/)).toBeTruthy();
    expect(screen.getByText(/سرور هیچ برنامهٔ تغذیه‌ای برای شما برنگرداند/)).toBeTruthy();
    expect(container.querySelector('[data-target-source="none"]')).toBeTruthy();
  });

  it("fails closed on 403", async () => {
    installApi((path) => {
      if (path === "/api/v1/nutrition/plans/member/17") return reply(403, { error: { message: "forbidden" } });
      if (path.startsWith("/api/v1/nutrition/food-logs/member/17/daily")) return reply(403, { error: { message: "forbidden" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberNutrition memberId={17} />);

    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به تغذیهٔ این عضو مجاز نیست");
    expect(screen.queryByText(/کیلوکالری/)).toBeNull();
  });
});
