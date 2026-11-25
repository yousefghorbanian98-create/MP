/**
 * گیت «هیچ مسیر دکوراتیو» — هر مسیر API باید مصرف‌کنندهٔ واقعی در Studio/mobile
 * داشته باشد یا استثنای صریح و قابل‌راستی‌آزمایی داشته باشد.
 *
 * چرا: در همین پروژه `Exercise.video_url` همیشه خالی و بی‌مصرف بود،
 * `KpiCard` ساخته و تست شد ولی هیچ‌جا سوار نشد، و `UpdateBanner` کامل
 * بود ولی کاربر هرگز آن را نمی‌دید. این تست همان رده باگ را می‌بندد.
 *
 * شمارش API callها از AST تایپ‌اسکریپت و tokenهای Dart انجام می‌شود؛ متن
 * comment/string به‌تنهایی مصرف‌کننده محسوب نمی‌شود. استثناها باید **دلیل** داشته باشند.
 */
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import * as ts from "typescript";
import { describe, expect, it } from "vitest";

/**
 * استثناهای پوشش: مسیرهایی که Studio/mobile مستقیماً صدا نمی‌زنند، اما
 * مصرف‌کنندهٔ عملیاتی/بیرونی دارند یا عمداً در backlog مانده‌اند.
 *
 * M61/D6 — این ساختار عوض شد چون گیت **دروغ** می‌گفت: قبلاً مقدار هر ردیف
 * فقط یک **متن** بود، و تست فقط طول متن را می‌سنجید («دلیل > ۵ کاراکتر»).
 * نتیجه: چهار ردیف مصرف‌کننده‌ای را نام می‌بردند که وجود نداشت:
 *   • `/auth/logout`  → «اپ Dart توکن را پاک می‌کند» — نمی‌کرد
 *   • `/face/privacy-notice` → «نسخهٔ متنی در اپ Dart» — صفر ارجاع
 *   • `/notifications/member/{id}` → «از مسیر /notifications می‌آید» — صفر ارجاع
 *   • `/members/memberships/plans` → «اپ از /members/memberships می‌خواند» — مسیر دیگری
 * اکنون هر ردیف باید `evidence` واقعی داشته باشد، یا `evidence: null` و
 * توضیح بیرونی/TODO روشن. `fileEvidence` برای استثنایی که در repo شاهد متنی
 * دارد، مسیر فایل را مشخص می‌کند و در تست بررسی می‌شود.
 */
interface Exception {
  /** چرا این مسیر امروز call مستقیمی از Studio/mobile ندارد. */
  why: string;
  /** مسیر واقعی API call در Studio/mobile؛ `null` = بدون call مستقیم در این دو اپ. */
  evidence: string | null;
  /** مصرف‌کنندهٔ خارج از دو اپ یا TODO صریح برای مسیرِ بدون مصرف‌کننده. */
  external?: string;
  /** فایل در repo که شاهد استثنا/مصرف‌کننده را دارد؛ مسیر نسبت به ریشهٔ repo. */
  fileEvidence?: string;
}

const ROUTE_EXCEPTIONS: Record<string, Exception> = {
  // WP 4.4 (B2): updateProduct حذف شد چون هیچ کدام از Studio و Client آن را صدا نمی‌زد.
  // بک‌اند PATCH را نگه می‌دارد؛ UI ویرایش قیمت/محصول هنوز ساخته نشده است.
  "/api/v1/shop/products/{product_id}": {
    why: "PATCH ویرایش محصول — بدون مصرف‌کنندهٔ Studio/Client پس از حذف updateProduct (WP 4.4)",
    evidence: null,
    external: "TODO: فرم ویرایش محصول در Studio یا حذف رسمی PATCH از بک‌اند",
  },
  // این مسیر در Flutter «پیشرفت» مصرف می‌شود، بیرون از Studio.
  // QF-23: گزارش زمان‌بندی‌شده backend has no Studio screen yet; the owner reads
  // numbers from the finance panel. The gate stays honest instead of inventing UI.
  "/api/v1/finance/reports/schedule": {
    why: "وضعیت اجرای گزارش روزانه؛ UI آن در QF-10/32 ساخته می‌شود",
    evidence: null,
    external: "TODO: نمایش برنامه/اجرای گزارش در صفحهٔ تحلیل‌ها",
  },
  "/api/v1/finance/reports/schedule/{job_key}/run": {
    why: "اجرای دستی گزارش — فعلاً از CLI/scheduler و با finance.write",
    evidence: null,
    external: "TODO: دکمهٔ اجرای دستی برای مالک در UI",
  },
  "/api/v1/finance/reports/daily/{run_date}": {
    why: "خواندن گزارش یک روز؛ مصرف‌کنندهٔ واقعی هنوز صفحهٔ گزارش نیست",
    evidence: null,
    external: "TODO: صفحهٔ گزارش روزانه با نمودار در QF-10",
  },
  // QF-28: نگهداری داده یک ابزار عملیاتی مالک است؛ عمداً در UI عمومی نیست.
  "/api/v1/admin/retention": {
    why: "پیش‌نمایش حذف دادهٔ منقضی — فقط super_admin، ابزار عملیاتی",
    evidence: null,
    external: "TODO: صفحهٔ حریم/نگهداری با تأیید دومرحله‌ای برای مالک",
  },
  "/api/v1/admin/retention/run": {
    why: "اجرای حذف دادهٔ منقضی — از CLI/runbook، نه دکمهٔ روزمره",
    evidence: null,
    external: "TODO: اجرای زمان‌بندی‌شده با ممیزی + UI مالک",
  },
  "/api/v1/assessments/member/{member_id}": {
    why: "اپ Flutter از همین مسیر در «پیشرفت» می‌خواند",
    evidence: "/assessments/member/",
  },
  "/api/v1/assessments": {
    why: "ثبت ارزیابی قدیمیِ ۱۴ دامنه در Studio/mobile مصرف‌کننده ندارد؛ UI فعلی از axis-assessments استفاده می‌کند",
    evidence: null,
    external: "TODO: اتصال یا حذف مسیر قدیمی ثبت ارزیابی",
  },
  "/api/v1/assessments/jp7": {
    why: "مسیر POST برای ثبت JP7 است؛ UI فعلی فقط روند JP7 را می‌خواند و ورودی اندازه‌گیری ندارد",
    evidence: null,
    external: "TODO: capture/entry flow برای اندازه‌گیری JP7",
  },
  "/api/v1/nutrition/plans": {
    why: "route مستقیم به service.create_plan_from_engine وصل است؛ apps از /ai/nutrition/generate به همان service می‌رسند، نه از این path",
    evidence: null,
    external: "TODO: تأیید مصرف بیرونی یا deprecate کردن مسیر direct-create",
  },
  "/api/v1/nutrition/plans/{plan_id}/approve": {
    why: "نمایش target تغذیه هست، اما UI تأیید مربی برای plan ندارد",
    evidence: null,
    external: "TODO: افزودن action تأیید مربی یا حذف endpoint بلااستفاده",
  },
  "/api/v1/axis-assessments/{assessment_id}/review": {
    why: "Studio/mobile ماتریس ارزیابی را می‌خواند/ثبت می‌کند، ولی UI بازبینی admin ندارد",
    evidence: null,
    external: "TODO: workflow تأیید/رد ارزیابی و audit را به UI وصل کنید",
  },
  "/api/v1/payments/wallet/pay": {
    why: "اپ خرید را از /shop/checkout انجام می‌دهد؛ endpoint پرداخت مستقیم کیف‌پول consumer داخل app ندارد",
    evidence: null,
    external: "TODO: تأیید caller بیرونی یا حذف route مستقیم پس از بررسی",
  },
  "/api/v1/payments/{payment_id}/gateway-return": {
    why: "این مسیر را بانکِ واقعی با GET مرورگر باز می‌کند (redirect after pay)، نه کدِ اپ؛ مصرف‌کنندهٔ آن مرورگرِ کاربر است",
    evidence: null,
    external: "صفحهٔ پرداختِ بانک (devtools/sandbox_bank.py و درگاه واقعی) کاربر را به همین مسیر برمی‌گرداند",
    fileEvidence: "mp-app/backend/modules/payments/router.py",
  },
  "/api/v1/payments/{payment_id}/start": {
    why: "فاز ۳: درگاه اینترنتی حذف شد؛ این مسیر فقط برای هارنس صندباکس محلی می‌ماند و در حالت manual با ۴۰۹ بسته است",
    evidence: null,
    external: "TODO: هارنس آزمایش محلی (devtools/sandbox_bank.py)؛ در production خاموش است",
  },
  "/api/v1/payments/{payment_id}/callback": {
    why: "همان مرز start: callback فقط برای صندباکس محلی معنا دارد و در حالت manual هرگز باز نمی‌شود",
    evidence: null,
    external: "TODO: هارنس آزمایش محلی (devtools/sandbox_bank.py)؛ در production خاموش است",
  },
  // ابزارهای عملیاتی، نه کاربر نهایی
  "/api/v1/metrics": {
    why: "Prometheus scrape می‌کند — مصرف‌کننده در infra/monitoring است، نه در دو اپ",
    evidence: null,
    external: "Prometheus (mp-app/infra/monitoring/prometheus.yml)",
    fileEvidence: "mp-app/infra/monitoring/prometheus.yml",
  },
  "/api/v1/health/ready": {
    why: "Readiness probe is used by operations; Studio uses the separate /health endpoint.",
    evidence: null,
    external: "mp-app/infra/scripts/healthcheck.sh",
    fileEvidence: "mp-app/infra/scripts/healthcheck.sh",
  },
  "/api/v1/admin/flags/{key}": {
    why: "Studio lists and updates flags through /admin/flags; no client looks up one flag by key",
    evidence: null,
    external: "TODO: use the single-flag GET route or retire it",
  },
  "/api/v1/library/exercises/{exercise_id}": {
    why: "ExerciseLibrary only browses/filter lists; there is no exercise-detail screen",
    evidence: null,
    external: "TODO: add exercise details or retire the unused detail route",
  },
  "/api/v1/reports/confidential/{member_id}": {
    why: "گزارش staff-only حساس با ownership/audit است؛ صفحهٔ نمایش/چاپ در Studio/mobile وجود ندارد",
    evidence: null,
    external: "TODO: جریان امن نمایش/چاپ گزارش برای staff؛ token یک‌بارمصرف در این route دیده نشد",
  },
  // M87 — outbox محدودِ بازخورد ساختاریافته در Flutter.
  "/api/v1/programs/sync/set-feedback": {
    why: "صف آفلاین owner-scoped برای بازخورد ساختاریافته از Flutter به همین endpoint sync می‌کند",
    evidence: "/programs/sync/set-feedback",
  },
  "/api/v1/programs/from-engine": {
    why: "UIها از /ai/program/generate استفاده می‌کنند که همان service را صدا می‌زند؛ route مستقیم consumer شناخته‌شده‌ای ندارد",
    evidence: null,
    external: "TODO: تأیید caller بیرونیِ import/migration یا deprecate کردن route مستقیم",
  },
  "/api/v1/classes/cancel": {
    why: "اپ Dart رزرو عضو را از مسیر لغو می‌کند و پس از آن فهرست را تازه می‌خواند",
    evidence: "/classes/cancel",
  },
  "/api/v1/payments/wallet/charge": {
    why: "این مسیر شارژ دستیِ کیف‌پول و پذیرش-only است؛ هیچ‌یک از دو اپ آن را مستقیم صدا نمی‌زند",
    evidence: null,
    external: "عملیات پذیرش برای اعتبار کیف‌پول؛ نه اتصال درگاه واقعی",
    fileEvidence: "docs/MuscleParadise/ACCESS-AUDIT-2026-11-15.md",
  },
  "/api/v1/payments/invoice/{member_id}": {
    why: "endpoint فاکتور تجمیعی در backend وجود دارد؛ هیچ صفحهٔ پرداخت/چاپ در دو اپ آن را مصرف نمی‌کند",
    evidence: null,
    external: "TODO: اتصال فاکتور مالی به جریان پذیرش/چاپ؛ هیچ token کوتاه‌عمری در مسیر تأیید نشد",
  },
  "/api/v1/members/memberships/{membership_id}/invoice": {
    why: "endpoint صورتحساب اشتراک هست، اما صفحهٔ عضویت/چاپی که آن را مصرف کند وجود ندارد",
    evidence: null,
    external: "TODO: اتصال صورتحساب اشتراک به جریان staff؛ بدون ادعای consumer موجود",
  },
  "/api/v1/members/memberships/from-plan": {
    why: "UI آن را صدا نمی‌زند و service فعلی مستقیماً اشتراک می‌سازد، بدون تأیید پرداخت",
    evidence: null,
    external: "TODO: فقط پس از طراحی تأیید پرداخت/مجوز کسب‌وکار به UI وصل شود",
  },
  "/api/v1/members/memberships/plans": {
    // M61/D6: این route هنوز consumer ندارد. اپ فقط تاریخچهٔ عضو را از
    // `/members/{member_id}/memberships` می‌خواند؛ آن با لیست پلن‌ها فرق دارد.
    why: "انتخاب/نمایش پلن عضویت در Studio/mobile هنوز به این endpoint وصل نیست",
    evidence: null,
    external: "TODO: اتصال فهرست پلن‌ها به جریان خرید/تمدید عضویت",
  },
  "/api/v1/members": {
    why: "فهرست/ثبت مستقیم عضو UI ندارد؛ جدول Studio از /admin/members-summary داده می‌گیرد",
    evidence: null,
    external: "TODO: ثبت‌نام و فهرست مستقیم اعضا یا حذف route بلااستفاده",
  },
  "/api/v1/members/memberships": {
    why: "ایجاد اشتراک دستی UI ندارد؛ اپ فقط تاریخچه می‌خواند و خرید فروشگاهی مسیر جدا دارد",
    evidence: null,
    external: "TODO: اتصال ایجاد/تمدید دستی اشتراک به صفحهٔ عضویت",
  },
  // چهره
  "/api/v1/face/enroll": {
    why: "ساخت embedding و تطبیق معتبر سمت سرور پیاده نیست؛ مسیر ثبت چهره در اپ فعال نیست",
    evidence: null,
    external: "TODO: ابزار امن ثبت چهره برای کارکنان/کیوسک؛ تا طراحی رضایت، کنترل دسترسی و چرخهٔ حذف تکمیل نشود، مصرف‌کننده‌ای ادعا نمی‌شود",
  },
  "/api/v1/face/checkin": {
    why: "چک‌این چهره بدون probe معتبر و liveness باید fail-closed بماند؛ API با 409 رد می‌کند",
    evidence: null,
    external: "TODO: فقط پس از طراحی و پیاده‌سازی تطبیق و liveness سمت سرور، با آزمون حریم خصوصی و دستگاهی فعال شود",
  },
  "/api/v1/face/enroll/{member_id}": {
    why: "حذف template چهره در Studio/mobile UI ندارد؛ صرفاً endpoint حریم خصوصی است",
    evidence: null,
    external: "TODO: مسیر حذف چهره از تنظیمات حریم خصوصی",
  },
  "/api/v1/face/consent": {
    // M61/D1: اپ حالا رضایت را می‌گیرد؛ ادعای قبلی «اپ ندارد» منسوخ شد.
    why: "اپ Dart دکمهٔ رضایت بیومتریک دارد",
    evidence: "/face/consent",
  },
  "/api/v1/face/consent/revoke": {
    why: "پس‌گرفتن رضایت هنوز در UI نیست — یک TODO است (S4 در TODO-2026-11-16)",
    evidence: null,
    external: "TODO: S4 — پس‌گرفتن رضایت",
  },
  "/api/v1/face/checkin-qr": {
    why: "اسکنر QR (کیوسک/پذیرش) ساخته نشده — TODO: S5",
    evidence: null,
    external: "TODO: S5 — اسکنر کیوسک",
  },
  "/api/v1/face/checkins/{checkin_id}/exit": {
    why: "ثبت خروج از کیوسک — TODO: S5",
    evidence: null,
    external: "TODO: S5 — ثبت خروج",
  },
  "/api/v1/face/deep-status": {
    why: "پنل تشخیصی مدل — استودیو نمایشش نمی‌دهد",
    evidence: null,
    external: "TODO: پنل تشخیصی",
  },
  "/api/v1/face/privacy-notice": {
    // M61/D6: ادعای قبلی («نسخهٔ متنی در اپ») کاذب بود. اپ متن را از سرور
    // می‌خواند و در صفحهٔ چک‌این نشان می‌دهد.
    why: "اپ Dart متن اطلاعیه را پیش از رضایت نشان می‌دهد",
    evidence: "/face/privacy-notice",
  },
  // احراز هویت
  "/api/v1/auth/logout": {
    // M61/D3: ادعای قبلی («اپ توکن را پاک می‌کند») کاذب بود — خروج وجود نداشت.
    why: "اپ Dart خروج را با ارسال refresh token انجام می‌دهد",
    evidence: "/auth/logout",
  },
  "/api/v1/auth/logout-all": {
    why: "ابطال همهٔ نشست‌ها از پنل امنیتی — UI ندارد، TODO",
    evidence: null,
    external: "TODO: پنل امنیتی",
  },
  // اعلان و جمعیت
  "/api/v1/notifications": {
    why: "مسیر ارسال دستی اعلان در Studio/mobile فراخوانی نمی‌شود؛ پنل موجود فقط یادآوری‌ها را می‌خواند",
    evidence: null,
    external: "TODO: ساخت جریان ارسال اعلان یا اتصال به سرویس اعلان بیرونی",
  },
  "/api/v1/notifications/{notification_id}/read": {
    why: "اپ Dart وضعیت خوانده‌شدن اعلان عضو را در inbox ثبت می‌کند",
    evidence: "/notifications/$notificationId/read",
  },
  "/api/v1/notifications/member/{member_id}": {
    // M75: inbox عضو از مسیر مخصوص خودش داده را می‌خواند؛ member_id از نشست می‌آید.
    why: "صفحهٔ اعلان عضو فهرست را از API موجود دریافت می‌کند",
    evidence: "/notifications/member/$memberId",
  },
  "/api/v1/population/intake/next": {
    why: "UI فقط /population/gate-check را صدا می‌زند؛ route صف پذیرش /population/intake/next consumer داخل اپ ندارد",
    evidence: null,
    external: "TODO: صف پذیرش",
  },
  "/api/v1/population/paths": {
    why: "پنل تحلیل جمعیت ساخته نشده",
    evidence: null,
    external: "TODO: پنل تحلیل",
  },
  "/api/v1/members/me/face-consent": {
    why: "اپ Dart وضعیت رضایت را می‌خواند (M61/D1)",
    evidence: "/members/me/face-consent",
  },
};

const ROUTES_FILE = join(__dirname, "..", "..", "backend", "api", "routes.json");
const STUDIO_SRC = join(__dirname, "..", "src");
const CLIENT = join(__dirname, "..", "..", "client", "lib");
const REPO_ROOT = join(__dirname, "..", "..", "..");

interface ApiCall {
  path: string;
  file: string;
}

function backendRoutes(): string[] {
  if (!existsSync(ROUTES_FILE)) {
    throw new Error(
      "api/routes.json نیست — python scripts/export_routes.py را اجرا کنید",
    );
  }
  const parsed = JSON.parse(readFileSync(ROUTES_FILE, "utf8")) as { paths: string[] };
  return parsed.paths;
}

function sourceFiles(root: string, extension: RegExp): string[] {
  const found: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (extension.test(entry.name)) found.push(full);
    }
  };
  walk(root);
  return found;
}

const BASE_NAMES = new Set(["API_BASE", "base", "baseUrl", "baseURL", "apiBase"]);
const QUERY_NAMES = new Set(["q", "qs", "suffix", "queryString", "searchParams"]);
const REQUEST_FUNCTIONS = new Set(["fetch", "sessionFetch", "getJson", "getBlob", "postJson", "sendJson"]);
const API_METHODS = new Set(["get", "post", "put", "patch", "delete", "request"]);
const API_OBJECTS = new Set(["api", "apiClient", "http", "httpClient"]);

function isBaseExpression(expression: ts.Expression): boolean {
  return (
    (ts.isIdentifier(expression) && BASE_NAMES.has(expression.text)) ||
    (ts.isPropertyAccessExpression(expression) && BASE_NAMES.has(expression.name.text))
  );
}

function isQueryExpression(expression: ts.Expression): boolean {
  if (ts.isIdentifier(expression)) return QUERY_NAMES.has(expression.text);
  if (!ts.isConditionalExpression(expression)) return false;
  const whenTrue = pathExpression(expression.whenTrue);
  const whenFalse = pathExpression(expression.whenFalse);
  const isQueryFragment = (value: string | null) => value === "" || value?.startsWith("?");
  return isQueryFragment(whenTrue) && isQueryFragment(whenFalse);
}

/** Extract a request target only from an expression; comments and string literals are never traversed. */
function pathExpression(expression: ts.Expression): string | null {
  if (ts.isParenthesizedExpression(expression)) return pathExpression(expression.expression);
  if (ts.isStringLiteralLike(expression) || ts.isNoSubstitutionTemplateLiteral(expression)) {
    return expression.text;
  }
  if (ts.isIdentifier(expression)) {
    if (BASE_NAMES.has(expression.text)) return "/api/v1";
    if (QUERY_NAMES.has(expression.text)) return "?";
    return null;
  }
  if (ts.isTemplateExpression(expression)) {
    let value = expression.head.text;
    for (const span of expression.templateSpans) {
      if (isBaseExpression(span.expression)) value += "/api/v1";
      else if (!value.includes("?") && !isQueryExpression(span.expression)) value += "{}";
      value += span.literal.text;
    }
    return value;
  }
  if (ts.isBinaryExpression(expression) && expression.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const left = pathExpression(expression.left);
    const right = pathExpression(expression.right);
    return left === null || right === null ? null : left + right;
  }
  if (ts.isConditionalExpression(expression) && isQueryExpression(expression)) return "?";
  return null;
}

function isApiObject(expression: ts.Expression): boolean {
  if (ts.isIdentifier(expression)) return API_OBJECTS.has(expression.text);
  if (ts.isPropertyAccessExpression(expression)) {
    return expression.name.text === "api" || isApiObject(expression.expression);
  }
  return false;
}

function isRequestCall(expression: ts.Expression): boolean {
  if (ts.isIdentifier(expression)) return REQUEST_FUNCTIONS.has(expression.text);
  return (
    ts.isPropertyAccessExpression(expression) &&
    API_METHODS.has(expression.name.text) &&
    isApiObject(expression.expression)
  );
}

function normalizeApiPath(raw: string): string | null {
  let path = raw.trim();
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) {
    try {
      path = new URL(path).pathname;
    } catch {
      return null;
    }
  }
  const queryStart = path.search(/[?#]/);
  if (queryStart >= 0) path = path.slice(0, queryStart);
  if (!path) return null;

  if (path !== "/health") {
    const apiIndex = path.indexOf("/api/v1");
    if (apiIndex >= 0) path = path.slice(apiIndex);
    else if (path.startsWith("/")) path = `/api/v1${path}`;
    else return null;
  }
  path = path.replace(/\/{2,}/g, "/");
  if (path.length > 1) path = path.replace(/\/+$/, "");
  return path;
}

function pathExpressions(expression: ts.Expression): string[] {
  if (ts.isParenthesizedExpression(expression)) return pathExpressions(expression.expression);
  if (ts.isConditionalExpression(expression)) {
    return [...pathExpressions(expression.whenTrue), ...pathExpressions(expression.whenFalse)];
  }
  const path = pathExpression(expression);
  return path === null ? [] : [path];
}

function scanTypeScript(source: string, file = "<inline.ts>"): ApiCall[] {
  const scriptKind = file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const sourceFile = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true, scriptKind);
  const calls: ApiCall[] = [];
  const visit = (node: ts.Node) => {
    if (ts.isCallExpression(node) && isRequestCall(node.expression)) {
      const pathIndex =
        ts.isIdentifier(node.expression) && node.expression.text === "sendJson" ? 1 : 0;
      const argument = node.arguments[pathIndex];
      if (argument) {
        for (const raw of pathExpressions(argument)) {
          const path = normalizeApiPath(raw);
          if (path) calls.push({ path, file });
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
  return calls;
}

interface DartToken {
  kind: "identifier" | "string" | "symbol";
  value: string;
}

function tokenizeDart(source: string): DartToken[] {
  const tokens: DartToken[] = [];
  let index = 0;
  while (index < source.length) {
    const char = source[index];
    if (/\s/.test(char)) {
      index += 1;
      continue;
    }
    if (char === "/" && source[index + 1] === "/") {
      index += 2;
      while (index < source.length && source[index] !== "\n") index += 1;
      continue;
    }
    if (char === "/" && source[index + 1] === "*") {
      index += 2;
      let depth = 1;
      while (index < source.length && depth > 0) {
        if (source[index] === "/" && source[index + 1] === "*") {
          depth += 1;
          index += 2;
        } else if (source[index] === "*" && source[index + 1] === "/") {
          depth -= 1;
          index += 2;
        } else {
          index += 1;
        }
      }
      continue;
    }

    const rawPrefix = (char === "r" || char === "R") && ["'", '"'].includes(source[index + 1]);
    const quoteIndex = rawPrefix ? index + 1 : index;
    if (source[quoteIndex] === "'" || source[quoteIndex] === '"') {
      const quote = source[quoteIndex];
      const delimiter = source.startsWith(quote.repeat(3), quoteIndex) ? quote.repeat(3) : quote;
      index = quoteIndex + delimiter.length;
      let value = "";
      while (index < source.length && !source.startsWith(delimiter, index)) {
        if (!rawPrefix && source[index] === "\\" && index + 1 < source.length) {
          value += source[index + 1];
          index += 2;
        } else {
          value += source[index];
          index += 1;
        }
      }
      index = Math.min(source.length, index + delimiter.length);
      tokens.push({ kind: "string", value });
      continue;
    }

    if (/[A-Za-z_]/.test(char)) {
      const start = index;
      index += 1;
      while (index < source.length && /[A-Za-z0-9_]/.test(source[index])) index += 1;
      tokens.push({ kind: "identifier", value: source.slice(start, index) });
      continue;
    }
    tokens.push({ kind: "symbol", value: char });
    index += 1;
  }
  return tokens;
}

function normalizeDartPath(raw: string): string | null {
  const expanded = raw.replace(/\$\{([^}]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g, (_match, expression, name) => {
    const variable = String(expression ?? name).trim();
    return BASE_NAMES.has(variable) ? "/api/v1" : "{}";
  });
  return normalizeApiPath(expanded);
}

function isRiverpodApiCall(tokens: DartToken[], methodIndex: number): boolean {
  if (tokens[methodIndex - 1]?.value !== ".") return false;
  let receiverIndex = methodIndex - 2;
  if (tokens[receiverIndex]?.value === "!" || tokens[receiverIndex]?.value === "?") {
    receiverIndex -= 1;
  }
  if (tokens[receiverIndex]?.value !== ")") return false;

  let depth = 0;
  let openIndex = -1;
  for (let index = receiverIndex; index >= 0; index -= 1) {
    if (tokens[index].value === ")") depth += 1;
    else if (tokens[index].value === "(") {
      depth -= 1;
      if (depth === 0) {
        openIndex = index;
        break;
      }
    }
  }
  if (openIndex < 3) return false;
  if (!["read", "watch"].includes(tokens[openIndex - 1]?.value ?? "")) return false;
  return tokens
    .slice(openIndex + 1, receiverIndex)
    .some((token) => token.kind === "identifier" && token.value === "apiClientProvider");
}

function scanDart(source: string, file = "<inline.dart>"): ApiCall[] {
  const tokens = tokenizeDart(source);
  const calls: ApiCall[] = [];
  const methods = new Set(["get", "post", "put", "patch", "delete"]);
  const apiNames = new Set(["api", "_api", "apiClient"]);

  const addCall = (methodIndex: number) => {
    let argumentIndex = methodIndex + 2;
    if (tokens[argumentIndex]?.kind === "identifier" && tokens[argumentIndex].value === "Uri") {
      if (
        tokens[argumentIndex + 1]?.value === "." &&
        tokens[argumentIndex + 2]?.value === "parse" &&
        tokens[argumentIndex + 3]?.value === "("
      ) {
        argumentIndex += 4;
      }
    }
    if (tokens[argumentIndex]?.kind !== "string") return;
    const path = normalizeDartPath(tokens[argumentIndex].value);
    if (path) calls.push({ path, file });
  };

  // Direct aliases: `api.get(...)`, `_api.post(...)`, or `apiClient.get(...)`.
  for (let index = 0; index < tokens.length - 3; index += 1) {
    if (tokens[index].kind !== "identifier" || !apiNames.has(tokens[index].value)) continue;
    let methodIndex = index + 1;
    if (tokens[methodIndex]?.value === "!" || tokens[methodIndex]?.value === "?") methodIndex += 1;
    if (
      tokens[methodIndex]?.value !== "." ||
      tokens[methodIndex + 1]?.kind !== "identifier" ||
      !methods.has(tokens[methodIndex + 1].value) ||
      tokens[methodIndex + 2]?.value !== "("
    ) {
      continue;
    }
    addCall(methodIndex + 1);
  }

  // Riverpod's common provider chain was previously invisible to this gate:
  // `ref.read(apiClientProvider).post(...)` (and `watch`) is a real API call,
  // not decorative text. Match only the provider expression as the receiver.
  for (let methodIndex = 0; methodIndex < tokens.length - 2; methodIndex += 1) {
    if (
      tokens[methodIndex].kind !== "identifier" ||
      !methods.has(tokens[methodIndex].value) ||
      tokens[methodIndex + 1]?.value !== "(" ||
      !isRiverpodApiCall(tokens, methodIndex)
    ) {
      continue;
    }
    addCall(methodIndex);
  }
  return calls;
}

function repositoryApiCalls(): ApiCall[] {
  const studioCalls = sourceFiles(STUDIO_SRC, /\.(ts|tsx)$/).flatMap((file) =>
    scanTypeScript(readFileSync(file, "utf8"), file),
  );
  const clientCalls = sourceFiles(CLIENT, /\.dart$/).flatMap((file) =>
    scanDart(readFileSync(file, "utf8"), file),
  );
  return [...studioCalls, ...clientCalls];
}

function isParameter(segment: string): boolean {
  return segment === "{}" || /^\{[^{}]+\}$/.test(segment) || /^:[A-Za-z_][A-Za-z0-9_]*$/.test(segment);
}

function routeMatchesPath(route: string, path: string): boolean {
  const normalizedRoute = normalizeApiPath(route);
  const normalizedPath = normalizeApiPath(path);
  if (!normalizedRoute || !normalizedPath) return false;
  const routeParts = normalizedRoute.split("/").filter(Boolean);
  const pathParts = normalizedPath.split("/").filter(Boolean);
  if (routeParts.length !== pathParts.length) return false;
  // Only a backend route parameter may match a concrete client path (or its
  // extracted `{}` placeholder). A dynamic client segment must not wildcard a
  // static backend segment — e.g. `/payments/{id}/receipt` is not an invoice.
  return routeParts.every((part, index) => part === pathParts[index] || isParameter(part));
}

function missingRoutes(routes: string[], calls: ApiCall[]): string[] {
  return routes.filter(
    (route) =>
      !calls.some((call) => routeMatchesPath(route, call.path)) &&
      ROUTE_EXCEPTIONS[route] === undefined,
  );
}

function evidenceMatches(route: string, evidence: string, calls: ApiCall[]): boolean {
  const fragment = evidence.replace(/\$\{([^}]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)/g, "{}");
  return calls.some((call) => call.path.includes(fragment) && routeMatchesPath(route, call.path));
}

describe("no decorative API surface", () => {
  it("counts only real API calls, not matching comments or string literals", () => {
    const route = "/api/v1/__m71_probe/{member_id}";
    const commentAndStringOnly = `
      // sessionFetch("/api/v1/__m71_probe/123")
      const note = "api.get('/__m71_probe/123')";
      /* api.post('/__m71_probe/123', {}) */
    `;
    const fakeCalls = [
      ...scanTypeScript(commentAndStringOnly),
      ...scanDart(commentAndStringOnly),
    ];
    expect(routeMatchesPath(route, route)).toBe(true);
    expect(missingRoutes([route], fakeCalls)).toEqual([route]);
    expect(
      routeMatchesPath(
        "/api/v1/payments/invoice/{member_id}",
        "/api/v1/payments/{paymentId}/receipt",
      ),
    ).toBe(false);

    const realCalls = [
      ...scanTypeScript('sessionFetch(`${API_BASE}/__m71_probe/${memberId}`);'),
      ...scanDart("await api.get('/__m71_probe/$memberId');"),
      ...scanDart("await ref.read(apiClientProvider).post('/__m71_probe/$memberId', {});"),
    ];
    expect(missingRoutes([route], realCalls)).toEqual([]);

    const conditionalCalls = scanTypeScript(
      'getJson(gatewayId ? `/shop/gateways/${gatewayId}` : "/shop/gateways", token);',
    );
    expect(conditionalCalls.map((call) => call.path)).toEqual([
      "/api/v1/shop/gateways/{}",
      "/api/v1/shop/gateways",
    ]);
    expect(missingRoutes(["/api/v1/shop/gateways/{gateway_id}"], conditionalCalls)).toEqual([]);
  });

  it("each backend path is used by a real Studio/Client API call or has a documented exception", () => {
    const routes = backendRoutes();
    expect(routes.length).toBeGreaterThan(50);

    const calls = repositoryApiCalls();
    const missing = missingRoutes(routes, calls);
    expect(missing, `مسیر بدون call واقعی و exception مستند: ${missing.join(", ")}`).toEqual([]);
  });

  it("every exception maps to a backend route and has verifiable call/external/TODO evidence", () => {
    const calls = repositoryApiCalls();
    const backendRouteSet = new Set(backendRoutes());
    const problems: string[] = [];

    for (const [route, exception] of Object.entries(ROUTE_EXCEPTIONS)) {
      expect(route.startsWith("/api/v1/"), `${route} باید /api/v1 باشد`).toBe(true);
      expect(exception.why.length, `${route}: دلیل خالی است`).toBeGreaterThan(5);
      if (!backendRouteSet.has(route)) problems.push(`${route}: دیگر در routes.json نیست؛ exception کهنه را حذف کنید`);

      if (exception.evidence === null) {
        expect(exception.external, `${route}: بدون evidence باید external/TODO داشته باشد`).toBeTruthy();
        expect((exception.external ?? "").length, `${route}: external/TODO باید توضیح داشته باشد`).toBeGreaterThan(5);
        const isTodo = exception.external?.startsWith("TODO") ?? false;
        if (!isTodo && !exception.fileEvidence) {
          problems.push(`${route}: ادعای external consumer بدون fileEvidence است`);
        }
        if (exception.fileEvidence) {
          const file = join(REPO_ROOT, exception.fileEvidence);
          if (!existsSync(file)) {
            problems.push(`${route}: file evidence «${exception.fileEvidence}» وجود ندارد`);
          } else {
            const externalText = readFileSync(file, "utf8");
            const endpointTail = route.replace("/api/v1", "");
            if (!externalText.includes(endpointTail) && !externalText.includes(route)) {
              problems.push(`${route}: file evidence در ${exception.fileEvidence} مسیر را نشان نمی‌دهد`);
            }
          }
        }
        continue;
      }

      expect(exception.evidence.length, `${route}: evidence خالی است`).toBeGreaterThan(0);
      if (!evidenceMatches(route, exception.evidence, calls)) {
        problems.push(`${route}: evidence «${exception.evidence}» به API call واقعیِ همان route نمی‌رسد`);
      }
    }

    expect(problems, problems.join("\n")).toEqual([]);
  });

  it("does not leave a route as external/TODO when a real Studio/Client consumer exists", () => {
    const calls = repositoryApiCalls();
    const noCallExceptions = Object.entries(ROUTE_EXCEPTIONS)
      .filter(([, exception]) => exception.evidence === null)
      .map(([route]) => route);
    for (const route of noCallExceptions) {
      const usedByClient = calls.some((call) => routeMatchesPath(route, call.path));
      expect(usedByClient, `${route}: real API call exists — replace TODO/external with concrete call evidence`).toBe(false);
    }
  });
});
