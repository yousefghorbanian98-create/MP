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

// ── Feature flags (GET/PUT /admin/flags — M46-c1) ──

export interface FeatureFlagRow {
  id: number;
  key: string;
  enabled: boolean;
  description: string;
}

export function fetchFlags(token = getToken(), signal?: AbortSignal) {
  return getJson<FeatureFlagRow[]>("/admin/flags", token, signal);
}

/** ویرایش پرچم — تنها عملیات نوشتنِ استودیو تا امروز. */
export async function putFlag(
  key: string,
  enabled: boolean,
  description = "",
  token = getToken(),
): Promise<FeatureFlagRow> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}/admin/flags`, {
      method: "PUT",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify({ key, enabled, description }),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new AuthError("نشست معتبر نیست — توکن مدیر را وارد کنید");
  }
  if (!resp.ok) throw new ApiError(`خطای ${resp.status} در ثبت پرچم`, resp.status);
  return (await resp.json()) as FeatureFlagRow;
}

// ── سلامت سیستم (GET /health + /api/v1/health/ready) ──

export interface HealthInfo {
  status: string;
  service: string;
  version: string;
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthInfo> {
  const resp = await fetch("/health", { signal });
  if (!resp.ok) throw new ApiError(`خطای ${resp.status} در /health`, resp.status);
  return (await resp.json()) as HealthInfo;
}

// ── من (GET /members/me) — M46-c2 ──

export interface Me {
  id: number;
  user_id: number;
  full_name: string;
  phone: string;
  role: string;
  goal: string;
  gender: string;
  height_cm: number | null;
}

export function fetchMe(token = getToken(), signal?: AbortSignal) {
  return getJson<Me>("/members/me", token, signal);
}

// ── تولید برنامه از موتور قواعد (POST /ai/program/generate — G8) ──

export interface GeneratedProgram {
  id: number;
  member_id: number;
  goal: string;
  engine_version: string;
  status: string;
  llm_explanation: string;
  weeks_count?: number;
}

export async function generateProgram(
  memberId: number,
  opts: { goal?: string; level?: string; days_per_week?: number; weeks_count?: number } = {},
  token = getToken(),
): Promise<GeneratedProgram> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}/ai/program/generate`, {
      method: "POST",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify({
        member_id: memberId,
        goal: opts.goal ?? "hypertrophy",
        level: opts.level ?? "beginner",
        days_per_week: opts.days_per_week ?? 3,
        weeks_count: opts.weeks_count ?? 4,
        constraints: [],
      }),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new AuthError("نشست معتبر نیست — توکن مدیر را وارد کنید");
  }
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new ApiError(detail?.error?.message ?? `خطای ${resp.status} در تولید برنامه`, resp.status);
  }
  return (await resp.json()) as GeneratedProgram;
}

// ── گردش تأیید برنامه (US-203) ──

async function postJson<T>(path: string, body: unknown, token: string | null): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new AuthError("نشست معتبر نیست — توکن مدیر را وارد کنید");
  }
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new ApiError(detail?.error?.message ?? `خطای ${resp.status}`, resp.status);
  }
  return (await resp.json()) as T;
}

export function approveProgram(programId: number, token = getToken()) {
  return postJson<ProgramSummaryRow>(`/programs/${programId}/approve`, {}, token);
}

export function rejectProgram(programId: number, reason: string, token = getToken()) {
  return postJson<ProgramSummaryRow>(`/programs/${programId}/reject`, { reason }, token);
}

// ── G2 — گزارش حجم هفتگی (volume-landmarks-1.0) ──

export interface VolumeLandmarks {
  muscle: string;
  level: string;
  mv: number;
  mev: number;
  mav_min: number;
  mav_max: number;
  mrv: number;
  hard_set_max_rir: number;
  source: string;
  rule_version: string;
}

export interface VolumeMuscleRow {
  muscle: string;
  level: string;
  planned_sets: number;
  effective_sets: number;
  source_of_number: "planned" | "reported_hard_sets" | string;
  data_state: "no_feedback" | "reported" | string;
  hard_sets: number;
  soft_sets: number;
  unknown_rir_sets: number;
  landmarks: VolumeLandmarks;
  status: string;
  suggestion: { delta_sets: number; reason: string; rule_version: string };
  rule_version: string;
}

export interface VolumeReport {
  member_id: number;
  program_id: number | null;
  week_number?: number;
  level: string;
  muscles: VolumeMuscleRow[];
  reason: string;
  rule_version: string;
}

export function fetchMemberVolume(
  memberId: number,
  level: VolumeLevel = "intermediate",
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<VolumeReport>(
    `/programs/member/${memberId}/volume?level=${level}`,
    token,
    signal,
  );
}

export type VolumeLevel = "beginner" | "intermediate" | "advanced";

// ── G5 — ثبت غذای روزانه ──

export interface FoodRow {
  id: number;
  name_fa: string;
  category: string;
  kcal_per_100g: number;
  protein_g_per_100g: number;
  carbs_g_per_100g: number;
  fat_g_per_100g: number;
  dry_or_raw: boolean;
}

export interface FoodLogItem {
  id: number;
  food_id: number;
  name_fa: string;
  grams: number;
  meal_slot: string;
  kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  warning: string;
}

export interface DailyNutrition {
  member_id: number;
  date: string;
  items: FoodLogItem[];
  totals: { kcal: number; protein_g: number; carbs_g: number; fat_g: number };
  by_slot: Record<string, { kcal: number; protein_g: number; count: number }>;
  target: { kcal: number; protein_g: number; carbs_g: number; fat_g: number };
  target_source: "approved_plan" | "none" | string;
  plan_id: number | null;
  data_state: "logged" | "nothing_logged" | string;
  reason: string;
  rule_version: string;
}

export interface FoodLogResult {
  logged: number;
  rejected: { index: number; reason: string }[];
  reason: string;
  rule_version: string;
}

export function searchFoods(query: string, token = getToken(), signal?: AbortSignal) {
  return getJson<FoodRow[]>(
    `/nutrition/foods?q=${encodeURIComponent(query)}&limit=25`,
    token,
    signal,
  );
}

export function logFood(
  memberId: number,
  entries: { food_id: number; grams: number; meal_slot: string; logged_for_date: string }[],
  token = getToken(),
) {
  return postJson<FoodLogResult>("/nutrition/food-logs", { member_id: memberId, entries }, token);
}

export function fetchDailyNutrition(
  memberId: number,
  date: string,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<DailyNutrition>(
    `/nutrition/food-logs/member/${memberId}/daily?date=${date}`,
    token,
    signal,
  );
}

// ── G3 — تغذیهٔ سازگار ──

export interface AdaptiveReport {
  member_id: number;
  goal: string;
  current_target_kcal: number | null;
  plan_id: number | null;
  estimate: {
    tdee_kcal: number | null;
    confidence: "high" | "medium" | "low" | "insufficient" | string;
    data_state: string;
    mean_intake_kcal: number | null;
    weight_change_kcal_per_day?: number;
    reason: string;
    trend: {
      slope_kg_per_week: number | null;
      smoothed_start_kg: number | null;
      smoothed_end_kg: number | null;
      days_used: number;
      span_days: number;
      confidence: string;
      reason: string;
      notes: string[];
    };
    assumptions?: string[];
    rule_version: string;
  };
  suggestion: {
    suggested_target_kcal: number | null;
    delta_kcal: number;
    action: "increase" | "decrease" | "keep" | "none" | string;
    capped?: boolean;
    reason: string;
    rule_version: string;
  };
  data_counts: { weight_entries: number; intake_days: number };
  latest_weight_kg: number | null;
  rule_version: string;
}

export interface WeightLogResult {
  logged: number;
  updated: number;
  rejected: { index: number; reason: string }[];
  reason: string;
  rule_version: string;
}

export function fetchAdaptiveReport(memberId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<AdaptiveReport>(
    `/nutrition/member/${memberId}/adaptive`,
    token,
    signal,
  );
}

export function logWeight(
  memberId: number,
  entries: { weight_kg: number; logged_for_date: string }[],
  token = getToken(),
) {
  return postJson<WeightLogResult>("/nutrition/weight-logs", { member_id: memberId, entries }, token);
}

// ── G6 — روند JP7 ──

export interface Jp7Point {
  id: number;
  measured_at: string | null;
  sum_mm: number;
  sites: Record<string, number>;
  body_fat_pct: number | null;
}

export interface Jp7Trend {
  member_id: number;
  measurements: Jp7Point[];
  trend: {
    first_at: string | null;
    last_at: string | null;
    span_days: number;
    first_sum_mm: number;
    last_sum_mm: number;
    delta_mm: number;
    delta_mm_per_week: number | null;
    biggest_change_site: string;
    biggest_change_mm: number;
  } | null;
  site_deltas?: Record<string, { first_mm: number; last_mm: number; delta_mm: number }>;
  interpretation: {
    status: "stable" | "decreasing" | "increasing" | "insufficient" | string;
    headline: string;
    detail: string;
    confidence: string;
    threshold_mm?: number;
    suggestion?: string;
  };
  data_state: string;
  body_fat_note: string;
  rule_version: string;
}

export function fetchJp7Trend(memberId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<Jp7Trend>(`/assessments/jp7/member/${memberId}/trend`, token, signal);
}

/** G12 — مرور جدول غذایی با فیلتر دسته (بدون جستجو = همهٔ غذاها). */
export function browseFoods(
  query: string,
  limit = 100,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<FoodRow[]>(
    `/nutrition/foods?q=${encodeURIComponent(query)}&limit=${limit}`,
    token,
    signal,
  );
}

// ── G13 — آمادگی/خستگی ──

export interface ReadinessSignal {
  name: string;
  value: number | null;
  score: number | null;
  reason: string;
}

export interface ReadinessReport {
  member_id: number;
  program_id: number | null;
  readiness: {
    score: number | null;
    band: "ready" | "monitor" | "fatigued" | "insufficient" | string;
    recommendation: "increase" | "keep" | "deload" | "insufficient" | string;
    volume_delta_sets: number;
    signals: ReadinessSignal[];
    missing_signals: string[];
    reason: string;
    weights: Record<string, number>;
    thresholds: {
      deload_below: number;
      recovery_below: number;
      rir_tolerance: number;
      volume_spike_ratio: number;
    };
    actionable?: boolean;
    rule_version: string;
  } | null;
  data_counts?: { feedback_rows: number; sets_last_7_days: number; sets_prior_7_days: number };
  reason: string;
  note?: string;
  rule_version: string;
}

export function fetchReadiness(memberId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<ReadinessReport>(`/programs/member/${memberId}/readiness`, token, signal);
}
