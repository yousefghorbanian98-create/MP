import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Q11 — «هیچ کنترل تعاملی از صفر کد نمی‌شود».
 *
 * این تست سه چیز را قفل می‌کند و بدون آن‌ها هر ادعایی دربارهٔ رعایت Q11
 * فقط حرف است:
 *
 *   ۱. کتابخانه‌های انتخاب‌شده واقعاً در dependencyها با نسخهٔ قفل‌شده هستند
 *      و مجوزشان در NOTICE ثبت شده است.
 *   ۲. ریشهٔ اپ واقعاً RTL + locale فارسی antd را می‌گیرد (StyleProvider
 *      layer برای هم‌زیستی با Tailwind، ConfigProvider direction=rtl).
 *   ۳. بودجهٔ کنترل‌های دست‌ساز «ratchet» است: عدد هر فایل فقط می‌تواند
 *      کم شود. فایل تازه با کنترل خام، تست را قرمز می‌کند.
 *
 * چرا ratchet و نه صفر مطلق: صفحهٔ فروشگاه Studio هنوز کنترل خام دارد؛
 * پاک کردن یک‌شبهٔ آن با تست‌های موجود ریسک بالایی دارد. بودجهٔ عددی
 * اجازهٔ بدهی فنی موجود را می‌دهد ولی جلوی رشد آن را می‌گیرد.
 */

const ROOT = resolve(__dirname, "..");
const SRC = join(ROOT, "src");
const BUDGET = join(ROOT, "tests", "uiControlBudget.json");

interface Dependency {
  name: string;
  version: string;
  license: string;
  why: string;
}

/** فهرست بستهٔ مجاز و الزامی Q11 — با نسخهٔ major قفل‌شده. */
const REQUIRED: Dependency[] = [
  { name: "antd", version: "5.", license: "MIT", why: "کامپوننت‌های آماده: Select/Modal/Switch/Table/Upload" },
  { name: "@ant-design/cssinjs", version: "1.", license: "MIT", why: "StyleProvider layer — هم‌زیستی با Tailwind" },
  { name: "@ant-design/icons", version: "5.", license: "MIT", why: "آیکون‌های آماده با aria" },
  { name: "react-multi-date-picker", version: "4.", license: "MIT", why: "تقویم جلالی/RTL با locale فارسی" },
];

function pkg(): {
  dependencies?: Record<string, string>;
} {
  return JSON.parse(readFileSync(join(ROOT, "package.json"), "utf8")) as {
    dependencies?: Record<string, string>;
  };
}

function notice(): string {
  return readFileSync(join(ROOT, "..", "..", "NOTICE-THIRD-PARTY.md"), "utf8");
}

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.tsx?$/.test(entry)) out.push(full);
  }
  return out;
}

/**
 * الگوهای «کنترل دست‌ساز». عمداً باریک‌اند: دکمهٔ خام HTML کنترل تعاملی
 * چندحالته نیست و هدف Q11 نیست؛ هدف toggle/checkbox/select/dialog/datepicker
 * است که رفتار و دسترس‌پذیری‌شان باید از کتابخانه بیاید.
 */
const HANDMADE: { key: string; pattern: RegExp; label: string }[] = [
  { key: "select", pattern: /<select\b/g, label: "select خام" },
  { key: "date", pattern: /type=["']date["']/g, label: "input type=date خام" },
  { key: "checkbox", pattern: /type=["']checkbox["']/g, label: "checkbox خام" },
  { key: "radio", pattern: /type=["']radio["']/g, label: "radio خام" },
  { key: "dialog", pattern: /role=["']dialog["']/g, label: "dialog دست‌ساز" },
];

function countHandmade(): Record<string, Record<string, number>> {
  const result: Record<string, Record<string, number>> = {};
  for (const file of walk(SRC)) {
    const text = readFileSync(file, "utf8");
    const hits: Record<string, number> = {};
    for (const rule of HANDMADE) {
      const matches = text.match(rule.pattern);
      if (matches && matches.length > 0) hits[rule.key] = matches.length;
    }
    if (Object.keys(hits).length > 0) result[relative(ROOT, file).split("\\").join("/")] = hits;
  }
  return result;
}

describe("Q11 — کتابخانهٔ کنترل‌های UI", () => {
  it("dependencyهای الزامی با نسخهٔ major قفل‌شده نصب‌اند", () => {
    const deps = pkg().dependencies ?? {};
    const missing = REQUIRED.filter((dep) => {
      const installed = deps[dep.name];
      return !installed || !installed.includes(dep.version);
    }).map((dep) => `${dep.name}@${dep.version}*`);
    expect(missing).toEqual([]);
  });

  it("هر dependency در NOTICE با مجوز ثبت شده است", () => {
    const rows = notice();
    const undocumented = REQUIRED.filter((dep) => !rows.includes(`| ${dep.name} `)).map(
      (dep) => dep.name,
    );
    expect(undocumented).toEqual([]);
  });

  it("ریشهٔ اپ RTL + locale فارسی antd را ست می‌کند", () => {
    const main = readFileSync(join(SRC, "main.tsx"), "utf8");
    expect(main).toContain("StyleProvider");
    expect(main).toContain("ConfigProvider");
    expect(main).toContain("faIR");
    expect(main).toContain('direction="rtl"');
  });

  it("کنترل دست‌ساز از بودجهٔ مصوب بیشتر نشده است", () => {
    const budget = JSON.parse(readFileSync(BUDGET, "utf8")) as Record<
      string,
      Record<string, number>
    >;
    const actual = countHandmade();
    const overflow: string[] = [];
    for (const [file, hits] of Object.entries(actual)) {
      for (const [key, count] of Object.entries(hits)) {
        const allowed = budget[file]?.[key] ?? 0;
        if (count > allowed) overflow.push(`${file}: ${key} ${count} > بودجهٔ ${allowed}`);
      }
    }
    expect(overflow).toEqual([]);
  });

  it("بودجهٔ کنترل دست‌ساز باد نمی‌کند (بدون ردیف مرده)", () => {
    const budget = JSON.parse(readFileSync(BUDGET, "utf8")) as Record<
      string,
      Record<string, number>
    >;
    const actual = countHandmade();
    const stale: string[] = [];
    for (const [file, hits] of Object.entries(budget)) {
      for (const [key, allowed] of Object.entries(hits)) {
        const count = actual[file]?.[key] ?? 0;
        if (count < allowed) stale.push(`${file}: ${key} بودجهٔ ${allowed} ولی واقعی ${count}`);
      }
    }
    expect(stale).toEqual([]);
  });
});
