import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  SESSION_EXPIRED_EVENT,
  clearSession,
  logoutSession,
  sessionFetch,
  storeTokenPair,
} from "../src/lib/session";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function initFor(call: unknown): RequestInit {
  return (call as [RequestInfo | URL, RequestInit])[1];
}

function authorization(call: unknown): string | null {
  return new Headers(initFor(call).headers).get("Authorization");
}

function urlFor(call: unknown): string {
  return String((call as [RequestInfo | URL])[0]);
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("Studio session transport (M67)", () => {
  it("refreshes once after 401, rotates the pair, and retries with the new access token", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(reply(401, { error: { message: "expired" } }))
      .mockResolvedValueOnce(
        reply(200, { access_token: "fresh-access", refresh_token: "refresh-2" }),
      )
      .mockResolvedValueOnce(reply(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/protected", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer old-access" },
      body: JSON.stringify({ operation: "save" }),
    });

    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(authorization(fetchMock.mock.calls[0])).toBe("Bearer old-access");
    expect(String(initFor(fetchMock.mock.calls[1]).body)).toBe(
      JSON.stringify({ refresh_token: "refresh-1" }),
    );
    expect(authorization(fetchMock.mock.calls[1])).toBeNull();
    expect(authorization(fetchMock.mock.calls[2])).toBe("Bearer fresh-access");
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("fresh-access");
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("refresh-2");
  });

  it("shares one refresh between concurrent 401s and retries both requests", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    const calls: { url: string; authorization: string | null }[] = [];
    let refreshCalls = 0;
    let resolveRefresh!: (response: Response) => void;
    const refreshResponse = new Promise<Response>((resolve) => {
      resolveRefresh = resolve;
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = new URL(String(input), window.location.href).pathname;
      const auth = new Headers(init?.headers).get("Authorization");
      calls.push({ url, authorization: auth });
      if (url === "/api/v1/auth/refresh") {
        refreshCalls += 1;
        return refreshResponse;
      }
      if (auth === "Bearer old-access") return reply(401, { error: { message: "expired" } });
      return reply(200, { ok: true });
    });
    vi.stubGlobal("fetch", fetchMock);

    const first = sessionFetch("/api/v1/protected/one");
    const second = sessionFetch("/api/v1/protected/two");
    await vi.waitFor(() => expect(refreshCalls).toBe(1));
    resolveRefresh(reply(200, { access_token: "fresh-access", refresh_token: "refresh-2" }));

    const responses = await Promise.all([first, second]);

    expect(responses.map((response) => response.status)).toEqual([200, 200]);
    expect(refreshCalls).toBe(1);
    expect(calls.filter((call) => call.url.startsWith("/api/v1/protected"))).toHaveLength(4);
    expect(calls.filter((call) => call.authorization === "Bearer fresh-access")).toHaveLength(2);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("fresh-access");
  });

  it.each(["/api/v1/auth/otp/verify", "/api/v1/auth/refresh", "/api/v1/auth/logout"])(
    "does not recurse into refresh for auth endpoint %s",
    async (path) => {
      storeTokenPair({ access_token: "access", refresh_token: "refresh" });
      const fetchMock = vi.fn().mockResolvedValue(reply(401, { error: { message: "unauthorized" } }));
      vi.stubGlobal("fetch", fetchMock);

      const response = await sessionFetch(path, { method: "POST" });

      expect(response.status).toBe(401);
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(urlFor(fetchMock.mock.calls[0])).toBe(path);
      expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("refresh");
    },
  );

  it("refreshes protected phone-change auth routes, but not an invalid OTP retry", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    let phoneChangeCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const path = new URL(String(input), window.location.href).pathname;
      if (path === "/api/v1/auth/phone-change/verify-old") {
        phoneChangeCalls += 1;
        return phoneChangeCalls === 1
          ? reply(401, { error: { message: "expired access" } })
          : reply(400, { error: { message: "invalid OTP" } });
      }
      if (path === "/api/v1/auth/refresh") {
        return reply(200, { access_token: "fresh-access", refresh_token: "refresh-2" });
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/auth/phone-change/verify-old", {
      method: "POST",
      body: JSON.stringify({ challenge_id: "challenge", code: "000000" }),
    });

    expect(response.status).toBe(400);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(urlFor(fetchMock.mock.calls[1])).toBe("/api/v1/auth/refresh");
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("fresh-access");
  });

  it("does not refresh a 403; authorization failure is not an expired session", async () => {
    storeTokenPair({ access_token: "access", refresh_token: "refresh" });
    const fetchMock = vi.fn().mockResolvedValue(reply(403, { error: { message: "forbidden" } }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/admin/secret");

    expect(response.status).toBe(403);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("access");
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("refresh");
  });

  it("clears the session and signals the app when refresh is rejected", async () => {
    storeTokenPair({ access_token: "expired", refresh_token: "revoked-refresh" });
    const expired = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, expired);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(reply(401, { error: { message: "expired" } }))
      .mockResolvedValueOnce(reply(401, { error: { message: "refresh revoked" } }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/protected");

    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
    expect(expired).toHaveBeenCalledTimes(1);
    window.removeEventListener(SESSION_EXPIRED_EVENT, expired);
  });

  it("does not clear a newer cross-tab token pair when the old refresh request fails", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    let resolveRefresh!: (response: Response) => void;
    const pendingRefresh = new Promise<Response>((resolve) => {
      resolveRefresh = resolve;
    });
    let refreshCalls = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const path = new URL(String(input), window.location.href).pathname;
      if (path === "/api/v1/protected") {
        return Promise.resolve(reply(401, { error: { message: "expired" } }));
      }
      if (path === "/api/v1/auth/refresh") {
        refreshCalls += 1;
        return pendingRefresh;
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const protectedRequest = sessionFetch("/api/v1/protected");
    await vi.waitFor(() => expect(refreshCalls).toBe(1));
    // Simulate a successful refresh in another tab, which shares localStorage.
    localStorage.setItem(ACCESS_TOKEN_KEY, "new-access");
    localStorage.setItem(REFRESH_TOKEN_KEY, "new-refresh");
    resolveRefresh(reply(401, { error: { message: "old refresh already rotated" } }));

    const response = await protectedRequest;

    expect(response.status).toBe(401);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("new-access");
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("new-refresh");
  });

  it("does not clear a token pair rotated in another tab while retry is pending", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    let resolveRetry!: (response: Response) => void;
    const pendingRetry = new Promise<Response>((resolve) => {
      resolveRetry = resolve;
    });
    let protectedCalls = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const path = new URL(String(input), window.location.href).pathname;
      if (path === "/api/v1/protected") {
        protectedCalls += 1;
        return protectedCalls === 1
          ? Promise.resolve(reply(401, { error: { message: "expired" } }))
          : pendingRetry;
      }
      if (path === "/api/v1/auth/refresh") {
        return Promise.resolve(
          reply(200, { access_token: "fresh-access", refresh_token: "refresh-2" }),
        );
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const protectedRequest = sessionFetch("/api/v1/protected");
    await vi.waitFor(() => expect(protectedCalls).toBe(2));
    // A newer session in another tab shares localStorage with this request.
    localStorage.setItem(ACCESS_TOKEN_KEY, "new-access");
    localStorage.setItem(REFRESH_TOKEN_KEY, "new-refresh");
    resolveRetry(reply(401, { error: { message: "stale retry" } }));

    const response = await protectedRequest;

    expect(response.status).toBe(401);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("new-access");
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("new-refresh");
  });

  it("does not loop if the post-refresh retry is still 401", async () => {
    storeTokenPair({ access_token: "stale", refresh_token: "refresh-1" });
    const expired = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, expired);
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(reply(401, { error: { message: "expired" } }))
      .mockResolvedValueOnce(
        reply(200, { access_token: "fresh-but-invalid", refresh_token: "refresh-2" }),
      )
      .mockResolvedValueOnce(reply(401, { error: { message: "still unauthorized" } }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/protected");

    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(urlFor(fetchMock.mock.calls[1])).toBe("/api/v1/auth/refresh");
    expect(urlFor(fetchMock.mock.calls[2])).toBe("/api/v1/protected");
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
    expect(expired).toHaveBeenCalledTimes(1);
    window.removeEventListener(SESSION_EXPIRED_EVENT, expired);
  });

  it("logout sends the rotating refresh token and clears browser access even when revocation is unconfirmed", async () => {
    storeTokenPair({ access_token: "access", refresh_token: "refresh-2" });
    const fetchMock = vi.fn().mockResolvedValue(reply(503, { error: { message: "offline" } }));
    vi.stubGlobal("fetch", fetchMock);

    const revoked = await logoutSession();

    expect(revoked).toBe(false);
    expect(urlFor(fetchMock.mock.calls[0])).toBe("/api/v1/auth/logout");
    expect(String(initFor(fetchMock.mock.calls[0]).body)).toBe(
      JSON.stringify({ refresh_token: "refresh-2" }),
    );
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
  });

  it("clears browser credentials synchronously while remote logout is still pending", async () => {
    storeTokenPair({ access_token: "access", refresh_token: "refresh" });
    let resolveLogout!: (response: Response) => void;
    const remote = new Promise<Response>((resolve) => {
      resolveLogout = resolve;
    });
    vi.stubGlobal("fetch", vi.fn(() => remote));

    const pending = logoutSession();

    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
    resolveLogout(reply(200, { status: "logged_out" }));
    await expect(pending).resolves.toBe(true);
  });

  it("does not restore a session when an in-flight refresh finishes after logout", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh-1" });
    let resolveRefresh!: (response: Response) => void;
    const pendingRefresh = new Promise<Response>((resolve) => {
      resolveRefresh = resolve;
    });
    let protectedCalls = 0;
    let refreshCalls = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const path = new URL(String(input), window.location.href).pathname;
      if (path === "/api/v1/protected") {
        protectedCalls += 1;
        return Promise.resolve(reply(401, { error: { message: "expired" } }));
      }
      if (path === "/api/v1/auth/refresh") {
        refreshCalls += 1;
        return pendingRefresh;
      }
      if (path === "/api/v1/auth/logout") {
        return Promise.resolve(reply(200, { status: "logged_out" }));
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const protectedRequest = sessionFetch("/api/v1/protected");
    await vi.waitFor(() => expect(refreshCalls).toBe(1));
    await expect(logoutSession()).resolves.toBe(true);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();

    resolveRefresh(reply(200, { access_token: "late-access", refresh_token: "refresh-2" }));
    const response = await protectedRequest;

    expect(response.status).toBe(401);
    expect(protectedCalls).toBe(1);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull();
  });

  it("does not let a late logout response clear a subsequently signed-in session", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "old-refresh" });
    let resolveLogout!: (response: Response) => void;
    const pendingLogout = new Promise<Response>((resolve) => {
      resolveLogout = resolve;
    });
    vi.stubGlobal("fetch", vi.fn(() => pendingLogout));

    const logout = logoutSession();
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBeNull();
    storeTokenPair({ access_token: "new-access", refresh_token: "new-refresh" });
    resolveLogout(reply(200, { status: "logged_out" }));

    await expect(logout).resolves.toBe(true);
    expect(localStorage.getItem(ACCESS_TOKEN_KEY)).toBe("new-access");
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe("new-refresh");
  });

  it("makes a protected request after local logout without reusing the former bearer token", async () => {
    storeTokenPair({ access_token: "old-access", refresh_token: "refresh" });
    clearSession();
    const fetchMock = vi.fn().mockResolvedValue(reply(401, { error: { message: "unauthorized" } }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await sessionFetch("/api/v1/protected");

    expect(response.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(authorization(fetchMock.mock.calls[0])).toBeNull();
  });
});
