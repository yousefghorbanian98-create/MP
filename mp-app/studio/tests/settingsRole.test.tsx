import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Settings } from "../src/pages/Settings";

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function tokenFor(role: string): string {
  return `header.${btoa(JSON.stringify({ role }))}.signature`;
}

function mockSettingsApi(): string[] {
  const paths: string[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    paths.push(`${url.pathname}${url.search}`);
    if (url.pathname === "/health") {
      return reply(200, { status: "ok", service: "api", version: "test" });
    }
    if (url.pathname === "/api/v1/admin/flags") return reply(200, []);
    if (url.pathname === "/api/v1/admin/users") return reply(200, []);
    if (url.pathname === "/api/v1/admin/audit") return reply(200, []);
    throw new Error(`Unexpected request: ${url.pathname}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return paths;
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("Settings role controls", () => {
  it("keeps settings available to admin but hides the owner-only role manager and its API calls", async () => {
    localStorage.setItem("mp_token", tokenFor("admin"));
    const paths = mockSettingsApi();

    render(<Settings />);

    await waitFor(() => expect(paths).toContain("/api/v1/admin/flags"));
    expect(screen.queryByText("admin pass — نقش‌های کاربران")).toBeNull();
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(paths).not.toContain("/api/v1/admin/users");
    expect(paths.some((path) => path.startsWith("/api/v1/admin/audit"))).toBe(false);
  });

  it("keeps the role manager visible and loads it for super_admin", async () => {
    localStorage.setItem("mp_token", tokenFor("super_admin"));
    const paths = mockSettingsApi();

    render(<Settings />);

    expect(await screen.findByText("admin pass — نقش‌های کاربران")).toBeTruthy();
    await waitFor(() => expect(paths).toContain("/api/v1/admin/users"));
    expect(paths.some((path) => path.startsWith("/api/v1/admin/audit"))).toBe(true);
  });
});
