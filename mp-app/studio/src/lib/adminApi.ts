/**
 * کلاینت API مدیریتی — درخواست‌های محافظت‌شده از sessionFetch می‌گذرند تا 401
 * فقط یک‌بار refresh/retry شود و 403 به‌عنوان خطای مجوز باقی بماند.
 */

import { getAccessToken, sessionFetch } from "./session";

export class AuthError extends Error {}
export class ForbiddenError extends Error {}

async function throwAuthOrForbidden(response: Response): Promise<never> {
  if (response.status === 401) {
    throw new AuthError("نشست معتبر نیست — با کد یک‌بارمصرف دوباره وارد شوید");
  }
  let message = "نقش شما اجازهٔ این کار را ندارد";
  try {
    const body = (await response.json()) as { error?: { message?: string } };
    message = body.error?.message ?? message;
  } catch {
    // Keep the role-specific fallback when the response is not JSON.
  }
  throw new ForbiddenError(message);
}

export interface LeaderboardEntry {
  member_id: number;
  full_name: string;
  [key: string]: unknown;
}

export interface Leaderboards {
  top_athletes: LeaderboardEntry[];
  top_spenders: LeaderboardEntry[];
  most_visits: LeaderboardEntry[];
  most_time: LeaderboardEntry[];
  window_days: number;
  rule_version: string;
  generated_at: string;
}

export async function fetchLeaderboards(
  base = "/api/v1",
  token: string | null = getAccessToken(),
  windowDays = 30,
): Promise<Leaderboards> {
  const resp = await sessionFetch(`${base}/admin/analytics/leaderboards?window_days=${windowDays}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) {
    throw new Error(`خطای ${resp.status} در دریافت تحلیل‌ها`);
  }
  return (await resp.json()) as Leaderboards;
}

// ── M43: admin pass — مدیریت نقش‌ها [finn] ──

export interface UserRow {
  id: number;
  phone: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string | null;
}

export interface AuditRow {
  id: number;
  actor_user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  detail: string;
  created_at: string;
}

function authHeaders(token: string | null): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

export async function fetchUsers(base = "/api/v1", token: string | null = getAccessToken()): Promise<UserRow[]> {
  const resp = await sessionFetch(`${base}/admin/users`, { headers: authHeaders(token) });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new Error(`خطای ${resp.status}`);
  return (await resp.json()) as UserRow[];
}

export async function setUserRole(userId: number, role: string, base = "/api/v1", token: string | null = getAccessToken()): Promise<void> {
  const resp = await sessionFetch(`${base}/admin/users/${userId}/role`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ role }),
  });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new Error(`خطای ${resp.status}`);
}

export async function revokeUserRole(userId: number, base = "/api/v1", token: string | null = getAccessToken()): Promise<void> {
  const resp = await sessionFetch(`${base}/admin/users/${userId}/role`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new Error(`خطای ${resp.status}`);
}

export async function fetchAudit(action: string | null = null, base = "/api/v1", token: string | null = getAccessToken()): Promise<AuditRow[]> {
  const q = action ? `?action=${encodeURIComponent(action)}` : "";
  const resp = await sessionFetch(`${base}/admin/audit${q}`, { headers: authHeaders(token) });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new Error(`خطای ${resp.status}`);
  return (await resp.json()) as AuditRow[];
}


// ── M44: ریسک ریزش [finn] ──

export interface ChurnRow {
  member_id: number;
  full_name: string;
  risk_score: number | null;
  band: "high" | "medium" | "low" | "unknown";
  signals: { weight: number; reason: string }[];
  reason: string;
  rule_version: string;
}

export async function fetchChurnRisk(base = "/api/v1", token: string | null = getAccessToken()): Promise<ChurnRow[]> {
  const resp = await sessionFetch(`${base}/admin/analytics/churn-risk`, { headers: authHeaders(token) });
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new Error(`خطای ${resp.status}`);
  const body = (await resp.json()) as { risk_rows: ChurnRow[] };
  return body.risk_rows;
}
