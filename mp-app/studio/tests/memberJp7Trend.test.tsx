/**
 * MEM-07 / PWA-36 — «ارزیابی و روند» در مسیر عضو.
 *
 * آنچه این تست‌ها قفل می‌کنند (معیار پذیرش MEM-07):
 * - هر عدد با واحد و تاریخ اندازه‌گیری نمایش داده می‌شود.
 * - `trend === null` / `insufficient_measurements` ⇒ هیچ عدد پیشرفتی ساخته نمی‌شود؛
 *   «۰ میلی‌متر پیشرفت» وقتی داده نیست ممنوع است.
 * - `data_state` ناشناخته (مثل `stale`) حتی اگر `trend` پر باشد، **قابل مقایسه نیست**
 *   و عدد پیشرفت نمایش داده نمی‌شود.
 * - ۴۰۳ ⇒ fail-closed، بدون هیچ عددی.
 * - درصد چربی قفل، «قفل» گفته می‌شود؛ عکس پیشرفت بدن نه پیاده‌سازی شده و نه رندر می‌شود.
 */
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberJp7Trend } from "../src/components/MemberJp7Trend";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

const memberProfile = { id: 17, user_id: 41, full_name: "مریم", phone: "09121234567", role: "member" };

const point = (id: number, iso: string, sum: number, bodyFat: number | null = null) => ({
  id,
  measured_at: iso,
  sum_mm: sum,
  sites: { chest: 10 },
  body_fat_pct: bodyFat,
});

function trendPayload(overrides: Record<string, unknown> = {}) {
  return {
    member_id: 17,
    measurements: [point(1, "2026-10-01T09:00:00", 88.5), point(2, "2026-11-01T09:00:00", 84)],
    trend: {
      first_at: "2026-10-01T09:00:00",
      last_at: "2026-11-01T09:00:00",
      span_days: 31,
      first_sum_mm: 88.5,
      last_sum_mm: 84,
      delta_mm: -4.5,
      delta_mm_per_week: -1.02,
      biggest_change_site: "abdomen",
      biggest_change_mm: -2.5,
    },
    site_deltas: { abdomen: { first_mm: 20, last_mm: 17.5, delta_mm: -2.5 } },
    interpretation: {
      status: "decreasing",
      headline: "بافت زیرجلدی کاهش یافته است",
      detail: "مجموع چین‌ها ۴٫۵ میلی‌متر کم شده.",
      confidence: "medium",
      threshold_mm: 2.0,
      suggestion: "همان ناحیه را با همان کالیپر تکرار کنید",
    },
    data_state: "trend_available",
    body_fat_note: "درصد چربی محاسبه نشده و نمایش داده نمی‌شود (D-012).",
    rule_version: "jp7-trend-1.0",
    ...overrides,
  };
}

function installApi(handler: (path: string) => Response) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      calls.push(url.pathname);
      return handler(url.pathname);
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

describe("member JP7 trend (MEM-07)", () => {
  it("reads the member id from the server and renders each measurement with unit, date and source", async () => {
    const calls = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/assessments/jp7/member/17/trend") return reply(200, trendPayload());
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberJp7Trend />);

    expect(await screen.findByText(/اندازه‌گیری‌ها/)).toBeTruthy();
    // واحد در هر عدد هست؛ عدد لخت نمایش داده نمی‌شود.
    expect(screen.getAllByText(/میلی‌متر/).length).toBeGreaterThan(0);
    // منبع هم روی صفحه نوشته شده است.
    expect(screen.getAllByText(/GET \/api\/v1\/assessments\/jp7\/member\/\{member_id\}\/trend/).length).toBeGreaterThan(0);
    // درصد چربی قفل، «قفل» گفته می‌شود، نه صفر.
    expect(screen.getAllByText(/قفل \(نمایش داده نمی‌شود\)/).length).toBe(2);
    expect(calls).toContain("/api/v1/members/me");
    expect(calls.some((path) => path.includes("/programs/member/41"))).toBe(false);
  });

  it("shows the delta only when the server says the series is comparable", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend") return reply(200, trendPayload());
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberJp7Trend memberId={17} />);

    expect(await screen.findByText(/تغییر مجموع چین/)).toBeTruthy();
    expect(screen.getByText(/سرعت تغییر/)).toBeTruthy();
    expect(screen.getByText(/آستانهٔ تغییر/)).toBeTruthy();
    expect(container.querySelector('[data-comparable="yes"]')).toBeTruthy();
  });

  it("never invents progress when there is no trend (one measurement)", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend")
        return reply(
          200,
          trendPayload({
            measurements: [point(1, "2026-10-01T09:00:00", 88.5)],
            trend: null,
            site_deltas: {},
            interpretation: {
              status: "insufficient",
              headline: "برای تفسیر روند حداقل دو اندازه‌گیری لازم است",
              detail: "فقط ۱ اندازه‌گیری ثبت شده. یک نقطه، روند نیست.",
              confidence: "insufficient",
            },
            data_state: "insufficient_measurements",
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberJp7Trend memberId={17} />);

    expect(await screen.findByText(/روند نیست — داده کافی نیست/)).toBeTruthy();
    // هیچ عدد پیشرفتی ساخته نمی‌شود.
    expect(screen.queryByText(/تغییر مجموع چین/)).toBeNull();
    expect(screen.queryByText(/سرعت تغییر/)).toBeNull();
    // و «۰ پیشرفت» هم گفته نمی‌شود.
    expect(container.textContent).not.toMatch(/پیشرفت[^.]{0,12}۰/);
    expect(container.querySelector('[data-comparable="no"]')).toBeTruthy();
    // اندازه‌گیری خام هست، با واحد.
    expect(screen.getByText(/اندازه‌گیری‌ها/)).toBeTruthy();
  });

  it("treats an unknown data_state as not comparable even when a trend object is present", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend")
        return reply(200, trendPayload({ data_state: "stale" }));
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberJp7Trend memberId={17} />);

    expect(await screen.findByText(/این پاسخ «قابل مقایسه» نیست/)).toBeTruthy();
    expect(screen.queryByText(/تغییر مجموع چین/)).toBeNull();
    expect(container.querySelector('[data-trend-state="stale"]')).toBeTruthy();
    expect(container.querySelector('[data-comparable="no"]')).toBeTruthy();
  });

  it("fails closed on 403 and renders no numbers", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend")
        return reply(403, { error: { message: "دسترسی فقط به دادهٔ خودتان مجاز است" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberJp7Trend memberId={17} />);

    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به ارزیابی این عضو مجاز نیست");
    expect(screen.queryByText(/تغییر مجموع چین/)).toBeNull();
    expect(screen.queryByText(/اندازه‌گیری‌ها/)).toBeNull();
  });

  it("says 'no data' instead of zero progress when the series is empty, and shows no body photo", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend")
        return reply(
          200,
          trendPayload({
            measurements: [],
            trend: null,
            site_deltas: {},
            interpretation: {
              status: "insufficient",
              headline: "برای تفسیر روند حداقل دو اندازه‌گیری لازم است",
              detail: "فقط ۰ اندازه‌گیری ثبت شده. یک نقطه، روند نیست.",
              confidence: "insufficient",
            },
            data_state: "insufficient_measurements",
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberJp7Trend memberId={17} />);

    expect(await screen.findByText(/این «پیشرفت صفر» نیست/)).toBeTruthy();
    expect(screen.queryByText(/تغییر مجموع چین/)).toBeNull();
    // عکس پیشرفت بدن نه پیاده‌سازی شده و نه رندر می‌شود.
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toContain("عکس پیشرفت بدن در این برش نه پیاده‌سازی شده و نه نمایش داده می‌شود.");
  });

  it("shows a server-provided body-fat percentage with its unit, never as a bare number", async () => {
    installApi((path) => {
      if (path === "/api/v1/assessments/jp7/member/17/trend")
        return reply(
          200,
          trendPayload({
            measurements: [point(1, "2026-10-01T09:00:00", 88.5, 21.4)],
            trend: null,
            data_state: "insufficient_measurements",
          }),
        );
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberJp7Trend memberId={17} />);

    expect(await screen.findByText(/درصد چربی: .*٪/)).toBeTruthy();
  });
});
