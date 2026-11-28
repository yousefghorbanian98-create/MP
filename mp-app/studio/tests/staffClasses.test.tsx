/**
 * STAFF-04 (PWA-43) — کلاس/حضور برای کارکنان: اعداد و وضعیت از سرور.
 *
 * دروازهٔ برداری این برش: «هیچ ادعای حضوری در کلاینت ساخته نمی‌شود».
 *  ۱. ظرفیت/تأییدشده/انتظار/جای خالی مستقیماً از `GET /classes` می‌آیند
 *     (عددِ جعلی یا محاسبهٔ کلاینتی وجود ندارد).
 *  ۲. وضعیت هر ورود از `result` سرور می‌آید؛ تغییر `ok` به `denied` در پاسخ
 *     سرور، متن UI را عوض می‌کند — یعنی متن hard-coded نیست.
 *  ۳. صفحه هیچ درخواست POST/PATCH نمی‌فرستد: بدون endpoint تأیید مربی، دکمهٔ
 *     «حاضر شد» ساخته نمی‌شود (همان قاعدهٔ MEM-12: دکمه ادعا نیست).
 *  ۴. roster نام‌دار endpoint ندارد؛ صفحه GAP را صریح می‌نویسد.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Classes } from "../src/pages/Classes";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

interface Call {
  method: string;
  path: string;
}

const CLASSES = [
  {
    id: 3,
    name: "کراس‌فیت صبح",
    capacity: 12,
    schedule_text: "شنبه ۰۷:۰۰",
    coach_id: 9,
    confirmed: 5,
    waitlisted: 2,
    seats_left: 7,
  },
  {
    id: 4,
    name: "تمرین قدرتی",
    capacity: 8,
    schedule_text: "یکشنبه ۱۸:۰۰",
    coach_id: null,
    confirmed: 8,
    waitlisted: 1,
    seats_left: 0,
  },
];

function stub(result: string) {
  const calls: Call[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    const method = (init?.method ?? "GET").toUpperCase();
    calls.push({ method, path: `${url.pathname}${url.search}` });
    if (url.pathname === "/api/v1/classes") return reply(200, CLASSES);
    if (url.pathname === "/api/v1/admin/checkins") {
      return reply(200, {
        items: [
          {
            checkin_id: 71,
            member_id: 4,
            member_name: "سارا تمرین",
            method: "qr",
            result,
            denial_reason: result === "ok" ? "" : "اشتراک منقضی",
            checked_in_at: "2026-11-28T06:10:00+00:00",
            checked_out_at: null,
            is_open: result === "ok",
          },
        ],
        rule_version: "checkin-feed-1.0",
        generated_at: "2026-11-28T06:20:00+00:00",
      });
    }
    throw new Error(`Unexpected request: ${method} ${url.pathname}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

if (typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) =>
      ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as unknown as MediaQueryList,
  });
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", `header.${btoa(JSON.stringify({ role: "coach" }))}.signature`);
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("STAFF-04 — کلاس‌ها و حضور کارکنان", () => {
  it("ظرفیت و شمارش رزرو را عیناً از سرور نشان می‌دهد و جای خالی نمی‌سازد", async () => {
    const calls = stub("ok");
    render(<Classes />);

    expect(await screen.findByText("کراس‌فیت صبح")).toBeTruthy();
    expect(screen.getByText(/ظرفیت ۱۲ · تأییدشده ۵ · انتظار ۲/)).toBeTruthy();
    expect(screen.getByText(/۷ جای خالی/)).toBeTruthy();
    // کلاس پر: پیام از seats_left=0 سرور می‌آید، نه از تفریق کلاینتی.
    expect(screen.getByText(/ظرفیت پر — فقط لیست انتظار/)).toBeTruthy();
    expect(calls.some((c) => c.path === "/api/v1/classes")).toBe(true);
  }, 15000);

  it("وضعیت ورود را از result سرور می‌خواند، نه از متن ثابت", async () => {
    stub("ok");
    render(<Classes />);
    expect(await screen.findByText("در باشگاه (باز)")).toBeTruthy();
  }, 15000);

  it("وقتی سرور result=denied می‌دهد، همان را با دلیل نشان می‌دهد", async () => {
    stub("denied");
    render(<Classes />);
    expect(await screen.findByText("رد شد")).toBeTruthy();
    expect(screen.getByText(/دلیل سرور: اشتراک منقضی/)).toBeTruthy();
    expect(screen.queryByText("در باشگاه (باز)")).toBeNull();
  }, 15000);

  it("هیچ درخواست نوشتنی نمی‌فرستد و دکمهٔ «حاضر شد» ندارد", async () => {
    const calls = stub("ok");
    render(<Classes />);
    await screen.findByText("کراس‌فیت صبح");

    await waitFor(() => expect(calls.length).toBeGreaterThanOrEqual(2));
    expect(calls.every((c) => c.method === "GET")).toBe(true);
    expect(screen.queryByRole("button", { name: /حاضر/ })).toBeNull();
    // نبود roster نام‌دار صریح گفته می‌شود، نه با دادهٔ ساختگی پر می‌شود.
    expect(screen.getByText(/roster نمی‌سازد/)).toBeTruthy();
  }, 15000);
});
