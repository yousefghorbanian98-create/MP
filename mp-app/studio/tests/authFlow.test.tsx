import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { useAppStore } from "../src/stores/appStore";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function tokenFor(role: string, marker = "login"): string {
  return `header.${btoa(JSON.stringify({ role, marker }))}.signature`;
}

beforeEach(() => {
  localStorage.clear();
  window.history.replaceState({}, "", "/");
  useAppStore.setState({ page: "dashboard" });
});
afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("Studio OTP authentication flow (M67)", () => {
  it("signs in without pasting a token, refreshes on 401, then revokes and clears on logout", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    let memberMeCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      calls.push({ url: `${url.pathname}${url.search}`, init });

      if (url.pathname === "/api/v1/auth/otp/request") {
        return reply(200, { phone: "09121234567", expires_in: 120, dev_code: "123456" });
      }
      if (url.pathname === "/api/v1/auth/otp/verify") {
        return reply(200, {
          access_token: tokenFor("manager"),
          refresh_token: "refresh-1",
          user: { id: 1, phone: "09121234567", role: "manager", full_name: "مدیر آزمون" },
        });
      }
      if (url.pathname === "/api/v1/auth/refresh") {
        return reply(200, { access_token: tokenFor("manager", "fresh"), refresh_token: "refresh-2" });
      }
      if (url.pathname === "/api/v1/auth/logout") return reply(200, { status: "logged_out" });
      if (url.pathname === "/api/v1/members/me") {
        memberMeCalls += 1;
        if (memberMeCalls === 1) return reply(401, { error: { message: "expired" } });
        return reply(200, {
          id: 1,
          user_id: 1,
          full_name: "مدیر آزمون",
          phone: "09121234567",
          role: "manager",
          goal: "",
          gender: "male",
          height_cm: null,
        });
      }
      if (url.pathname === "/api/v1/admin/kpis") {
        return reply(200, {
          members_total: 0,
          active_members: 0,
          new_members_30d: 0,
          revenue_paid_rial: 0,
          active_memberships: 0,
          classes: 0,
          class_fill_rate: null,
          generated_at: "2026-11-16T00:00:00Z",
        });
      }
      if (url.pathname === "/api/v1/admin/attendance") {
        return reply(200, {
          window_days: 7,
          total_checkins: 0,
          distinct_members: 0,
          closed_sessions: 0,
          open_sessions: 0,
          total_minutes: 0,
          series: [],
          rule_version: "test",
          generated_at: "2026-11-16T00:00:00Z",
        });
      }
      if (url.pathname === "/api/v1/admin/members-summary") {
        return reply(200, { items: [], rule_version: "test", expiring_days: 7 });
      }
      if (url.pathname === "/api/v1/classes") return reply(200, []);
      if (url.pathname === "/api/v1/updates/manifest") {
        return reply(200, {
          update_available: false,
          latest: "0.1.0",
          current: "0.1.0",
          min_supported: "0.1.0",
          notes: "",
        });
      }
      return reply(200, {});
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.replaceState({}, "", "/staff/members");

    render(<App />);
    const phone = await screen.findByLabelText("شمارهٔ موبایل");
    expect(window.location.pathname).toBe("/login");
    expect(new URLSearchParams(window.location.search).get("returnTo")).toBe("/staff/members");
    expect(calls).toHaveLength(0);
    expect(screen.queryByText("پرچم‌های قابلیت")).toBeNull();
    expect(screen.queryByPlaceholderText("توکن ادمین (JWT) را اینجا بچسبانید")).toBeNull();
    fireEvent.change(phone, { target: { value: "۰۹۱۲۱۲۳۴۵۶۷" } });
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    await screen.findByText(/کد آزمایشی محیط توسعه/);
    fireEvent.change(screen.getByLabelText("کد یک‌بارمصرف"), { target: { value: "۱۲۳۴۵۶" } });
    fireEvent.click(screen.getByRole("button", { name: "ورود امن" }));

    await screen.findByRole("button", { name: "خروج از حساب" });
    expect(window.location.pathname).toBe("/staff/members");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("مدیریت اعضا");
    await waitFor(() => expect(memberMeCalls).toBe(2));
    expect(calls.filter((call) => call.url === "/api/v1/auth/refresh")).toHaveLength(1);
    const memberRequests = calls.filter((call) => call.url === "/api/v1/members/me");
    expect(memberRequests).toHaveLength(2);
    expect(new Headers(memberRequests[0].init?.headers).get("Authorization"))
      .toBe(`Bearer ${tokenFor("manager")}`);
    expect(new Headers(memberRequests[1].init?.headers).get("Authorization"))
      .toBe(`Bearer ${tokenFor("manager", "fresh")}`);
    expect(localStorage.getItem("mp_token")).toBe(tokenFor("manager", "fresh"));
    expect(localStorage.getItem("mp_refresh")).toBe("refresh-2");

    fireEvent.click(screen.getByRole("button", { name: "خروج از حساب" }));
    await screen.findByText("از حساب خارج شدید.");
    expect(localStorage.getItem("mp_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh")).toBeNull();
    const logout = calls.find((call) => call.url === "/api/v1/auth/logout");
    expect(logout).toBeDefined();
    expect(JSON.parse(String(logout?.init?.body))).toEqual({ refresh_token: "refresh-2" });
  });

  it("blocks direct navigation to settings for an authenticated manager", async () => {
    localStorage.setItem("mp_token", tokenFor("manager"));
    localStorage.setItem("mp_refresh", "manager-refresh");
    window.history.replaceState({}, "", "/staff/settings");
    const paths: string[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      paths.push(url.pathname);
      if (url.pathname === "/api/v1/members/me") {
        return reply(200, {
          id: 3,
          user_id: 3,
          full_name: "مدیر آزمون",
          phone: "09121234567",
          role: "manager",
          goal: "",
          gender: "male",
          height_cm: null,
        });
      }
      if (url.pathname === "/api/v1/updates/manifest") {
        return reply(200, { update_available: false, latest: "0.1.0", current: "0.1.0", min_supported: "0.1.0", notes: "" });
      }
      return reply(200, []);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(window.location.pathname).toBe("/staff/settings");
    expect(alert.textContent).toContain("دسترسی به این صفحه برای نقش جاری مجاز نیست");
    expect(paths).not.toContain("/api/v1/admin/flags");
    expect(screen.queryByText("پرچم‌های قابلیت")).toBeNull();
  });

  it("restores a refresh-protected deep link without exposing the requested screen", async () => {
    localStorage.setItem("mp_token", tokenFor("manager", "expired"));
    localStorage.setItem("mp_refresh", "refresh-before-load");
    window.history.replaceState({}, "", "/staff/settings");
    const paths: string[] = [];
    let meCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      paths.push(url.pathname);
      if (url.pathname === "/api/v1/members/me") {
        meCalls += 1;
        if (meCalls === 1) return reply(401, { error: { message: "expired" } });
        return reply(200, {
          id: 3,
          user_id: 3,
          full_name: "مدیر آزمون",
          phone: "09121234567",
          role: "manager",
          goal: "",
          gender: "male",
          height_cm: null,
        });
      }
      if (url.pathname === "/api/v1/auth/refresh") {
        return reply(200, { access_token: tokenFor("manager", "fresh"), refresh_token: "refresh-after-load" });
      }
      return reply(200, []);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    const alert = await screen.findByRole("alert");
    expect(window.location.pathname).toBe("/staff/settings");
    expect(alert.textContent).toContain("دسترسی به این صفحه برای نقش جاری مجاز نیست");
    expect(meCalls).toBe(3); // restore + one retry + TopBar identity lookup
    expect(paths.filter((path) => path === "/api/v1/auth/refresh")).toHaveLength(1);
    expect(paths).not.toContain("/api/v1/admin/flags");
    expect(localStorage.getItem("mp_token")).toBe(tokenFor("manager", "fresh"));
    expect(localStorage.getItem("mp_refresh")).toBe("refresh-after-load");
  });

  it("keeps restored member sessions out of staff routes", async () => {
    localStorage.setItem("mp_token", tokenFor("member"));
    localStorage.setItem("mp_refresh", "member-refresh");
    window.history.replaceState({}, "", "/staff/finance");
    const paths: string[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      paths.push(url.pathname);
      if (url.pathname === "/api/v1/members/me") {
        return reply(200, {
          id: 2,
          user_id: 2,
          full_name: "عضو آزمون",
          phone: "09121112222",
          role: "member",
          goal: "",
          gender: "male",
          height_cm: null,
        });
      }
      return reply(200, {});
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به این مسیر برای نقش جاری مجاز نیست");
    expect(paths).toEqual(["/api/v1/members/me"]);
    expect(screen.queryByText("خلاصهٔ مالی")).toBeNull();
  });

  it("signs in a member to a today deep link and keeps navigation and logout coherent", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      calls.push({ url: url.pathname, init });
      if (url.pathname === "/api/v1/auth/otp/request") {
        return reply(200, { phone: "09121112222", expires_in: 120, dev_code: "111111" });
      }
      if (url.pathname === "/api/v1/auth/otp/verify") {
        return reply(200, {
          access_token: tokenFor("member"),
          refresh_token: "member-refresh",
          user: { id: 2, phone: "09121112222", role: "member", full_name: "عضو" },
        });
      }
      if (url.pathname === "/api/v1/auth/logout") return reply(200, { status: "logged_out" });
      if (url.pathname === "/api/v1/members/me") {
        return reply(200, {
          id: 17,
          user_id: 2,
          full_name: "عضو واقعی",
          phone: "09121112222",
          role: "member",
          goal: "hypertrophy",
          gender: "male",
          height_cm: 180,
          constraints: "[]",
        });
      }
      if (url.pathname === "/api/v1/members/17/memberships") return reply(200, []);
      return reply(200, {});
    });
    vi.stubGlobal("fetch", fetchMock);
    window.history.replaceState({}, "", "/member/today");

    render(<App />);
    const phone = await screen.findByLabelText("شمارهٔ موبایل");
    expect(window.location.pathname).toBe("/login");
    expect(new URLSearchParams(window.location.search).get("returnTo")).toBe("/member/today");
    fireEvent.change(phone, { target: { value: "09121112222" } });
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));
    await screen.findByText(/کد آزمایشی محیط توسعه/);
    fireEvent.change(screen.getByLabelText("کد یک‌بارمصرف"), { target: { value: "111111" } });
    fireEvent.click(screen.getByRole("button", { name: "ورود امن" }));

    await screen.findByRole("heading", { name: "امروز" });
    expect(window.location.pathname).toBe("/member/today");
    expect(screen.getByRole("main").getAttribute("dir")).toBe("rtl");
    expect(screen.getByRole("link", { name: "امروز" }).getAttribute("aria-current")).toBe("page");

    fireEvent.click(screen.getByRole("link", { name: "خانه" }));
    await waitFor(() => expect(window.location.pathname).toBe("/member"));
    await screen.findByRole("heading", { name: "خانهٔ عضو" });
    expect(await screen.findByText("عضو واقعی")).toBeTruthy();
    expect(await screen.findByText(/سابقهٔ اشتراکی در حساب شما ثبت نشده است/)).toBeTruthy();
    expect(calls.some((call) => call.url === "/api/v1/members/17/memberships")).toBe(true);

    const waitForPopState = () =>
      new Promise<void>((resolve) => window.addEventListener("popstate", () => resolve(), { once: true }));
    await act(async () => {
      const popped = waitForPopState();
      window.history.back();
      await popped;
    });
    await waitFor(() => expect(window.location.pathname).toBe("/member/today"));
    await screen.findByRole("heading", { name: "امروز" });
    await act(async () => {
      const popped = waitForPopState();
      window.history.forward();
      await popped;
    });
    await waitFor(() => expect(window.location.pathname).toBe("/member"));
    await screen.findByRole("heading", { name: "خانهٔ عضو" });
    await act(async () => {
      const popped = waitForPopState();
      window.history.back();
      await popped;
    });
    await waitFor(() => expect(window.location.pathname).toBe("/member/today"));

    fireEvent.click(screen.getByRole("button", { name: "خروج از حساب" }));
    await screen.findByText("از حساب خارج شدید.");
    expect(window.location.pathname).toBe("/login");
    expect(new URLSearchParams(window.location.search).get("returnTo")).toBe("/member/today");
    expect(localStorage.getItem("mp_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh")).toBeNull();
    const logout = calls.find((call) => call.url === "/api/v1/auth/logout");
    expect(JSON.parse(String(logout?.init?.body))).toEqual({ refresh_token: "member-refresh" });
  });

  it("holds a member deep link behind session restoration and returns to login on expired refresh", async () => {
    localStorage.setItem("mp_token", tokenFor("member", "expired"));
    localStorage.setItem("mp_refresh", "revoked-member-refresh");
    window.history.replaceState({}, "", "/member/today");
    const paths: string[] = [];
    let resolveMe!: (response: Response) => void;
    const pendingMe = new Promise<Response>((resolve) => { resolveMe = resolve; });
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      paths.push(url.pathname);
      if (url.pathname === "/api/v1/members/me") return pendingMe;
      if (url.pathname === "/api/v1/auth/refresh") return Promise.resolve(reply(401, { error: { message: "revoked" } }));
      return Promise.resolve(reply(200, {}));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    expect(screen.getByRole("status").textContent).toContain("در حال بررسی نشست");
    expect(screen.queryByRole("heading", { name: "فضای عضو" })).toBeNull();
    await act(async () => resolveMe(reply(401, { error: { message: "expired" } })));
    await screen.findByLabelText("شمارهٔ موبایل");

    expect(window.location.pathname).toBe("/login");
    expect(new URLSearchParams(window.location.search).get("returnTo")).toBe("/member/today");
    expect(screen.getByRole("status").textContent).toContain("نشست منقضی یا لغو شده");
    expect(screen.queryByRole("heading", { name: "فضای عضو" })).toBeNull();
    expect(localStorage.getItem("mp_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh")).toBeNull();
    expect(paths).toEqual(["/api/v1/members/me", "/api/v1/auth/refresh"]);
  });

  it("shows a recoverable session-check error instead of member content when offline", async () => {
    localStorage.setItem("mp_token", tokenFor("member", "offline"));
    localStorage.setItem("mp_refresh", "member-refresh");
    window.history.replaceState({}, "", "/member");
    const fetchMock = vi.fn(async () => {
      throw new Error("network unavailable");
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByLabelText("شمارهٔ موبایل");

    expect(window.location.pathname).toBe("/login");
    expect(new URLSearchParams(window.location.search).get("returnTo")).toBe("/member");
    expect(screen.getByRole("status").textContent).toContain("برای بررسی نشست به سرور دسترسی نیست");
    expect(screen.queryByRole("heading", { name: "فضای عضو" })).toBeNull();
    expect(localStorage.getItem("mp_token")).toBe(tokenFor("member", "offline"));
    expect(localStorage.getItem("mp_refresh")).toBe("member-refresh");
  });

  it("fails closed and revokes a member token when /members/me reports a different role", async () => {
    localStorage.setItem("mp_token", tokenFor("member", "stale-role"));
    localStorage.setItem("mp_refresh", "member-refresh");
    window.history.replaceState({}, "", "/member");
    const calls: string[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(input instanceof Request ? input.url : String(input), window.location.href);
      calls.push(url.pathname);
      if (url.pathname === "/api/v1/members/me") return reply(200, { role: "coach" });
      return reply(200, { status: "logged_out" });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByLabelText("شمارهٔ موبایل");

    expect(screen.getByRole("status").textContent).toContain("نقش نشست با هویت حساب در سرور هم‌خوان نیست");
    expect(screen.queryByRole("heading", { name: "فضای عضو" })).toBeNull();
    expect(localStorage.getItem("mp_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh")).toBeNull();
    expect(calls).toEqual(["/api/v1/members/me", "/api/v1/auth/logout"]);
  });

  it("reports a backend session-check failure without rendering the member route", async () => {
    localStorage.setItem("mp_token", tokenFor("member", "server-error"));
    localStorage.setItem("mp_refresh", "member-refresh");
    window.history.replaceState({}, "", "/member/today");
    vi.stubGlobal("fetch", vi.fn(async () => reply(503, { detail: "unavailable" })));

    render(<App />);
    await screen.findByLabelText("شمارهٔ موبایل");

    expect(window.location.pathname).toBe("/login");
    expect(screen.getByRole("status").textContent).toContain("سرور نتوانست نشست را بررسی کند");
    expect(screen.queryByRole("heading", { name: "فضای عضو" })).toBeNull();
    expect(localStorage.getItem("mp_token")).toBe(tokenFor("member", "server-error"));
    expect(localStorage.getItem("mp_refresh")).toBe("member-refresh");
  });
});
