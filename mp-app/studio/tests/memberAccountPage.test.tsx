import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberAccount } from "../src/pages/MemberAccount";
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
  constraints: '["knee_injury","future_constraint"]',
};

const memberships = [
  {
    id: 81,
    member_id: 17,
    plan_name: "پلن ماهانهٔ واقعی",
    started_at: "2026-11-01T08:00:00",
    expires_at: "2026-11-30T11:59:00",
    status: "active",
    price_rial: 2_500_000,
  },
];

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
  setClock("2026-11-23T12:00:00Z");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
  setClock(null);
});

describe("member account API vertical slice (MEM-01)", () => {
  it("loads the authenticated profile, then requests only its server-owned member ID", async () => {
    const { calls } = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, memberProfile);
      if (path === "/api/v1/members/17/memberships") return reply(200, memberships);
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberAccount />);

    expect(await screen.findByText("مریم عضو واقعی")).toBeTruthy();
    expect(await screen.findByText("پلن ماهانهٔ واقعی")).toBeTruthy();
    expect(screen.getByText("آسیب زانو")).toBeTruthy();
    expect(screen.getByText("future_constraint")).toBeTruthy();
    expect(screen.getByText("رو به پایان")).toBeTruthy();
    expect(screen.getByText("۷ روز تا پایان اعتبار")).toBeTruthy();
    expect(screen.getByText(/۹ آذر ۱۴۰۵/)).toBeTruthy();

    await waitFor(() => expect(calls.map((call) => call.path)).toEqual([
      "/api/v1/members/me",
      "/api/v1/members/17/memberships",
    ]));
    expect(calls.every((call) => call.authorization === "Bearer member-access-token")).toBe(true);
    // The endpoint ID is the server's Member.id (17), not User.id (41), and never a client-selected ID.
    expect(calls.some((call) => call.path === "/api/v1/members/41/memberships")).toBe(false);
  });

  it("fails closed on a role mismatch and never requests a member history", async () => {
    const { calls } = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, { ...memberProfile, role: "coach" });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberAccount />);

    expect((await screen.findByRole("alert")).textContent).toContain("هویت حساب عضو از پاسخ سرور تأیید نشد");
    expect(screen.queryByText("مریم عضو واقعی")).toBeNull();
    expect(calls.map((call) => call.path)).toEqual(["/api/v1/members/me"]);
  });

  it("shows profile loading and retryable history errors, not an empty or expired state", async () => {
    let releaseProfile!: (response: Response) => void;
    let historyAttempts = 0;
    const deferredProfile = new Promise<Response>((resolve) => { releaseProfile = resolve; });
    const { calls } = installApi((path) => {
      if (path === "/api/v1/members/me") return deferredProfile;
      if (path === "/api/v1/members/17/memberships") {
        historyAttempts += 1;
        return historyAttempts === 1
          ? reply(503, { error: { message: "سرویس سابقه موقتاً در دسترس نیست" } })
          : reply(200, []);
      }
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberAccount />);
    expect(screen.getByRole("status").textContent).toContain("در حال دریافت حساب عضو");
    releaseProfile(reply(200, memberProfile));

    expect(await screen.findByText("مریم عضو واقعی")).toBeTruthy();
    expect((await screen.findByRole("alert")).textContent).toContain("سرویس سابقه موقتاً در دسترس نیست");
    expect(screen.queryByText(/سابقهٔ اشتراکی در حساب شما ثبت نشده/)).toBeNull();
    expect(screen.queryByText("منقضی")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "تلاش دوباره" }));
    expect(await screen.findByText(/سابقهٔ اشتراکی در حساب شما ثبت نشده است/)).toBeTruthy();
    expect(historyAttempts).toBe(2);
    expect(calls.map((call) => call.path)).toEqual([
      "/api/v1/members/me",
      "/api/v1/members/17/memberships",
      "/api/v1/members/17/memberships",
    ]);
  });

  it("does not request history when the server profile ID is invalid", async () => {
    const { calls } = installApi((path) => {
      if (path === "/api/v1/members/me") return reply(200, { ...memberProfile, id: 0 });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberAccount />);

    expect((await screen.findByRole("alert")).textContent).toContain("شناسهٔ پروفایل عضو از سرور معتبر نیست");
    expect(calls.map((call) => call.path)).toEqual(["/api/v1/members/me"]);
  });
});
