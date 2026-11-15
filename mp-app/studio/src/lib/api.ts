/**
 * کلاینت API استودیو (M45-c1) — همهٔ صفحه‌ها از اینجا داده می‌گیرند، نه از mock.
 *
 * قواعد:
 * - هیچ عددی ساختگی نیست: هر فیلد یا از API می‌آید یا صریحاً null/نامعلوم است.
 * - خطای ۴۰۱/۴۰۳ → AuthError (صفحه توکن می‌خواهد)؛ خطای شبکه → ApiError.
 * - توکن در localStorage با کلید `mp_token` — همان قرارداد adminApi.ts.
 */

export const API_BASE = "/api/v1";

export class AuthError extends Error {}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getToken(): string | null {
  return typeof localStorage !== "undefined" ? localStorage.getItem("mp_token") : null;
}

async function getJson<T>(path: string, token: string | null, signal?: AbortSignal): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}${path}`, { headers: authHeaders(token), signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("اتصال به سرور برقرار نشد — آیا بک‌اند روی ۸۷۵۱ اجراست؟", 0);
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new AuthError("نشست معتبر نیست — توکن مدیر را وارد کنید");
  }
  if (!resp.ok) {
    throw new ApiError(`خطای ${resp.status} در ${path}`, resp.status);
  }
  return (await resp.json()) as T;
}

// ── KPI داشبورد (GET /admin/kpis — M29) ──

export interface BackendKpis {
  members_total: number;
  active_members: number;
  new_members_30d: number;
  revenue_paid_rial: number;
  active_memberships: number;
  classes: number;
  class_fill_rate: number | null;
  generated_at: string;
}

export function fetchKpis(token = getToken(), signal?: AbortSignal) {
  return getJson<BackendKpis>("/admin/kpis", token, signal);
}

// ── خلاصهٔ اعضا (GET /admin/members-summary — M45-c1) ──

export type MembershipStatus = "active" | "expiring" | "expired" | "unknown";

export interface MemberSummaryRow {
  member_id: number;
  user_id: number;
  full_name: string;
  phone: string;
  goal: string;
  gender: string;
  membership_id: number | null;
  plan_name: string | null;
  status: MembershipStatus;
  days_left: number | null;
  expires_at: string | null;
  is_active: boolean;
}

export interface MembersSummary {
  items: MemberSummaryRow[];
  rule_version: string;
  expiring_days: number;
  unknown_status_meaning: string;
  generated_at: string;
}

export function fetchMembersSummary(token = getToken(), signal?: AbortSignal) {
  return getJson<MembersSummary>("/admin/members-summary", token, signal);
}

// ── حضور (GET /admin/attendance — M45-c2) ──

export interface AttendancePoint {
  date: string;
  count: number;
}

export interface AttendanceSummary {
  window_days: number;
  total_checkins: number;
  distinct_members: number;
  closed_sessions: number;
  open_sessions: number;
  total_minutes: number;
  series: AttendancePoint[];
  rule_version: string;
  generated_at: string;
}

export function fetchAttendance(days = 30, token = getToken(), signal?: AbortSignal) {
  return getJson<AttendanceSummary>(`/admin/attendance?days=${days}`, token, signal);
}

// ── مالی (GET /payments/finance/summary — M27) ──

export interface FinanceSummary {
  total_paid_rial: number;
  total_pending_rial: number;
  paid_count: number;
  generated_at: string;
}

export function fetchFinanceSummary(token = getToken(), signal?: AbortSignal) {
  return getJson<FinanceSummary>("/payments/finance/summary", token, signal);
}

// ── برنامه‌ها (GET /programs/member/{id}) — هیچ endpoint فهرست همهٔ برنامه‌ها وجود ندارد ──

export interface ProgramRow {
  id: number;
  member_id: number;
  status?: string;
  [key: string]: unknown;
}

export function fetchMemberPrograms(memberId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<ProgramRow[]>(`/programs/member/${memberId}`, token, signal);
}

export interface ProgramSummaryRow {
  id: number;
  member_id: number;
  member_name: string;
  status: "draft" | "approved" | "rejected" | string;
  goal: string;
  engine_version: string;
  weeks_count: number;
  llm_explanation: string;
  reject_reason: string;
  approved_at: string | null;
  created_at: string | null;
}

export interface ProgramsSummary {
  items: ProgramSummaryRow[];
  rule_version: string;
  counts_by_status: Record<string, number>;
}

export function fetchProgramsSummary(
  status: string | null = null,
  token = getToken(),
  signal?: AbortSignal,
) {
  const q = status ? `?status=${status}` : "";
  return getJson<ProgramsSummary>(`/programs${q}`, token, signal);
}

// ── ارزیابی ۱۴ محوری (GET /axis-assessments/...) ──

export interface AxisScoreRow {
  axis: number;
  name_fa: string;
  score: number | null;
  quality: string;
  decision_state: "direct" | "maintain" | "covered" | "refer" | "unknown" | string;
  decision_reason: string;
}

export interface AssessmentMatrix {
  assessment_id: number;
  member_id: number;
  status: string;
  axes: AxisScoreRow[];
  summary: Record<string, number>;
  rule_versions: Record<string, string>;
}

export interface AssessmentHistoryRow {
  assessment_id: number;
  member_id: number;
  status: string;
  created_at: string | null;
}

export function fetchAssessmentHistory(memberId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<AssessmentHistoryRow[]>(`/axis-assessments/member/${memberId}`, token, signal);
}

export function fetchAssessmentMatrix(
  assessmentId: number,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<AssessmentMatrix>(`/axis-assessments/${assessmentId}/matrix`, token, signal);
}

// ── جریان ورودهای اخیر (GET /admin/checkins — M45-c2) ──

export interface CheckinFeedRow {
  checkin_id: number;
  member_id: number;
  member_name: string;
  method: string;
  result: string;
  denial_reason: string;
  checked_in_at: string | null;
  checked_out_at: string | null;
  is_open: boolean;
}

export interface CheckinFeed {
  items: CheckinFeedRow[];
  rule_version: string;
  generated_at: string;
}

export function fetchCheckinFeed(limit = 50, token = getToken(), signal?: AbortSignal) {
  return getJson<CheckinFeed>(`/admin/checkins?limit=${limit}`, token, signal);
}
