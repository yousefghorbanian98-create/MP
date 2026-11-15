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
 * مسیرهایی که مصرف‌کننده‌شان خارج از کد کلاینت است — هر کدام **باید**
 * دلیل و مصرف‌کنندهٔ واقعی داشته باشد. استثنای بی‌دلیل = کد دکوراتیو.
 */
const NON_STUDIO_CONSUMERS: Record<string, string> = {
  // اپ Flutter فعلاً صفحهٔ تاریخچه ارزیابی را ندارد؛ مسیر در API باقی است
  "/api/v1/assessments/member/{member_id}": "اپ Flutter (در نقشهٔ راه صفحهٔ ارزیابی)",
  // ابزارهای عملیاتی، نه کاربر نهایی
  "/api/v1/metrics": "Prometheus scrape (monitoring/README)",
  "/api/v1/reports/confidential/{member_id}":
    "گزارش محرمانه با توکن کوتاه‌عمر — مصرف‌کنندهٔ بیرونی چاپ/امضا",
  // همگام‌سازی آفلاین: کلاینت Dart در Q4 فقط داربست دارد (بدون Flutter SDK)
  "/api/v1/programs/sync/set-feedback": "صف آفلاین اپ Dart — Q4 سمت Dart باقی است",
  "/api/v1/programs/from-engine":
    "مسیر مستقیم ثبت خروجی موتور برای مهاجرت/کاوشگر؛ استودیو از /ai/program/generate استفاده می‌کند",
  // اپ Dart: رزرو کلاس هست، لغو رزرو در UI نیست (سمت API پوشش دارد)
  "/api/v1/classes/cancel": "اپ Dart — لغو رزرو در نقشهٔ راه؛ API آماده و تست‌شده",
  // پرداخت: D-024 پروژهٔ پژوهشی — درگاه واقعی خارج از دامنه
  "/api/v1/payments/wallet/charge": "شارژ کیف پول — نیاز به درگاه؛ فقط API + تست",
  "/api/v1/payments/invoice/{member_id}": "صورتحساب برای چاپ در پذیرش — API + تست",
  "/api/v1/members/memberships/{membership_id}/invoice": "صورتحساب اشتراک — API + تست",
  "/api/v1/members/memberships/from-plan": "خرید اشتراک از پلن — درگاه لازم است",
  "/api/v1/members/memberships/plans": "پلن‌های جنسیت‌محور — اپ Dart از /members/memberships می‌خواند",
  // چهره: اپ Dart رضایت را از مسیر API نمی‌گیرد؛ بک‌اند ۴۰۳ می‌دهد (امن)
  "/api/v1/face/consent": "رضایت بیومتریک — اپ Dart ندارد؛ بک‌اند بدون آن ۴۰۳ می‌دهد",
  "/api/v1/face/consent/revoke": "پس‌گرفتن رضایت — مسیر فرانت باقی است",
  "/api/v1/face/checkin-qr": "چک‌این با QR — اپ Dart از /face/qr-token سمتِ کیوسک استفاده می‌کند",
  "/api/v1/face/checkins/{checkin_id}/exit": "ثبت خروج — کیوسک ورودی؛ مسیر تست‌شده",
  "/api/v1/face/deep-status": "وضعیت DeepFace — پنل تشخیصی ادمین",
  "/api/v1/face/privacy-notice": "متن اطلاعیه — نسخهٔ متنی در اپ Dart",
  // احراز هویت
  "/api/v1/auth/logout": "خروج — اپ Dart توکن را پاک می‌کند و مسیر را صدا نمی‌زند",
  "/api/v1/auth/logout-all": "ابطال همهٔ نشست‌ها — پنل امنیتی",
  // اعلان و جمعیت
  "/api/v1/notifications/member/{member_id}": "فهرست اعلان عضو — از مسیر /notifications می‌آید",
  "/api/v1/population/intake/next": "صف پذیرش (population) — اپ Dart gate-check را صدا می‌زند",
  "/api/v1/population/paths": "مسیرهای جمعیت — پنل تحلیل",
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

  it("every documented exception actually names a consumer", () => {
    for (const [route, reason] of Object.entries(NON_STUDIO_CONSUMERS)) {
      expect(route.startsWith("/api/v1/")).toBe(true);
      expect(reason.length).toBeGreaterThan(5);
    }
  });
});
