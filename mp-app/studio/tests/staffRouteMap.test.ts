/**
 * STAFF-01 (الف) — گیت کامل‌بودن نقشهٔ مسیر کارکنان.
 *
 * چرا این تست: `PAGE_IDS` منبع حقیقت صفحه‌های کارکنان است، ولی تا امروز افزودن
 * یک صفحه به آن **هیچ چیز را قرمز نمی‌کرد**؛ نه مسیر، نه رندر، نه تست. این تست
 * همان ratchet است که برای کنترل‌های دست‌ساز (uiLibrary) کار کرد.
 *
 * برای **هر** صفحه در `PAGE_IDS` سه چیز سنجیده می‌شود:
 *   ۱. مسیر: `parseStudioRoute("/staff/<page>")` همان صفحه را برمی‌گرداند.
 *   ۲. رندر: کلید آن صفحه در نقشهٔ `pages` در `src/App.tsx` وجود دارد و مجموعهٔ
 *      کلیدها **دقیقاً** برابر `PAGE_IDS` است (نه کمتر، نه بیشتر).
 *   ۳. تست اختصاصی: دست‌کم یک فایل در `tests/` همان کامپوننت صفحه را import
 *      می‌کند (`pages/<Name>`). فهرست صفحه‌های بی‌تست در
 *      `tests/staffRouteMapBaseline.json` ثبت شده و فقط می‌تواند **کوچک** شود:
 *      صفحهٔ تازه بدون تست ⇒ ردیف تازه در «بی‌تست» ⇒ قرمز.
 *
 * چرا baseline و نه صفر مطلق: امروز دو صفحه (`members`, `analytics`) تست
 * اختصاصی ندارند؛ پنهان‌کردن این بدهی با یک استثنا همان کاری است که `uiLibrary`
 * اجازه نمی‌داد. عدد ثبت می‌شود و فقط کاهش مجاز است.
 *
 * ownership سمت سرور (ستون دوم STAFF-01) در این تست نیست؛ آن با ماتریس SEC-01
 * سنجیده می‌شود و جدا ثبت شده است.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { PAGE_IDS, type PageId } from "../src/stores/appStore";
import { parseStudioRoute, staffPath } from "../src/lib/navigation";

const ROOT = resolve(__dirname, "..");
const APP = readFileSync(join(ROOT, "src", "App.tsx"), "utf8");
const BASELINE = JSON.parse(
  readFileSync(join(ROOT, "tests", "staffRouteMapBaseline.json"), "utf8"),
) as { withoutDedicatedTest: PageId[] };

/** نقشهٔ `pages` در App.tsx: کلید ⇒ نام کامپوننت. */
function pageMap(): Map<string, string> {
  // نوعِ نقشه خودش `=>` دارد، پس `[^=]*` کار نمی‌کرد؛ تا اولین `= {` جلو می‌رویم.
  const block = APP.match(/const pages: Record<PageId,[\s\S]*?>\s*=\s*\{([\s\S]*?)\n\};/);
  if (!block) throw new Error("نقشهٔ pages در src/App.tsx پیدا نشد — تست باید بازبینی شود");
  const map = new Map<string, string>();
  for (const line of block[1].split("\n")) {
    const hit = line.match(/^\s*([a-z][a-z0-9]*):\s*([A-Z][A-Za-z0-9]*)\s*,?\s*$/);
    if (hit) map.set(hit[1], hit[2]);
  }
  return map;
}

function testFiles(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) testFiles(full, out);
    else if (/\.test\.tsx?$/.test(entry)) out.push(full);
  }
  return out;
}

const TEST_SOURCES = testFiles(join(ROOT, "tests")).map((file) => ({
  name: file.slice(ROOT.length + 1),
  text: readFileSync(file, "utf8"),
}));

/** آیا فایلی در tests وجود دارد که همان کامپوننت صفحه را import کند؟ */
function hasDedicatedTest(component: string): boolean {
  const needle = new RegExp(`pages/${component}["']`);
  return TEST_SOURCES.some((file) => needle.test(file.text));
}

describe("STAFF-01 — نقشهٔ مسیر کارکنان", () => {
  it("هر PageId یک مسیر /staff/<page> دارد که به همان صفحه resolve می‌شود", () => {
    const broken: string[] = [];
    for (const page of PAGE_IDS) {
      const path = staffPath(page);
      if (path !== `/staff/${page}`) broken.push(`${page}: staffPath=${path}`);
      const route = parseStudioRoute(path);
      if (route.type !== "staff" || route.page !== page) {
        broken.push(`${page}: resolve=${JSON.stringify(route)}`);
      }
    }
    expect(broken).toEqual([]);
  });

  it("نقشهٔ pages در App.tsx دقیقاً همان PAGE_IDS است (صفحهٔ بی‌رندر ⇒ قرمز)", () => {
    const map = pageMap();
    const missing = PAGE_IDS.filter((page) => !map.has(page));
    const extra = [...map.keys()].filter((key) => !(PAGE_IDS as readonly string[]).includes(key));
    expect({ missing, extra }).toEqual({ missing: [], extra: [] });
    // نام کامپوننت هم باید واقعاً به یک import در App.tsx وصل باشد، نه اسم خالی.
    const unimported = [...map.values()].filter(
      (name) => !new RegExp(`import \\{ ${name} \\} from "\\./pages/`).test(APP),
    );
    expect(unimported).toEqual([]);
  });

  it("هر صفحهٔ کارکنان تست اختصاصی دارد — و فهرست بی‌تست‌ها فقط کوچک می‌شود", () => {
    const map = pageMap();
    const withoutTest = PAGE_IDS.filter((page) => !hasDedicatedTest(map.get(page) ?? ""));
    // ratchet: مجموعه باید **دقیقاً** برابر baseline باشد؛ صفحهٔ تازه بدون تست
    // این آرایه را بزرگ‌تر می‌کند و قرمز می‌شود، و نوشتن تست برای بدهی قدیمی
    // نیازمند کوچک‌کردن baseline در همان commit است.
    expect(withoutTest.sort()).toEqual([...BASELINE.withoutDedicatedTest].sort());
  });

  it("baseline خودش معتبر است: صفحهٔ حذف‌شده از PAGE_IDS در آن نمی‌ماند", () => {
    const stale = BASELINE.withoutDedicatedTest.filter(
      (page) => !(PAGE_IDS as readonly string[]).includes(page),
    );
    expect(stale).toEqual([]);
  });
});
