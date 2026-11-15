import { describe, expect, it, vi } from "vitest";
import {
  ApiError,
  AuthError,
  fetchAttendance,
  fetchFinanceSummary,
  fetchKpis,
  fetchMembersSummary,
} from "../src/lib/api";

const kpis = {
  members_total: 12,
  active_members: 7,
  new_members_30d: 3,
  revenue_paid_rial: 5_000_000,
  active_memberships: 8,
  classes: 4,
  class_fill_rate: null,
  generated_at: "2026-11-15T00:00:00Z",
};

const members = {
  items: [
    {
      member_id: 1,
      user_id: 1,
      full_name: "علی",
      phone: "0912",
      goal: "hypertrophy",
      gender: "male",
      membership_id: null,
      plan_name: null,
      status: "unknown",
      days_left: null,
      expires_at: null,
      is_active: true,
    },
  ],
  rule_version: "admin-members-summary-1.0",
  expiring_days: 7,
  unknown_status_meaning: "بی‌اشتراک = نامعلوم، نه منقضی",
  generated_at: "2026-11-15T00:00:00Z",
};

const attendance = {
  window_days: 7,
  total_checkins: 0,
  distinct_members: 0,
  closed_sessions: 0,
  open_sessions: 0,
  total_minutes: 0,
  series: [],
  rule_version: "admin-attendance-1.0",
  generated_at: "2026-11-15T00:00:00Z",
};

describe("studio api client (M45-c1)", () => {
  it("calls the real backend path for KPIs", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => kpis }));
    vi.stubGlobal("fetch", fetchMock);
    const data = await fetchKpis("tok");
    expect(data.members_total).toBe(12);
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/kpis", expect.anything());
  });

  it("keeps null class_fill_rate as unknown — never coerces to 0", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => kpis })));
    const data = await fetchKpis("tok");
    expect(data.class_fill_rate).toBeNull();
  });

  it("parses members summary with unknown status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: true, status: 200, json: async () => members })),
    );
    const data = await fetchMembersSummary("tok");
    expect(data.items[0].status).toBe("unknown");
    expect(data.rule_version).toBe("admin-members-summary-1.0");
  });

  it("requests attendance with an explicit window", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, status: 200, json: async () => attendance }));
    vi.stubGlobal("fetch", fetchMock);
    const data = await fetchAttendance(7, "tok");
    expect(data.total_checkins).toBe(0);
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/admin/attendance?days=7");
  });

  it("raises AuthError on 403 so the page asks for a token", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 403, json: async () => ({}) })));
    await expect(fetchKpis(null)).rejects.toBeInstanceOf(AuthError);
  });

  it("raises ApiError with status on 500 — no silent fallback to mock data", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) })));
    await expect(fetchFinanceSummary("tok")).rejects.toBeInstanceOf(ApiError);
  });

  it("raises ApiError(0) when the backend is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    await expect(fetchKpis("tok")).rejects.toMatchObject({ status: 0 });
  });
});
