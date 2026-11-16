/**
 * گیت «هیچ مسیر دکوراتیو» — هر مسیر API باید حداقل یک مصرف‌کنندهٔ واقعی
 * در استودیو داشته باشد.
 *
 * چرا: در همین پروژه `Exercise.video_url` همیشه خالی و بی‌مصرف بود،
 * `KpiCard` ساخته و تست شد ولی هیچ‌جا سوار نشد، و `UpdateBanner` کامل
 * بود ولی کاربر هرگز آن را نمی‌دید. این تست همان رده باگ را می‌بندد.
 *
 * استثناها باید **دلیل** داشته باشند، نه سکوت.
 */
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const BACKEND = join(__dirname, "..", "..", "backend");
const CLIENT = join(__dirname, "..", "..", "client", "lib");

/**
 * مسیرهایی که مصرف‌کننده‌شان خارج از کد کلاینت است.
 *
 * M61/D6 — این ساختار عوض شد چون گیت **دروغ** می‌گفت: قبلاً مقدار هر ردیف
 * فقط یک **متن** بود، و تست فقط طول متن را می‌سنجید («دلیل > ۵ کاراکتر»).
 * نتیجه: چهار ردیف مصرف‌کننده‌ای را نام می‌بردند که وجود نداشت:
 *   • `/auth/logout`  → «اپ Dart توکن را پاک می‌کند» — نمی‌کرد
 *   • `/face/privacy-notice` → «نسخهٔ متنی در اپ Dart» — صفر ارجاع
 *   • `/notifications/member/{id}` → «از مسیر /notifications می‌آید» — صفر ارجاع
 *   • `/members/memberships/plans` → «اپ از /members/memberships می‌خواند» — صفر ارجاع
 * اکنون هر ردیف باید `consumer` (چه کسی واقعاً صدایش می‌زند) **و** یک
 * `evidence` قابل‌بازرسی داشته باشد: یا رشته‌ای که در کد کلاینت پیدا می‌شود،
 * یا `null` به معنای «همهٔ مصرف‌کننده‌ها بیرون از این مخزن‌اند» — که آن هم
 * باید `external` را نام ببرد و در تست دیگری سنجیده می‌شود.
 */
interface Exception {
  /** چرا این مسیر امروز مصرف‌کنندهٔ داخلی ندارد. */
  why: string;
  /** رشته‌ای که باید در کد کلاینت پیدا شود؛ `null` = مصرف‌کننده بیرون از مخزن. */
  evidence: string | null;
  /** اگر evidence=null، مصرف‌کنندهٔ بیرونی چه کسی است. */
  external?: string;
}

const NON_STUDIO_CONSUMERS: Record<string, Exception> = {
  // اپ Flutter صفحهٔ تاریخچهٔ ارزیابی ندارد؛ مسیر در API باقی است
  "/api/v1/assessments/member/{member_id}": {
    why: "اپ Flutter از همین مسیر در «پیشرفت» می‌خواند",
    evidence: "/assessments/member/",
  },
  // ابزارهای عملیاتی، نه کاربر نهایی
  "/api/v1/metrics": {
    why: "Prometheus scrape می‌کند — مصرف‌کننده در infra/monitoring است، نه در دو اپ",
    evidence: null,
    external: "Prometheus (mp-app/infra/monitoring/prometheus.yml)",
  },
  "/api/v1/reports/confidential/{member_id}": {
    why: "گزارش محرمانه با توکن کوتاه‌عمر؛ مصرف‌کنندهٔ چاپ/امضا بیرون از دو اپ است",
    evidence: null,
    external: "پذیرش/چاپ — توکن یک‌بارمصرف از مدیر",
  },
  // همگام‌سازی آفلاین: سمت Dart هنوز ساخته نشده (Q4)
  "/api/v1/programs/sync/set-feedback": {
    why: "صف آفلاین Dart ساخته نشده — این ردیف خودش یک TODO است، نه یک انجام",
    evidence: null,
    external: "TODO: Q4 — صف آفلاین Dart",
  },
  "/api/v1/programs/from-engine": {
    why: "مسیر مستقیم مهاجرت/کاوشگر؛ استودیو از /ai/program/generate استفاده می‌کند",
    evidence: null,
    external: "اسکریپت مهاجرت (یک‌بارمصرف)",
  },
  "/api/v1/classes/cancel": {
    why: "اپ Dart لغو رزرو ندارد — این ردیف یک TODO است (N1 در TODO-2026-11-16)",
    evidence: null,
    external: "TODO: N1 — لغو رزرو",
  },
  "/api/v1/payments/wallet/charge": {
    why: "شارژ کیف پول نیاز به درگاه دارد؛ D-024 پروژهٔ پژوهشی",
    evidence: null,
    external: "TODO: G10/درگاه — مسدود تا تصمیم درگاه",
  },
  "/api/v1/payments/invoice/{member_id}": {
    why: "صورتحساب برای چاپ در پذیرش — توکن کوتاه‌عمر",
    evidence: null,
    external: "پذیرش/چاپ",
  },
  "/api/v1/members/memberships/{membership_id}/invoice": {
    why: "صورتحساب اشتراک برای چاپ در پذیرش",
    evidence: null,
    external: "پذیرش/چاپ",
  },
  "/api/v1/members/memberships/from-plan": {
    why: "خرید اشتراک از پلن نیاز به درگاه دارد",
    evidence: null,
    external: "TODO: مسدود تا تصمیم درگاه",
  },
  "/api/v1/members/memberships/plans": {
    // M61/D6: ادعای قبلی («اپ از /members/memberships می‌خواند») کاذب بود —
    // `grep memberships client/lib` صفر ارجاع داشت. اکنون خودِ مسیر در اپ خوانده
    // می‌شود (بنر اشتراک در home_page).
    why: "اپ Dart پلن‌های جنسیت‌محور را برای بنر اشتراک می‌خواند",
    evidence: "/members/$memberId/memberships",
  },
  // چهره
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
  "/api/v1/notifications/member/{member_id}": {
    // M61/D6: ادعای قبلی («از مسیر /notifications می‌آید») کاذب بود —
    // `grep notifications client/lib` صفر ارجاع داشت. صفحهٔ اعلان هنوز نیست.
    why: "صفحهٔ اعلان در اپ ساخته نشده — TODO: S3",
    evidence: null,
    external: "TODO: S3 — صفحهٔ اعلان عضو",
  },
  "/api/v1/population/intake/next": {
    why: "صف پذیرش — اپ gate-check را صدا می‌زند ولی نام مسیر در کد نیست",
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

/**
 * فهرست مسیرها از artifact داخل ریپو خوانده می‌شود، نه از اجرای پایتون:
 * جابِ studio در CI پایتون/venv ندارد و تست آنجا می‌شکست.
 * تولید مجدد: `python scripts/export_routes.py` (در جابِ backend و pre-commit).
 */
const ROUTES_FILE = join(__dirname, "..", "..", "backend", "api", "routes.json");

function backendRoutes(): string[] {
  if (!existsSync(ROUTES_FILE)) {
    throw new Error(
      "api/routes.json نیست — python scripts/export_routes.py را اجرا کنید",
    );
  }
  const parsed = JSON.parse(readFileSync(ROUTES_FILE, "utf8")) as { paths: string[] };
  return parsed.paths;
}

function studioSource(): string {
  const roots = [join(__dirname, "..", "src"), CLIENT];
  let text = "";
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (/\.(ts|tsx|dart)$/.test(entry.name)) text += readFileSync(full, "utf8");
    }
  };
  for (const r of roots) walk(r);
  return text;
}

describe("no decorative API surface", () => {
  it("each backend path is consumed by the studio (or has a documented exception)", () => {
    const routes = backendRoutes();
    expect(routes.length).toBeGreaterThan(50);

    const src = studioSource();
    const missing: string[] = [];

    for (const route of routes) {
      // /api/v1/foo/{id}/bar → همهٔ قطعه‌های ثابت باید در کد کلاینت دیده شوند
      const parts = route.replace("/api/v1", "").split("/").filter((p) => p && !p.startsWith("{"));
      if (parts.length === 0) continue;
      const found =
        parts.every((seg) => src.includes(seg)) || NON_STUDIO_CONSUMERS[route] !== undefined;
      if (!found) missing.push(route);
    }

    expect(missing, `مسیر بدون مصرف‌کننده: ${missing.join(", ")}`).toEqual([]);
  });

  /**
   * M61/D6 — قلب تغییر: استثنا فقط وقتی معتبر است که **قابل بازرسی** باشد.
   *
   * نسخهٔ قبلی این تست فقط `reason.length > 5` را می‌سنجید، پس یک جملهٔ
   * خوش‌ساخت کافی بود تا مسیرِ کاملاً بی‌مصرف سبز شود. چهار ردیف دقیقاً همین
   * سوءاستفاده را کرده بودند و کسی نفهمید.
   */
  it("every exception is verifiable — evidence found in real client code, or an external consumer", () => {
    const src = studioSource();
    const problems: string[] = [];

    for (const [route, exc] of Object.entries(NON_STUDIO_CONSUMERS)) {
      expect(route.startsWith("/api/v1/"), `${route} باید /api/v1 باشد`).toBe(true);
      expect(exc.why.length, `${route}: دلیل خالی است`).toBeGreaterThan(5);

      if (exc.evidence === null) {
        // مصرف‌کننده بیرونی: باید صریح نام برده شود و «TODO» یا یک نام واقعی باشد
        expect(exc.external, `${route}: بدون evidence باید external داشته باشد`).toBeTruthy();
        expect((exc.external ?? "").length).toBeGreaterThan(5);
        continue;
      }

      // ادعای «کد کلاینت این را صدا می‌زند» باید در کد کلاینت **پیدا شود**
      if (!src.includes(exc.evidence)) {
        problems.push(`${route}: evidence «${exc.evidence}» در کد کلاینت پیدا نشد`);
      }
    }

    expect(problems, problems.join("\n")).toEqual([]);
  });

  it("no exception claims a consumer that was already removed", () => {
    // نگهبان رگرسیون برای همان چهار ادعای کاذبِ D6.
    const src = studioSource();
    const withdrawalClaims = Object.entries(NON_STUDIO_CONSUMERS)
      .filter(([, e]) => e.external !== undefined && !e.external.startsWith("TODO"))
      .map(([route]) => route);
    // ردیف‌های «بیرونی واقعی» (چاپ/متریک/مهاجرت) نباید در کد کلاینت ادعای مصرف کنند
    for (const route of withdrawalClaims) {
      const parts = route.replace("/api/v1", "").split("/").filter((p) => p && !p.startsWith("{"));
      // اگر کد کلاینت صریحاً از آن استفاده می‌کند، باید evidence داشت نه external
      const usedByClient = parts.length > 0 && parts.every((seg) => src.includes(seg));
      expect(!usedByClient, `${route}: کد کلاینت استفاده می‌کند — باید evidence بدهد`).toBe(true);
    }
  });
});
