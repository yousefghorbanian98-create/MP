import type { MemberMembership } from "./api";
import { now, SHOP_TIMEZONE, toDate } from "./clock";

export type MemberMembershipState = "active" | "expiring" | "expired" | "cancelled" | "unknown";

export interface MemberMembershipView {
  state: MemberMembershipState;
  daysLeft: number | null;
}

const DAY_MS = 24 * 60 * 60 * 1000;
const constraintLabels: Record<string, string> = {
  knee_injury: "آسیب زانو",
  low_back_pain: "کمردرد",
  shoulder_impingement: "گیرافتادگی شانه",
  wrist_issue: "مشکل مچ دست",
  hypertension: "فشار خون بالا",
  pregnancy: "بارداری",
};

/** Backend membership datetimes are UTC; SQLite may serialize UTC without a trailing Z. */
function parseBackendInstant(value: string): Date {
  const isIsoDateTime = /^\d{4}-\d{2}-\d{2}T/.test(value);
  const hasTimezone = /(?:[zZ]|[+-]\d{2}:?\d{2})$/.test(value);
  return toDate(isIsoDateTime && !hasTimezone ? `${value}Z` : value);
}

/** Keep known injury names human-readable while preserving unknown server labels verbatim. */
export function formatMemberConstraints(value: string): string[] {
  const raw = value.trim();
  if (!raw) return [];
  try {
    const decoded: unknown = JSON.parse(raw);
    if (Array.isArray(decoded) && decoded.every((item): item is string => typeof item === "string")) {
      return decoded.filter(Boolean).map((item) => constraintLabels[item] ?? item);
    }
  } catch {
    // Preserve malformed or older server values rather than claiming no constraints exist.
  }
  return [raw];
}

/** Interpret the server status plus the exact expiry instant; do not wait for a scheduled expiry job. */
export function getMemberMembershipView(
  membership: Pick<MemberMembership, "status" | "expires_at">,
  at: Date = now(),
): MemberMembershipView {
  if (membership.status === "cancelled") return { state: "cancelled", daysLeft: null };
  if (membership.status === "expired") return { state: "expired", daysLeft: null };
  if (membership.status !== "active") return { state: "unknown", daysLeft: null };

  const expiry = parseBackendInstant(membership.expires_at);
  if (!Number.isFinite(expiry.getTime())) return { state: "unknown", daysLeft: null };
  const remainingMs = expiry.getTime() - at.getTime();
  if (remainingMs <= 0) return { state: "expired", daysLeft: null };

  const daysLeft = Math.ceil(remainingMs / DAY_MS);
  return { state: daysLeft <= 7 ? "expiring" : "active", daysLeft };
}

/** Render backend UTC/offset timestamps in the shop's Persian calendar and timezone. */
export function formatMemberDateTime(value: string): string {
  const date = parseBackendInstant(value);
  if (!Number.isFinite(date.getTime())) return "تاریخ نامعتبر";
  return new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
    timeZone: SHOP_TIMEZONE,
    dateStyle: "long",
    timeStyle: "short",
  }).format(date);
}
