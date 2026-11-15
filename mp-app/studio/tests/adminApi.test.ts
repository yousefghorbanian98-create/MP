import { describe, expect, it, vi } from "vitest";
import { AuthError, fetchLeaderboards } from "../src/lib/adminApi";

const sample = {
  top_athletes: [{ member_id: 1, full_name: "الف", avg_axis_score: 85, axes_counted: 3, method: "m" }],
  top_spenders: [],
  most_visits: [],
  most_time: [],
  window_days: 30,
  rule_version: "admin-analytics-1.0",
  generated_at: "2026-11-15T00:00:00Z",
};

describe("adminApi.fetchLeaderboards", () => {
  it("parses leaderboards from the real API", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => sample })));
    const data = await fetchLeaderboards("/api/v1", "tok", 30);
    expect(data.top_athletes).toHaveLength(1);
    expect(data.rule_version).toBe("admin-analytics-1.0");
  });

  it("throws AuthError on 401/403 — token required", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 401, json: async () => ({}) })));
    await expect(fetchLeaderboards("/api/v1", null)).rejects.toBeInstanceOf(AuthError);
  });

  it("fails loud on other errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })));
    await expect(fetchLeaderboards("/api/v1", "tok")).rejects.toThrow("500");
  });
});

describe("adminApi role management (M43)", () => {
  it("setUserRole posts the role payload", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }));
    vi.stubGlobal("fetch", fetchMock);
    const { setUserRole } = await import("../src/lib/adminApi");
    await setUserRole(7, "coach", "/api/v1", "tok");
    const call = fetchMock.mock.calls[0] as unknown[];
    expect(String(call[0])).toContain("/admin/users/7/role");
  });

  it("revokeUserRole maps 403 to AuthError (owner-only)", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 403, json: async () => ({}) })));
    const { revokeUserRole, AuthError } = await import("../src/lib/adminApi");
    await expect(revokeUserRole(7, "/api/v1", "tok")).rejects.toBeInstanceOf(AuthError);
  });
});

describe("adminApi churn risk (M44)", () => {
  it("parses risk rows including unknown band", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: true, status: 200,
      json: async () => ({ risk_rows: [{ member_id: 1, full_name: "x", risk_score: null, band: "unknown", signals: [], reason: "r", rule_version: "churn-risk-1.0" }] }),
    })));
    const { fetchChurnRisk } = await import("../src/lib/adminApi");
    const rows = await fetchChurnRisk("/api/v1", "tok");
    expect(rows[0].band).toBe("unknown");
    expect(rows[0].risk_score).toBeNull();
  });
});
