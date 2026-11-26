// P‑2 · درایور قطعیِ UI برای عامل‌ها (بدون وابستگی جدید).
/* global process, document, localStorage, Response, Headers, URL, setTimeout */
// اجرا: npm run drive -- render Expenses clock 2026-03-20T20:30:00Z state
// افعال: render <Page> | clock <ISO|+ms> | type <برچسب> <مقدار> | tap <متن> | state [مسیر] | snapshot <فایل>
// خطاها شناسه‌دار هستند: DRV-001 فعل ناشناخته، DRV-002 صفحهٔ ناشناخته، DRV-003 هدف پیدا نشد،
// DRV-004 ساعت نامعتبر، DRV-005 کنش پیش از render.
// همهٔ ماژول‌های UI با import() پویا بارگذاری می‌شوند تا فراخوانی مستقیم با node فقط CLI را اجرا کند.
import { spawnSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const VERBS = new Set(["render", "clock", "type", "tap", "state", "snapshot"]);
const ARITY = { render: 1, clock: 1, type: 2, tap: 1, snapshot: 1, state: 0 };
const MEMBER_ID = 7;

// فقط صفحه‌ها و پنل‌های پوشش‌داده‌شده؛ بقیه DRV-002 می‌گیرند.
const PAGES = {
  Shop: { load: () => import("../src/pages/Shop.tsx"), props: {} },
  Nutrition: { load: () => import("../src/pages/Nutrition.tsx"), props: {} },
  Expenses: { load: () => import("../src/pages/Expenses.tsx"), props: {} },
  PeriodReportPanel: {
    load: () => import("../src/components/PeriodReportPanel.tsx"),
    props: {},
  },
  AdaptiveNutritionPanel: {
    load: () => import("../src/components/AdaptiveNutritionPanel.tsx"),
    props: { memberId: MEMBER_ID },
  },
};

export function parseArgv(argv) {
  const steps = [];
  let i = 0;
  while (i < argv.length) {
    const verb = argv[i];
    if (!VERBS.has(verb)) {
      throw new Error(`DRV-001 فعل ناشناخته «${verb}». افعال مجاز: ${[...VERBS].join(", ")}`);
    }
    const arity = ARITY[verb];
    const args = [];
    if (verb === "state") {
      // مسیر اختیاری: فقط اگر توکن بعدی فعل نباشد.
      if (i + 1 < argv.length && !VERBS.has(argv[i + 1])) args.push(argv[i + 1]);
      i += 1 + args.length;
    } else {
      for (let k = 1; k <= arity; k++) args.push(argv[i + k]);
      i += 1 + arity;
    }
    steps.push({ verb, args: args.filter((a) => a !== undefined) });
  }
  return steps;
}

function fail(code, step, message, hint) {
  return { code, step, message, hint };
}

function sortKeys(obj) {
  return Object.fromEntries(Object.keys(obj).sort().map((k) => [k, obj[k]]));
}

function getPath(obj, path) {
  return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

// پاسخ‌های کمینه برای رندر؛ هر درخواست ثبت می‌شود و بدنه‌اش هم ثبت می‌شود.
// شکل‌های کمینهٔ پاسخ (از همان فیکسچرهای تست‌های موجود). مسیرهای ناشناخته {} می‌گیرند.
function fixtureFor(url, method) {
  const period = { from_date: "", to_date: "", count: 0, total_rial: 0, by_category: [], items: [] };
  const emptyDay = {
    member_id: MEMBER_ID, date: "", items: [], totals: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
    by_slot: {}, target: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 }, target_source: "none",
    plan_id: null, data_state: "nothing_logged", reason: "", rule_version: "food-logging-1.0",
  };
  const cart = { member_id: MEMBER_ID, items: [], total_rial: 0, count: 0 };
  if (url.includes("/expenses?")) return period;
  if (url.includes("/finance/reports/period")) return { ...period, kind: "month" };
  if (url.includes("/food-logs/member/") && url.includes("/daily")) return emptyDay;
  if (url.includes("/shop/status"))
    return { mode: "in_person", is_open: true, reason: "open", opens_at: "07:00", closes_at: "23:00",
      timezone: "Asia/Tehran", closed_weekdays: [], online_purchase: false, checked_at: "" };
  if (url.includes("/shop/categories")) return [];
  if (url.includes("/shop/products") && method === "GET") return [];
  if (url.includes("/shop/cart")) return cart;
  return {};
}

function installFetch(calls) {
  const original = globalThis.fetch;
  globalThis.fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = (init.method ?? "GET").toUpperCase();
    const headers = new Headers(init.headers ?? {});
    calls.push({
      method,
      url,
      auth: headers.get("Authorization"),
      body: init.body ? JSON.parse(String(init.body)) : null,
    });
    const body = fixtureFor(url, method);
    return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
  };
  return () => {
    globalThis.fetch = original;
  };
}

export async function runSteps(steps) {
  const calls = [];
  const restoreFetch = installFetch(calls);
  const { act, cleanup, fireEvent, render } = await import("@testing-library/react");
  const { React } = { React: (await import("react")).default };
  const { setClock } = await import("../src/lib/clock.ts");
  const { useAppStore } = await import("../src/stores/appStore.ts");
  localStorage.setItem("mp_token", "tok-123");
  useAppStore.setState({ selectedMemberId: MEMBER_ID });
  setClock(null);
  let clockIso = null;
  let rendered = false;
  const extra = {};
  const flush = () => act(async () => new Promise((r) => setTimeout(r, 0)));
  const result = { ok: true, steps: steps.length, state: {}, error: null };
  try {
    for (let s = 0; s < steps.length; s++) {
      const { verb, args } = steps[s];
      if (verb === "render") {
        const name = args[0];
        const page = PAGES[name];
        if (!page) {
          result.error = fail("DRV-002", s, `صفحهٔ «${name}» ناشناخته است.`,
            `یکی از: ${Object.keys(PAGES).join(", ")}`);
          break;
        }
        const mod = await page.load();
        const Cmp = mod[name] ?? mod.default;
        cleanup();
        render(React.createElement(Cmp, page.props));
        rendered = true;
        await flush();
      } else if (verb === "clock") {
        const raw = args[0];
        let next;
        if (/^[+-]\d+$/.test(raw)) {
          if (clockIso === null) {
            result.error = fail("DRV-004", s, "clock نسبی بدون ساعت قبلی.",
              "ابتدا یک clock مطلق (ISO) بدهید.");
            break;
          }
          next = new Date(new Date(clockIso).getTime() + Number(raw)).toISOString();
        } else {
          const t = new Date(raw);
          if (Number.isNaN(t.getTime())) {
            result.error = fail("DRV-004", s, `ساعت نامعتبر «${raw}».`, "نمونه: 2026-03-20T20:30:00Z");
            break;
          }
          next = t.toISOString();
        }
        clockIso = next;
        setClock(next);
      } else if (verb === "type") {
        if (!rendered) {
          result.error = fail("DRV-005", s, "type پیش از render.", "ابتدا render <Page> بدهید.");
          break;
        }
        const [label, value] = args;
        const labels = [...document.querySelectorAll("label")].filter((l) =>
          l.textContent?.includes(label),
        );
        const input = labels.map((l) => l.querySelector("input")).find(Boolean);
        if (!input) {
          result.error = fail("DRV-003", s, `برچسب «${label}» پیدا نشد.`,
            "متن برچسبِ قابل‌دیدن را دقیق‌تر یا کوتاه‌تر بدهید.");
          break;
        }
        fireEvent.change(input, { target: { value } });
        await flush();
      } else if (verb === "tap") {
        if (!rendered) {
          result.error = fail("DRV-005", s, "tap پیش از render.", "ابتدا render <Page> بدهید.");
          break;
        }
        const [text] = args;
        const btn = [...document.querySelectorAll("button")].find((b) =>
          b.textContent?.includes(text),
        );
        if (!btn) {
          result.error = fail("DRV-003", s, `دکمهٔ «${text}» پیدا نشد.`,
            "متن دکمه را از snapshot بخوانید.");
          break;
        }
        fireEvent.click(btn);
        await flush();
      } else if (verb === "state") {
        const path = args[0];
        if (path) extra[path] = getPath({ calls }, path);
      } else if (verb === "snapshot") {
        const text = (document.body.textContent ?? "").replace(/\s+/g, " ").trim();
        writeFileSync(args[0], text + "\n", "utf8");
      }
    }
  } finally {
    cleanup();
    setClock(null);
    restoreFetch();
    localStorage.removeItem("mp_token");
  }
  result.state = sortKeys({ calls, ...extra });
  if (result.error) result.ok = false;
  return result;
}

// CLI: node scripts/agent_drive.mjs <فرمان…>  → JSON نتیجه روی stdout
function cli(argv) {
  const out = "/tmp/mp-drive-result.json";
  rmSync(out, { force: true });
  const r = spawnSync(
    "npx",
    ["vitest", "run", "tests/driver/cli.test.tsx", "--reporter=dot"],
    {
      cwd: fileURLToPath(new URL("..", import.meta.url)),
      env: { ...process.env, MP_DRIVE_ARGV: JSON.stringify(argv), MP_DRIVE_OUT: out },
      encoding: "utf8",
    },
  );
  let body;
  try {
    body = readFileSync(out, "utf8");
  } catch {
    process.stderr.write(r.stdout + r.stderr);
    process.exit(1);
  }
  process.stdout.write(body);
  process.exit(r.status ?? 1);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const argv = process.argv.slice(2);
  try {
    parseArgv(argv);
  } catch (e) {
    process.stderr.write(String(e.message) + "\n");
    process.exit(2);
  }
  cli(argv);
}
