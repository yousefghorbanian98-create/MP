/**
 * MEM-09 / PWA-38 — کلاس و رزرو در مسیر عضو.
 *
 * قفل‌هایی که این تست‌ها می‌سازند:
 * - ظرفیت/صندلی خالی/لیست انتظار همیشه از سرور خوانده می‌شود و «دکمهٔ disabled»
 *   به‌عنوان اثبات عدم overbooking استفاده نمی‌شود (TODO صریح است).
 * - بعد از رزرو/لغو، حقیقت **دوباره از سرور** خوانده می‌شود (دو `GET /classes`).
 * - پیام موفقیت از `status` پاسخ سرور می‌آید: `confirmed` یا `waitlisted`.
 * - خطای `already_booked` به‌صورت متن دیده‌شدنی نشان داده می‌شود.
 * - سه حالت رزرو (تأییدشده / لیست انتظار / بدون رزرو) متن جدا دارند.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberClasses } from "../src/components/MemberClasses";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const classRow = (overrides: Record<string, unknown> = {}) => ({
  id: 7,
  name: "کراس‌فیت صبح",
  capacity: 10,
  schedule_text: "شنبه ۰۸:۰۰",
  coach_id: 3,
  confirmed: 4,
  waitlisted: 0,
  seats_left: 6,
  member_booking_status: null,
  member_booking_name: null,
  ...overrides,
});

function installApi(handler: (path: string, init?: RequestInit) => Response) {
  const calls: { path: string; method: string; body: unknown }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const method = init?.method ?? "GET";
      calls.push({
        path: url.pathname,
        method,
        body: init?.body ? JSON.parse(String(init.body)) : null,
      });
      return handler(url.pathname, init);
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

describe("member classes and booking (MEM-09)", () => {
  it("renders capacity, seats and waitlist from the server, with its source", async () => {
    installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, { id: 17, role: "member" });
      if (path === "/api/v1/classes") return reply(200, [classRow()]);
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses />);

    expect(await screen.findByText("کراس‌فیت صبح")).toBeTruthy();
    expect(screen.getByText(/ظرفیت: ۴ از ۱۰ · صندلی خالی: ۶ · لیست انتظار: ۰/)).toBeTruthy();
    expect(screen.getByText("رزرو شما: بدون رزرو")).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/classes/)).toBeTruthy();
  });

  it("distinguishes 'confirmed' from 'waitlisted' and from no booking at all", async () => {
    installApi((path) => {
      if (path === "/api/v1/classes")
        return reply(200, [
          classRow({ id: 1, name: "کلاس الف", member_booking_status: "confirmed" }),
          classRow({ id: 2, name: "کلاس ب", member_booking_status: "waitlisted", seats_left: 0 }),
          classRow({ id: 3, name: "کلاس ج", member_booking_status: null }),
        ]);
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberClasses memberId={17} />);

    expect(await screen.findByText("رزرو شما: تأییدشده")).toBeTruthy();
    expect(screen.getByText("رزرو شما: در لیست انتظار")).toBeTruthy();
    expect(screen.getByText("رزرو شما: بدون رزرو")).toBeTruthy();
    expect(container.querySelectorAll('[data-member-booking="none"]').length).toBe(1);
  });

  it("books through the API, then re-reads the server instead of trusting the click", async () => {
    let bookings = 0;
    const calls = installApi((path) => {
      if (path === "/api/v1/classes") {
        bookings += 1;
        return reply(
          200,
          [
            classRow({
              confirmed: bookings > 1 ? 5 : 4,
              seats_left: bookings > 1 ? 5 : 6,
              member_booking_status: bookings > 1 ? "confirmed" : null,
            }),
          ],
        );
      }
      if (path === "/api/v1/classes/book") return reply(200, { id: 31, status: "confirmed", member_name: "مریم" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses memberId={17} />);
    expect(await screen.findByText(/صندلی خالی: ۶/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "رزرو" }));

    await waitFor(() => expect(screen.getByText("رزرو شما: تأییدشده")).toBeTruthy());
    expect(screen.getByText(/رزرو شما توسط سرور تأیید شد/)).toBeTruthy();
    // payload واقعی ارسال شده است…
    const bookCall = calls.find((call) => call.path === "/api/v1/classes/book");
    expect(bookCall?.method).toBe("POST");
    expect(bookCall?.body).toEqual({ class_id: 7, member_id: 17 });
    // …و حقیقت از سرور دوباره خوانده شده است (دو بار GET /classes).
    expect(calls.filter((call) => call.path === "/api/v1/classes").length).toBe(2);
    expect(screen.getByText(/صندلی خالی: ۵/)).toBeTruthy();
  });

  it("reports a waitlisted result when the server says the class is full", async () => {
    installApi((path) => {
      if (path === "/api/v1/classes")
        return reply(200, [classRow({ seats_left: 0, confirmed: 10 })]);
      if (path === "/api/v1/classes/book") return reply(200, { id: 32, status: "waitlisted" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses memberId={17} />);
    expect(await screen.findByText(/ظرفیت پر است؛ اگر رزرو کنید/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "رزرو" }));
    await waitFor(() => expect(screen.getByText(/سرور شما را در لیست انتظار گذاشت/)).toBeTruthy());
  });

  it("surfaces the server's duplicate-booking error instead of hiding it", async () => {
    installApi((path) => {
      if (path === "/api/v1/classes") return reply(200, [classRow()]);
      if (path === "/api/v1/classes/book")
        return reply(400, { error: { message: "عضو قبلاً رزرو کرده است", code: "already_booked" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses memberId={17} />);
    fireEvent.click(await screen.findByRole("button", { name: "رزرو" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("عضو قبلاً رزرو کرده است");
  });

  it("cancels a booking and re-reads the server", async () => {
    let load = 0;
    const calls = installApi((path) => {
      if (path === "/api/v1/classes") {
        load += 1;
        return reply(200, [classRow({ member_booking_status: load > 1 ? null : "confirmed", confirmed: load > 1 ? 3 : 4 })]);
      }
      if (path === "/api/v1/classes/cancel") return reply(200, { id: 33, status: "cancelled" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses memberId={17} />);
    expect(await screen.findByText("رزرو شما: تأییدشده")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "لغو رزرو" }));

    await waitFor(() => expect(screen.getByText("رزرو شما: بدون رزرو")).toBeTruthy());
    expect(calls.find((call) => call.path === "/api/v1/classes/cancel")?.body).toEqual({
      class_id: 7,
      member_id: 17,
    });
    expect(calls.filter((call) => call.path === "/api/v1/classes").length).toBe(2);
  });

  it("fails closed on 403 with no class data", async () => {
    installApi((path) => {
      if (path === "/api/v1/classes") return reply(403, { error: { message: "forbidden" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberClasses memberId={17} />);

    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به کلاس‌ها مجاز نیست");
    expect(screen.queryByText(/صندلی خالی/)).toBeNull();
  });
});
