import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PhoneChangeDialog } from "../src/components/PhoneChangeDialog";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  clearSession,
  storeTokenPair,
} from "../src/lib/session";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

/** Same shape the server signs: the account id lives in `sub`. */
function jwtFor(userId: number): string {
  return `header.${btoa(JSON.stringify({ sub: String(userId), role: "member" }))}.signature`;
}

const MEMBER_TOKEN = jwtFor(41);
const OTHER_TOKEN = jwtFor(52);
const CHALLENGE = "c".repeat(43);

beforeEach(() => {
  localStorage.clear();
  storeTokenPair({ access_token: MEMBER_TOKEN, refresh_token: "member-41-refresh" });
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSession();
});

describe("M82 phone-change dialog", () => {
  it("verifies the old phone before the new one and does not refresh for a wrong OTP", async () => {
    const calls: { path: string; body: Record<string, string>; authorization: string | null }[] = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const raw = input instanceof Request ? input.url : String(input);
      const path = new URL(raw, window.location.href).pathname;
      const headers = new Headers(init?.headers);
      const body = JSON.parse(String(init?.body)) as Record<string, string>;
      calls.push({ path, body, authorization: headers.get("Authorization") });

      if (path.endsWith("/auth/phone-change/request")) {
        return reply(200, { challenge_id: CHALLENGE, expires_in: 120, dev_code: "111111" });
      }
      if (path.endsWith("/auth/phone-change/verify-old") && body.code === "000000") {
        return reply(400, { error: { code: "invalid_otp", message: "کد نادرست است" } });
      }
      if (path.endsWith("/auth/phone-change/verify-old")) {
        return reply(200, { challenge_id: CHALLENGE, expires_in: 120, dev_code: "222222" });
      }
      if (path.endsWith("/auth/phone-change/confirm")) {
        return reply(200, { status: "phone_changed", phone: "09123456789" });
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const completed = vi.fn();

    render(
      <PhoneChangeDialog
        currentPhone="09121234567"
        onClose={vi.fn()}
        onCompleted={completed}
      />,
    );

    fireEvent.change(screen.getByLabelText("شمارهٔ جدید"), {
      target: { value: "۰۹۱۲۳۴۵۶۷۸۹" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ارسال کد به شمارهٔ فعلی" }));
    expect(await screen.findByText("کد آزمایشی: 111111")).toBeTruthy();
    expect(screen.getByText(/شمارهٔ فعلی 09121234567/)).toBeTruthy();

    fireEvent.change(screen.getByLabelText(/کد شمارهٔ فعلی/), {
      target: { value: "000000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "تأیید کد فعلی و ارسال کد جدید" }));
    expect((await screen.findByRole("alert")).textContent).toContain("کد نادرست است");
    expect(fetchMock).toHaveBeenCalledTimes(2);

    fireEvent.change(screen.getByLabelText(/کد شمارهٔ فعلی/), {
      target: { value: "123456" },
    });
    fireEvent.click(screen.getByRole("button", { name: "تأیید کد فعلی و ارسال کد جدید" }));
    expect(await screen.findByText("کد آزمایشی: 222222")).toBeTruthy();

    fireEvent.change(screen.getByLabelText(/کد شمارهٔ جدید/), {
      target: { value: "222222" },
    });
    fireEvent.click(screen.getByRole("button", { name: "تأیید و تغییر شماره" }));
    await waitFor(() => expect(completed).toHaveBeenCalledWith("09123456789", { account: "41" }));

    expect(calls.map((call) => call.path)).toEqual([
      "/api/v1/auth/phone-change/request",
      "/api/v1/auth/phone-change/verify-old",
      "/api/v1/auth/phone-change/verify-old",
      "/api/v1/auth/phone-change/confirm",
    ]);
    expect(calls[0].body).toEqual({ new_phone: "09123456789" });
    expect(calls.at(-1)?.body).toEqual({ challenge_id: CHALLENGE, code: "222222" });
    expect(calls.every((call) => call.authorization === `Bearer ${MEMBER_TOKEN}`)).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(4);
    // The dialog itself never touches storage; only the shell decides what the outcome means.
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe(MEMBER_TOKEN);
  });

  it("reports the guard of the account that sent confirm even when the reply arrives late", async () => {
    let resolveConfirm!: (response: Response) => void;
    const pendingConfirm = new Promise<Response>((resolve) => {
      resolveConfirm = resolve;
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const path = new URL(String(input), window.location.href).pathname;
      if (path.endsWith("/auth/phone-change/request")) {
        return reply(200, { challenge_id: CHALLENGE, expires_in: 120, dev_code: "111111" });
      }
      if (path.endsWith("/auth/phone-change/verify-old")) {
        return reply(200, { challenge_id: CHALLENGE, expires_in: 120, dev_code: "222222" });
      }
      if (path.endsWith("/auth/phone-change/confirm")) return pendingConfirm;
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const completed = vi.fn();

    render(
      <PhoneChangeDialog currentPhone="09121234567" onClose={vi.fn()} onCompleted={completed} />,
    );

    fireEvent.change(screen.getByLabelText("شمارهٔ جدید"), {
      target: { value: "09123456789" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ارسال کد به شمارهٔ فعلی" }));
    await screen.findByText("کد آزمایشی: 111111");
    fireEvent.change(screen.getByLabelText(/کد شمارهٔ فعلی/), { target: { value: "111111" } });
    fireEvent.click(screen.getByRole("button", { name: "تأیید کد فعلی و ارسال کد جدید" }));
    await screen.findByText("کد آزمایشی: 222222");
    fireEvent.change(screen.getByLabelText(/کد شمارهٔ جدید/), { target: { value: "222222" } });
    fireEvent.click(screen.getByRole("button", { name: "تأیید و تغییر شماره" }));

    // While confirm is in flight, another account signs in on this browser.
    storeTokenPair({ access_token: OTHER_TOKEN, refresh_token: "other-52-refresh" });
    resolveConfirm(reply(200, { status: "phone_changed", phone: "09123456789" }));

    // The callback must describe the session that started the step, not the current one.
    await waitFor(() => expect(completed).toHaveBeenCalledWith("09123456789", { account: "41" }));
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe(OTHER_TOKEN);
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("other-52-refresh");
  });
});
