/**
 * کلاینت API تحلیل‌های مدیریتی (M42-c3) — خواندن لیدربوردها از بک‌اند واقعی.
 * توکن در localStorage (mp_token) — نسخهٔ فعلی استودیو dev است؛ auth کامل در صف.
 */

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
  token: string | null = typeof localStorage !== "undefined" ? localStorage.getItem("mp_token") : null,
  windowDays = 30,
): Promise<Leaderboards> {
  const resp = await fetch(`${base}/admin/analytics/leaderboards?window_days=${windowDays}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (resp.status === 401 || resp.status === 403) {
    throw new AuthError("نشست معتبر نیست — توکن ادمین را وارد کنید");
  }
  if (!resp.ok) {
    throw new Error(`خطای ${resp.status} در دریافت تحلیل‌ها`);
  }
  return (await resp.json()) as Leaderboards;
}

export class AuthError extends Error {}
