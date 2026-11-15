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
