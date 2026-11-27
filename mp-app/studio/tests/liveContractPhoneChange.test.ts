/**
 * Live phone-change contract (MEM-03 / PWA-32) — the Studio's real client against a
 * local API running the development SMS provider with dev-code echo.
 *
 * Why a separate suite: the offline tests stub `fetch`, so they prove the client's
 * request shape but not the contract. This file exercises the three real steps
 * (request → proof of the current phone → proof of the new phone), the session
 * revocation that follows, and `logout-all`, all over HTTP.
 *
 * It mutates the synthetic CI member's login number, so it must be the **last**
 * suite that uses that account, and it is skipped unless `MP_API_BASE` is set.
 * CI seeds a fresh database per run; never point this at a real environment.
 */
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { fetchMe, fetchSessions, logoutAllSessions } from "../src/lib/api";
import {
  clearSession,
  confirmPhoneChange,
  requestOtp,
  requestPhoneChange,
  storeTokenPair,
  verifyOldPhoneChange,
  verifyOtp,
} from "../src/lib/session";

const BASE = process.env.MP_API_BASE ?? "";
const SEEDED_PHONE = process.env.MP_LIVE_MEMBER_PHONE ?? "09120000004";
const OTHER_MEMBER_PHONE = "09120000005";
const NEW_PHONE = process.env.MP_LIVE_NEW_PHONE ?? "09120000104";
const live = BASE !== "";

let restoreFetch: (() => void) | undefined;
const requestPaths: string[] = [];

function installLiveFetch(): () => void {
  const original = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const absolute = raw.startsWith("http") ? raw : `${BASE}${raw}`;
    requestPaths.push(new URL(absolute).pathname);
    return original(absolute, init);
  }) as typeof fetch;
  return () => {
    globalThis.fetch = original;
  };
}

/** Direct HTTP check that bypasses the client's refresh-and-retry logic. */
function statusOf(path: string, init: RequestInit = {}): Promise<number> {
  return fetch(`${BASE}${path}`, init).then((response) => response.status);
}

function requireDevCode(step: { dev_code?: string | null }, label: string): string {
  if (!step.dev_code) {
    throw new Error(
      `${label}: سرور dev_code برنگرداند — API را با MP_ENVIRONMENT=development و MP_ALLOW_DEV_OTP_ECHO=true اجرا کنید`,
    );
  }
  return step.dev_code;
}

describe.skipIf(!live)("phone change live contract (MEM-03)", () => {
  beforeAll(() => {
    restoreFetch = installLiveFetch();
  });

  afterAll(() => {
    restoreFetch?.();
    clearSession();
  });

  it("changes the login number only through both OTP proofs and revokes every session", async () => {
    // 1) A genuine OTP login, so the session under test owns a real `sid` and refresh row.
    const loginCode = requireDevCode(await requestOtp(SEEDED_PHONE), "ورود اولیه");
    const login = await verifyOtp(SEEDED_PHONE, loginCode);
    storeTokenPair(login);
    const memberUserId = login.user?.id;
    expect(memberUserId).toEqual(expect.any(Number));
    expect(login.user?.phone).toBe(SEEDED_PHONE);

    const beforeChange = await fetchMe();
    expect(beforeChange.phone).toBe(SEEDED_PHONE);
    expect(beforeChange.user_id).toBe(memberUserId);
    expect(await fetchSessions()).toHaveLength(1);

    // 2) A number owned by another account is refused before any challenge exists.
    await expect(requestPhoneChange(OTHER_MEMBER_PHONE)).rejects.toThrow();

    // 3) Step one targets the current phone; a wrong code must not advance the flow.
    const started = await requestPhoneChange(NEW_PHONE);
    expect(started.challenge_id.length).toBeGreaterThan(10);
    await expect(verifyOldPhoneChange(started.challenge_id, "000000")).rejects.toThrow();
    const oldCode = requireDevCode(started, "اثبات شمارهٔ فعلی");

    // 4) Step two sends a *separate* code to the new number.
    const newStep = await verifyOldPhoneChange(started.challenge_id, oldCode);
    const newCode = requireDevCode(newStep, "اثبات شمارهٔ جدید");

    // 5) Confirm refuses a wrong new-number code, then accepts the real one.
    await expect(confirmPhoneChange(started.challenge_id, "000000")).rejects.toThrow();
    await expect(confirmPhoneChange(started.challenge_id, newCode)).resolves.toEqual({
      status: "phone_changed",
      phone: NEW_PHONE,
    });

    // 6) Every credential of the old session is dead: access and refresh alike.
    expect(
      await statusOf("/api/v1/members/me", {
        headers: { Authorization: `Bearer ${login.access_token}` },
      }),
    ).toBe(401);
    expect(
      await statusOf("/api/v1/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: login.refresh_token }),
      }),
      "confirm باید refresh tokenهای حساب را revoke کند",
    ).toBe(401);

    // 7) The same account now logs in with the new number.
    const newLoginCode = requireDevCode(await requestOtp(NEW_PHONE), "ورود با شمارهٔ جدید");
    const newLogin = await verifyOtp(NEW_PHONE, newLoginCode);
    expect(newLogin.user?.id).toBe(memberUserId);
    expect(newLogin.user?.phone).toBe(NEW_PHONE);

    const afterChange = await fetchMe(newLogin.access_token);
    expect(afterChange.user_id).toBe(memberUserId);
    expect(afterChange.phone).toBe(NEW_PHONE);

    // 8) The device list is real, scoped to this account, and marks this session.
    storeTokenPair(newLogin);
    const sessions = await fetchSessions();
    expect(Array.isArray(sessions)).toBe(true);
    expect(sessions.length).toBeGreaterThanOrEqual(1);
    expect(sessions.filter((row) => row.current)).toHaveLength(1);
    for (const row of sessions) expect(Number.isSafeInteger(row.id)).toBe(true);

    // 9) `logout-all` kills the session it was called from.
    await expect(logoutAllSessions()).resolves.toEqual({ status: "all_sessions_revoked" });
    expect(
      await statusOf("/api/v1/members/me", {
        headers: { Authorization: `Bearer ${newLogin.access_token}` },
      }),
    ).toBe(401);
    expect(
      await statusOf("/api/v1/auth/sessions", {
        headers: { Authorization: `Bearer ${newLogin.access_token}` },
      }),
    ).toBe(401);

    expect(requestPaths).toContain("/api/v1/auth/phone-change/confirm");
    expect(requestPaths).toContain("/api/v1/auth/logout-all");
  });
});
