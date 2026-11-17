/**
 * کلاینت API استودیو (M45-c1) — همهٔ صفحه‌ها از اینجا داده می‌گیرند، نه از mock.
 *
 * قواعد:
 * - هیچ عددی ساختگی نیست: هر فیلد یا از API می‌آید یا صریحاً null/نامعلوم است.
 * - خطای ۴۰۱/۴۰۳ → AuthError/ForbiddenError؛ خطای شبکه → ApiError.
 * - همهٔ درخواست‌های محافظت‌شده از sessionFetch می‌گذرند: یک refresh و یک retry برای ۴۰۱.
 */

import { getAccessToken, sessionFetch } from "./session";

export const API_BASE = "/api/v1";

/**
 * ۴۰۱ = «نشست معتبر نیست» (باید دوباره وارد شویم).
 *
 * جدا از ForbiddenError نگه داشته می‌شود چون رفتار کاربر متفاوت است:
 * برای ۴۰۱ باید توکن تازه بدهیم، برای ۴۰۳ توکن سالم است و فقط نقش اجازه
 * ندارد. نسخهٔ اول هر دو را AuthError می‌کرد و به مدیری که دسترسی نداشت
 * می‌گفت «توکن وارد کن» — یعنی کاربر را به اقدام اشتباه می‌فرستاد.
 */
export class AuthError extends Error {}

/** ۴۰۳ = توکن معتبر است، نقش اجازه ندارد. تلاش دوباره بی‌فایده است. */
export class ForbiddenError extends Error {}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/**
 * ۴۰۱ و ۴۰۳ را از هم جدا می‌کند.
 *
 * چرا تابع مشترک: این شرط در چهار نقطه تکرار شده بود و هر چهار جا یک پیام
 * اشتباه می‌دادند. یک نقطهٔ تصمیم، یک جای باگ.
 */
async function throwAuthOrForbidden(resp: Response): Promise<never> {
  if (resp.status === 401) {
    throw new AuthError("نشست معتبر نیست — با کد یک‌بارمصرف دوباره وارد شوید");
  }
  // ۴۰۳: پیام فارسیِ خودِ سرور گویاتر است («ساخت محصول فقط با تأیید مالک…»)
  let detail = "";
  try {
    const body = (await resp.json()) as { error?: { message?: string } };
    detail = body.error?.message ?? "";
  } catch {
    /* بدنه JSON نبود */
  }
  throw new ForbiddenError(detail || "نقش شما اجازهٔ این کار را ندارد");
}

function authHeaders(token: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getToken(): string | null {
  return getAccessToken();
}

async function getJson<T>(path: string, token: string | null, signal?: AbortSignal): Promise<T> {
  let resp: Response;
  try {
    resp = await sessionFetch(`${API_BASE}${path}`, { headers: authHeaders(token), signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("اتصال به سرور برقرار نشد — آیا بک‌اند روی ۸۷۵۱ اجراست؟", 0);
  }
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) {
    // پیام فارسیِ سرور را نگه می‌داریم: «عضو یافت نشد» به کاربر کمک می‌کند،
    // «خطای ۴۰۴ در /notifications/reminders/…» نه. اگر بدنه JSON نبود،
    // به پیام عمومی برمی‌گردیم.
    let detail = "";
    try {
      const body = (await resp.json()) as { error?: { message?: string } };
      detail = body.error?.message ?? "";
    } catch {
      /* بدنه JSON نیست */
    }
    throw new ApiError(detail || `خطای ${resp.status} در ${path}`, resp.status);
  }
  return (await resp.json()) as T;
}

/** دانلود فایل با هدر توکن — `fetch` خام توکن ندارد و ۴۰۱ می‌گیرد. */
async function getBlob(path: string, token: string | null): Promise<Blob> {
  let resp: Response;
  try {
    resp = await sessionFetch(`${API_BASE}${path}`, { headers: authHeaders(token) });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("اتصال به سرور برقرار نشد — آیا بک‌اند روی ۸۷۵۱ اجراست؟", 0);
  }
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) throw new ApiError(`دریافت فایل ناموفق (HTTP ${resp.status})`, resp.status);
  return resp.blob();
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

export interface CommissionResult {
  coach_id: number;
  coach_name: string;
  rate: number;
  attributed_payments_rial: number;
  commission_rial: number;
}

export function fetchCommission(
  coachId: number,
  rate: number,
  token = getToken(),
): Promise<CommissionResult> {
  return postJson<CommissionResult>(
    "/payments/finance/commission",
    { coach_id: coachId, rate },
    token,
  );
}

export function fetchPaymentsCsv(token = getToken()): Promise<Blob> {
  return getBlob("/payments/finance/export.csv", token);
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
  /** Q7 — JSON غربالگری ایمنی؛ «{}» یعنی غربالگری نشده، نه بی‌خطر. */
  safety_flags?: string;
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
    resp = await sessionFetch(`${API_BASE}/admin/flags`, {
      method: "PUT",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify({ key, enabled, description }),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
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
    resp = await sessionFetch(`${API_BASE}/ai/program/generate`, {
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
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
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
    resp = await sessionFetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
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

// ── Q6 — درگاه پرداخت (start / callback) ──

export interface PaymentRow {
  id: number;
  member_id: number;
  amount_rial: number;
  method: string;
  status: string;
  reference_id: string;
  gateway_authority?: string;
  description: string;
  paid_at: string | null;
}

export interface PaymentStart {
  payment_id: number;
  authority: string;
  redirect_url: string;
  amount_rial: number;
  callback_token: string;
}

export function createPayment(
  body: { member_id: number; amount_rial: number; method: string; description?: string },
  token = getToken(),
) {
  return postJson<PaymentRow>("/payments", body, token);
}

export interface Receipt {
  payment_id: number;
  member_id: number;
  amount_rial: number;
  paid_at: string | null;
  reference_id: string;
  [k: string]: unknown;
}

export function fetchReceipt(paymentId: number, token = getToken(), signal?: AbortSignal) {
  return getJson<Receipt>(`/payments/${paymentId}/receipt`, token, signal);
}

export function failPayment(paymentId: number, token = getToken()) {
  return postJson<PaymentRow>(`/payments/${paymentId}/fail`, {}, token);
}

export function startPayment(paymentId: number, callbackUrl = "", token = getToken()) {
  return postJson<PaymentStart>(
    `/payments/${paymentId}/start`,
    { callback_url: callbackUrl },
    token,
  );
}

export function confirmGatewayCallback(
  paymentId: number,
  authority: string,
  callbackToken: string,
  token = getToken(),
) {
  return postJson<PaymentRow>(
    `/payments/${paymentId}/callback`,
    { authority, callback_token: callbackToken },
    token,
  );
}

// ── autoreg-1.0 — وزنهٔ پیشنهادی ست بعدی (POST /ai/suggest-weight) ──

export interface WeightSuggestion {
  next_weight: number;
  action: "increase" | "decrease" | "hold";
  reason: string;
  rule_version: string;
}

export function suggestNextWeight(
  payload: { last_weight: number; reps_done: number; target_reps: number; rpe?: number | null },
  token = getToken(),
) {
  return postJson<WeightSuggestion>("/ai/suggest-weight", payload, token);
}

// ── G9 — کتابخانهٔ حرکات با تصویر (free-exercise-db، Unlicense) ──

export interface ExerciseRow {
  exercise_id: number;
  name_fa: string;
  name_en: string;
  muscle_group: string;
  equipment: string;
  difficulty: string;
  instructions_fa: string;
  image_url: string;
  image_url_alt: string;
  /** M60/R6 — انیمیشن اجرا؛ خالی یعنی ساخته نشده (به image_url برگرد). */
  gif_url: string;
}

export function browseExercises(
  muscleGroup: string | null = null,
  query = "",
  token = getToken(),
  signal?: AbortSignal,
) {
  const params = new URLSearchParams();
  if (muscleGroup) params.set("muscle_group", muscleGroup);
  if (query) params.set("q", query);
  const qs = params.toString();
  return getJson<ExerciseRow[]>(`/library/exercises${qs ? `?${qs}` : ""}`, token, signal);
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

// ── G8 — چت مربی–شاگرد ──

export interface ChatConversation {
  id: number;
  member_id: number;
  coach_id: number;
  subject: string;
  status: "open" | "closed" | string;
  last_message_at: string | null;
  created_at: string | null;
}

export interface ChatMessage {
  id: number;
  conversation_id: number;
  sender_id: number;
  sender_role: "member" | "coach" | string;
  body: string;
  is_system: boolean;
  read_at: string | null;
  created_at: string | null;
}

export interface ChatMessages {
  conversation_id: number;
  messages: ChatMessage[];
  unread_count: number;
  rule_version: string;
}

export function fetchConversations(memberId?: number, token = getToken(), signal?: AbortSignal) {
  const q = memberId !== undefined ? `?member_id=${memberId}` : "";
  return getJson<ChatConversation[]>(`/chat/conversations${q}`, token, signal);
}

export function openConversation(
  memberId: number,
  subject: string,
  token = getToken(),
) {
  return postJson<ChatConversation>(
    "/chat/conversations",
    { member_id: memberId, subject },
    token,
  );
}

export function fetchMessages(
  conversationId: number,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<ChatMessages>(
    `/chat/conversations/${conversationId}/messages`,
    token,
    signal,
  );
}

export function sendMessage(
  conversationId: number,
  body: string,
  token = getToken(),
) {
  return postJson<ChatMessage>(
    `/chat/conversations/${conversationId}/messages`,
    { body },
    token,
  );
}

export function markConversationRead(conversationId: number, token = getToken()) {
  return postJson<{ marked_read: number; rule_version: string }>(
    `/chat/conversations/${conversationId}/read`,
    {},
    token,
  );
}

// ── M54-c1 — آنالیز سگمنتال آنتروپومتریک (D-024) ──

export interface LimbMeasurement {
  id: number;
  member_id: number;
  measured_at: string | null;
  neck_cm: number | null;
  chest_cm: number | null;
  waist_cm: number | null;
  hip_cm: number | null;
  upper_arm_right_cm: number | null;
  upper_arm_left_cm: number | null;
  thigh_right_cm: number | null;
  thigh_left_cm: number | null;
  calf_right_cm: number | null;
  calf_left_cm: number | null;
  quality: string | null;
  notes: string;
}

export interface SegmentalRatio {
  value: number | null;
  band: string;
  reason: string;
  threshold: number;
}

export interface SegmentalAsymmetry {
  right_cm: number;
  left_cm: number;
  delta_cm: number;
  dominant_side: "right" | "left" | "equal";
  band: "normal" | "mild" | "notable";
  reason: string;
  threshold_cm: number;
}

export interface SegmentalReport {
  member_id: number;
  latest: LimbMeasurement | null;
  analysis: {
    ratios: {
      waist_to_height: SegmentalRatio;
      waist_to_hip: SegmentalRatio;
      arm_to_waist: SegmentalRatio;
    };
    asymmetry: {
      upper_arm: SegmentalAsymmetry | null;
      thigh: SegmentalAsymmetry | null;
      calf: SegmentalAsymmetry | null;
    };
    headline: string;
    missing: string[];
    note: string;
    rule_version: string;
  } | null;
  trend: {
    span_days: number;
    changes_cm: Record<string, number | null>;
    biggest_change: string | null;
    headline: string;
    rule_version: string;
  } | null;
  measurements_count: number;
  reason: string;
  note: string;
  rule_version: string;
}

export function fetchSegmentalReport(
  memberId: number,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<SegmentalReport>(
    `/assessments/limb/member/${memberId}/report`,
    token,
    signal,
  );
}

export function recordLimbMeasurement(
  memberId: number,
  values: Record<string, number | null>,
  token = getToken(),
) {
  const body: Record<string, unknown> = { member_id: memberId };
  for (const [k, v] of Object.entries(values)) {
    if (v !== null && v !== undefined && !Number.isNaN(v)) body[k] = v;
  }
  return postJson<LimbMeasurement>("/assessments/limb", body, token);
}

// ── G11 — یادآوری‌های پویا ──

export interface Reminder {
  key: string;
  priority: "high" | "normal";
  title: string;
  body: string;
  due_in_days: number;
  rule: string;
}

export interface ReminderSkipped {
  key: string;
  reason: string;
}

export interface RemindersReport {
  member_id: number;
  generated_at: string;
  reminders: Reminder[];
  skipped: ReminderSkipped[];
  counts: { due: number; skipped: number };
  thresholds: {
    renewal_lead_days: number;
    inactivity_days: number;
    reassess_days: number;
  };
  rule_version: string;
  created_notifications: number;
  data_sources: Record<string, boolean>;
}

export function fetchReminders(
  memberId: number,
  token = getToken(),
  signal?: AbortSignal,
) {
  return getJson<RemindersReport>(
    `/notifications/reminders/member/${memberId}`,
    token,
    signal,
  );
}

// ── M59 — فروشگاه، کیف‌پول، درگاه، دفتر قیمت، درخواست تأیید ──

async function sendJson<T>(
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  body: unknown,
  token: string | null,
): Promise<T> {
  let resp: Response;
  try {
    resp = await sessionFetch(`${API_BASE}${path}`, {
      method,
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("اتصال به سرور برقرار نشد", 0);
  }
  if (resp.status === 401 || resp.status === 403) await throwAuthOrForbidden(resp);
  if (!resp.ok) {
    const detail = (await resp.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new ApiError(detail?.error?.message ?? `خطای ${resp.status}`, resp.status);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export interface ShopVariant {
  id: number;
  label: string;
  price_rial: number;
  stock_qty: number;
  is_active: boolean;
}

export interface ShopProduct {
  id: number;
  sku: string;
  title: string;
  subtitle: string;
  description: string;
  price_rial: number;
  compare_at_rial: number | null;
  image_url: string;
  gallery: string[];
  category_id: number;
  stock_qty: number;
  is_active: boolean;
  variants: ShopVariant[];
}

export interface ShopCategory {
  id: number;
  slug: string;
  title: string;
  kind: "equipment" | "supplement" | "apparel" | "service";
  sort_order: number;
  is_active: boolean;
}

export interface CartLine {
  id: number;
  product_id: number;
  variant_id: number | null;
  title: string;
  variant_label: string;
  image_url: string;
  unit_price_rial: number;
  qty: number;
  line_total_rial: number;
}

export interface ShopCart {
  member_id: number;
  items: CartLine[];
  total_rial: number;
  count: number;
}

export interface ShopOrder {
  id: number;
  member_id: number;
  status: "pending" | "paid" | "failed" | "cancelled" | "delivered";
  total_rial: number;
  payment_id: number | null;
  note: string;
  created_at: string;
  items: {
    product_id: number;
    title: string;
    unit_price_rial: number;
    qty: number;
  }[];
}

export interface ShopGateway {
  id: number;
  kind: "zarinpal" | "idpay" | "card_to_card" | "cash";
  title: string;
  is_enabled: boolean;
  card_number_masked: string;
  card_holder: string;
  bank_name: string;
  public_key: string;
  instructions: string;
  secret_configured: boolean;
}

export interface PriceRow {
  id: number;
  category: "membership" | "coach_fee" | "program_fee";
  code: string;
  title: string;
  price_rial: number;
  duration_days: number | null;
  gender: string;
  effective_from?: string;
}

export interface ChangeRequest {
  id: number;
  kind: string;
  kind_label: string;
  payload: Record<string, unknown>;
  requested_by: number;
  status: "pending" | "approved" | "rejected";
  reviewed_by: number | null;
  reviewed_at: string | null;
  review_note: string;
  result: Record<string, unknown>;
  created_at: string;
}

export const fetchShopProducts = (
  params: { category?: string; kind?: string; search?: string } = {},
  token = getToken(),
  signal?: AbortSignal,
) => {
  const qs = new URLSearchParams();
  if (params.category) qs.set("category", params.category);
  if (params.kind) qs.set("kind", params.kind);
  if (params.search) qs.set("search", params.search);
  const suffix = qs.toString() ? `?${qs}` : "";
  return getJson<ShopProduct[]>(`/shop/products${suffix}`, token, signal);
};

export const fetchShopCategories = (token = getToken(), signal?: AbortSignal) =>
  getJson<ShopCategory[]>("/shop/categories", token, signal);

export const fetchCart = (token = getToken(), signal?: AbortSignal) =>
  getJson<ShopCart>("/shop/cart", token, signal);

export const addCartItem = (
  productId: number,
  qty = 1,
  variantId: number | null = null,
  token = getToken(),
) => sendJson<ShopCart>("POST", "/shop/cart", { product_id: productId, qty, variant_id: variantId }, token);

export const updateCartItem = (itemId: number, qty: number, token = getToken()) =>
  sendJson<ShopCart>("PATCH", `/shop/cart/${itemId}`, { qty }, token);

export const removeCartItem = (itemId: number, token = getToken()) =>
  sendJson<ShopCart>("DELETE", `/shop/cart/${itemId}`, undefined, token);

export const checkoutCart = (method: "wallet" | "zarinpal" | "card" | "cash" = "wallet", token = getToken()) =>
  sendJson<{ order_id: number; status: string; total_rial: number; payment_id: number | null }>(
    "POST",
    "/shop/checkout",
    { method },
    token,
  );

export const fetchShopOrders = (token = getToken(), signal?: AbortSignal) =>
  getJson<ShopOrder[]>("/shop/orders", token, signal);

export interface OrderReceipt {
  receipt_no: string;
  order_id: number;
  member_id: number;
  member_name: string | null;
  status: ShopOrder["status"];
  note: string;
  created_at: string | null;
  lines: {
    product_id: number;
    title: string;
    variant: string | null;
    unit_price_rial: number;
    qty: number;
    line_total_rial: number;
  }[];
  items_total_rial: number;
  total_rial: number;
  payment: {
    id: number;
    method: string;
    status: string;
    reference_id: string | null;
    paid_at: string | null;
  } | null;
  issued_at: string;
  branch: string;
}

/**
 * رسید سفارش (M60/R5).
 *
 * چرا مسیر جدا از `/shop/orders`: آن پاسخ برای لیست است (فقط عنوان/تعداد)،
 * این یکی اقلام با واریانت + وضعیت پرداخت + نام عضو را می‌دهد — همان چیزی
 * که انباردار برای تحویل چاپ می‌کند. کنترل مالکیت سمت سرور است.
 */
export const fetchOrderReceipt = (orderId: number, token = getToken(), signal?: AbortSignal) =>
  getJson<OrderReceipt>(`/shop/orders/${orderId}/receipt`, token, signal);

export const markOrderStatus = (orderId: number, status: ShopOrder["status"], token = getToken()) =>
  sendJson<{ id: number; status: string }>("PATCH", `/shop/orders/${orderId}`, { status }, token);

export const fetchGateways = (token = getToken(), signal?: AbortSignal) =>
  getJson<ShopGateway[]>("/shop/gateways", token, signal);

export interface GatewayInput {
  kind: ShopGateway["kind"];
  title: string;
  is_enabled?: boolean;
  /** فقط هنگام نوشتن؛ در پاسخ فقط `card_number_masked` برمی‌گردد. */
  card_number?: string;
  card_holder?: string;
  bank_name?: string;
  public_key?: string;
  secret_key?: string;
  instructions?: string;
}

export const upsertGateway = (
  payload: GatewayInput,
  gatewayId?: number,
  token = getToken(),
) =>
  sendJson<ShopGateway>(
    gatewayId ? "PUT" : "POST",
    gatewayId ? `/shop/gateways/${gatewayId}` : "/shop/gateways",
    payload,
    token,
  );

export const fetchPrices = (category?: PriceRow["category"], token = getToken(), signal?: AbortSignal) =>
  getJson<PriceRow[]>(`/shop/prices${category ? `?category=${category}` : ""}`, token, signal);

export const savePrice = (
  payload: {
    category: PriceRow["category"];
    code: string;
    title: string;
    price_rial: number;
    duration_days?: number | null;
    gender?: string;
  },
  token = getToken(),
) => sendJson<PriceRow>("POST", "/shop/prices", payload, token);

export const createProduct = (
  payload: {
    title: string;
    sku: string;
    category_id: number;
    price_rial: number;
    image_url?: string;
    stock_qty?: number;
    description?: string;
    variants?: { label: string; price_rial?: number | null; stock_qty?: number }[];
  },
  token = getToken(),
) => sendJson<ShopProduct>("POST", "/shop/products", payload, token);

export const updateProduct = (productId: number, payload: Record<string, unknown>, token = getToken()) =>
  sendJson<ShopProduct>("PATCH", `/shop/products/${productId}`, payload, token);

export const fetchChangeRequests = (token = getToken(), signal?: AbortSignal) =>
  getJson<ChangeRequest[]>("/shop/change-requests", token, signal);

export const askChangeRequest = (kind: string, payload: Record<string, unknown>, token = getToken()) =>
  sendJson<ChangeRequest>("POST", "/shop/change-requests", { kind, payload }, token);

export const reviewChangeRequest = (
  requestId: number,
  approve: boolean,
  note = "",
  token = getToken(),
) =>
  sendJson<ChangeRequest>("POST", `/shop/change-requests/${requestId}/review`, { approve, note }, token);
