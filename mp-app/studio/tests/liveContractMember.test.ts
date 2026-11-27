/**
 * Live member-account contract (MEM-01): Studio's real typed client against a local API.
 *
 * CI seeds isolated synthetic A/B member profiles and supplies a short-lived fixture
 * member token. Without both env vars the suite is visibly skipped; it never falls
 * back to a manager token or mocks the API.
 */
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import {
  ApiError,
  fetchMe,
  fetchMemberMemberships,
  ForbiddenError,
  type Me,
  type MemberMembership,
} from "../src/lib/api";
import { formatMemberDateTime, getMemberMembershipView } from "../src/lib/memberAccount";

const BASE = process.env.MP_API_BASE ?? "";
const TOKEN = process.env.MP_MEMBER_TOKEN ?? "";
const OTHER_MEMBER_PHONE = "09120000005";
const live = BASE !== "" && TOKEN !== "";

let restoreFetch: (() => void) | undefined;
let identity: Me;
let memberships: MemberMembership[];
const requestPaths: string[] = [];

function tokenClaims(token: string): Record<string, unknown> {
  const payload = token.split(".")[1];
  if (!payload) throw new Error("fixture token is not a JWT");
  return JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Record<string, unknown>;
}

/** Match the existing live-contract harness while keeping every request on the local API. */
function installLiveFetch(): () => void {
  const original = globalThis.fetch;
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = String(input);
    const absolute = raw.startsWith("http") ? raw : `${BASE}${raw}`;
    const url = new URL(absolute);
    requestPaths.push(`${url.pathname}${url.search}`);
    return original(absolute, init);
  }) as typeof fetch;
  return () => {
    globalThis.fetch = original;
  };
}

describe.skipIf(!live)("member account live contract (MEM-01)", () => {
  beforeAll(async () => {
    restoreFetch = installLiveFetch();
    identity = await fetchMe(TOKEN);
    memberships = await fetchMemberMemberships(identity.id, TOKEN);
  });

  afterAll(() => restoreFetch?.());

  it("GET /members/me returns only the authenticated member identity", () => {
    const claims = tokenClaims(TOKEN);
    expect(claims.role).toBe("member");
    expect(identity.role).toBe(claims.role);
    expect(identity.id).toEqual(expect.any(Number));
    expect(identity.user_id).toEqual(expect.any(Number));
    expect(identity.id).toBeGreaterThan(0);
    expect(identity.user_id).toBeGreaterThan(0);
    expect(identity.user_id).toBe(Number(claims.sub));
    // CI deliberately makes User.id and Member.id different.
    expect(identity.user_id).not.toBe(identity.id);

    // Explicit allowlist prevents other-member or extra sensitive profile fields leaking.
    expect(Object.keys(identity).sort()).toEqual([
      "constraints",
      "full_name",
      "gender",
      "goal",
      "height_cm",
      "id",
      "phone",
      "role",
      "user_id",
    ]);
    expect(JSON.stringify(identity)).not.toContain(OTHER_MEMBER_PHONE);
    expect(requestPaths[0]).toBe("/api/v1/members/me");
  });

  it("fetches memberships by Member.id and rejects User.id as a substitute", async () => {
    expect(Array.isArray(memberships)).toBe(true);
    expect(memberships.length).toBeGreaterThan(0);
    for (const row of memberships) expect(row.member_id).toBe(identity.id);
    expect(requestPaths[1]).toBe(`/api/v1/members/${identity.id}/memberships`);

    let wrongIdError: unknown;
    try {
      // This is intentionally the tempting but incorrect User.id value.
      await fetchMemberMemberships(identity.user_id, TOKEN);
    } catch (error) {
      wrongIdError = error;
    }
    expect(
      wrongIdError instanceof ForbiddenError ||
        (wrongIdError instanceof ApiError && [403, 404].includes(wrongIdError.status)),
    ).toBe(true);
    expect(requestPaths[2]).toBe(`/api/v1/members/${identity.user_id}/memberships`);
  });

  it("maps an unknown server membership status to unknown, never expired", () => {
    const knownStatuses = new Set(["active", "expired", "cancelled"]);
    const unknown = memberships.find((row) => !knownStatuses.has(row.status));
    expect(unknown, "the live fixture must include an unknown-status membership").toBeDefined();
    expect(getMemberMembershipView(unknown!)).toEqual({ state: "unknown", daysLeft: null });
  });

  it("formats a 23:30 UTC boundary in the Persian calendar and Asia/Tehran", () => {
    const formatted = formatMemberDateTime("2026-11-23T23:30:00Z");
    expect(formatted).toContain("۳ آذر ۱۴۰۵");
    expect(formatted).toContain("۳:۰۰");
  });
});
