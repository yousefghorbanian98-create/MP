import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  formatMemberConstraints,
  formatMemberDateTime,
  getMemberMembershipView,
} from "../src/lib/memberAccount";
import { setClock } from "../src/lib/clock";

beforeEach(() => setClock("2026-11-23T12:00:00Z"));
afterEach(() => setClock(null));

describe("member account membership status and timezone (MEM-02)", () => {
  it("does not label an unknown backend status as active or expired", () => {
    expect(getMemberMembershipView({ status: "pending", expires_at: "2026-12-01T12:00:00Z" })).toEqual({
      state: "unknown",
      daysLeft: null,
    });
  });

  it("uses the exact expiry instant, even before the scheduled expiry job runs", () => {
    expect(getMemberMembershipView({ status: "active", expires_at: "2026-11-23T12:00:00Z" })).toEqual({
      state: "expired",
      daysLeft: null,
    });
  });

  it("marks an active membership expiring within seven days and preserves a longer one as active", () => {
    // SQLite can serialize an aware UTC datetime without a suffix; it must still mean UTC.
    expect(getMemberMembershipView({ status: "active", expires_at: "2026-11-30T11:59:00" })).toEqual({
      state: "expiring",
      daysLeft: 7,
    });
    expect(getMemberMembershipView({ status: "active", expires_at: "2026-12-01T12:00:00Z" })).toEqual({
      state: "active",
      daysLeft: 8,
    });
  });

  it("preserves an explicit cancellation and treats a malformed expiry as unknown", () => {
    expect(getMemberMembershipView({ status: "cancelled", expires_at: "2026-12-01T12:00:00Z" }).state)
      .toBe("cancelled");
    expect(getMemberMembershipView({ status: "active", expires_at: "not-a-date" }).state)
      .toBe("unknown");
  });

  it("formats UTC instants using the Persian calendar and Asia/Tehran, including the day rollover", () => {
    // A timezone-naive backend timestamp is UTC, not the browser machine's local time.
    const formatted = formatMemberDateTime("2026-11-23T20:30:00");
    expect(formatted).toContain("۳ آذر ۱۴۰۵");
    expect(formatted).toContain("۰:۰۰");
  });

  it("labels known constraints while retaining unknown and malformed backend values", () => {
    expect(formatMemberConstraints('["knee_injury","future_constraint"]')).toEqual([
      "آسیب زانو",
      "future_constraint",
    ]);
    expect(formatMemberConstraints("[]")).toEqual([]);
    expect(formatMemberConstraints("not-json")).toEqual(["not-json"]);
  });
});
