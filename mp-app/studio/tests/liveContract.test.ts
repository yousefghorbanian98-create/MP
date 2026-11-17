/**
 * اثبات کار مشترک فرانت و بک‌اند — با API واقعی.
 *
 * بقیهٔ تست‌های استودیو `fetch` را mock می‌کنند: آن‌ها ثابت می‌کنند
 * «کامپوننت درست رفتار می‌کند»، نه «کلاینت TypeScript با سرور واقعی
 * حرف می‌زند». یک تغییر نام فیلد در بک‌اند، همهٔ تست‌های mock را سبز
 * می‌گذاشت و محصول را می‌شکست.
 *
 * این فایل همان توابع کلاینت (`src/lib/api.ts`) را روی یک سرور زنده
 * صدا می‌زند. اگر پاسخ واقعی با نوع TS نخواند، تست می‌شکند.
 *
 * اجرا:
 *   MP_API_BASE=http://127.0.0.1:8000 MP_TOKEN=... npm test -- liveContract
 * اگر متغیرها نباشند (مثلاً در CI بدون سرور) تست **skip** می‌شود — با
 * پیام روشن، نه سبزِ دروغین.
 */
import { describe, expect, it } from "vitest";
import {
  browseExercises,
  browseFoods,
  createPayment,
  fetchDailyNutrition,
  fetchKpis,
  fetchMembersSummary,
  fetchMemberVolume,
  fetchReadiness,
  suggestNextWeight,
} from "../src/lib/api";

const BASE = process.env.MP_API_BASE ?? "";
/**
 * شناسهٔ عضو نمونه از خود سرور خوانده می‌شود. در CI فقط یک عضو بذر
 * می‌شود و در محیط توسعه عضو ۴۱ وجود دارد؛ سخت‌کدکردن ۴۱ تست را
 * به دادهٔ یک ماشین گره می‌زد (اولین اجرای CI همین را نشان داد).
 */
let sampleMemberId: number | null = null;
async function memberId(): Promise<number> {
  if (sampleMemberId !== null) return sampleMemberId;
  const restore = installLiveFetch();
  try {
    const summary = await fetchMembersSummary(TOKEN);
    if (summary.items.length === 0) throw new Error("هیچ عضوی روی سرور نیست");
    sampleMemberId = summary.items[0].member_id;
    return sampleMemberId;
  } finally {
    restore();
  }
}
const TOKEN = process.env.MP_TOKEN ?? "";
const live = BASE !== "" && TOKEN !== "";

/**
 * کلاینت با `fetch` نسبی کار می‌کند؛ اینجا همان درخواست را به سرور
 * زنده می‌فرستیم و پاسخ را بی‌تغییر برمی‌گردانیم.
 */
function installLiveFetch() {
  const original = globalThis.fetch;
  globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const absolute = url.startsWith("http") ? url : `${BASE}${url}`;
    return original(absolute, init);
  }) as typeof fetch;
  return () => {
    globalThis.fetch = original;
  };
}

describe.skipIf(!live)("live contract: studio client × real backend", () => {
  it("KPI داشبورد با نوع BackendKpis می‌خواند", async () => {
    const restore = installLiveFetch();
    try {
      const k = await fetchKpis(TOKEN);
      expect(typeof k.members_total).toBe("number");
      expect(typeof k.active_members).toBe("number");
      expect(typeof k.revenue_paid_rial).toBe("number");
      // قرارداد صادقانه: ضریب پرشدن یا عدد است یا null (هرگز ۰ ساختگی)
      expect(k.class_fill_rate === null || typeof k.class_fill_rate === "number").toBe(true);
    } finally {
      restore();
    }
  });

  it("خلاصهٔ اعضا با MemberSummaryRow[] می‌خواند", async () => {
    const restore = installLiveFetch();
    try {
      const summary = await fetchMembersSummary(TOKEN);
      expect(Array.isArray(summary.items)).toBe(true);
      if (summary.items.length > 0) {
        const row = summary.items[0];
        expect(typeof row.member_id).toBe("number");
        expect(typeof row.full_name).toBe("string");
      }
    } finally {
      restore();
    }
  });

  it("کتابخانهٔ حرکات: نوع ExerciseRow و تصویر واقعی سرو می‌شود", async () => {
    const restore = installLiveFetch();
    try {
      const rows = await browseExercises(null, "", TOKEN);
      expect(rows.length).toBeGreaterThan(10);
      const row = rows[0];
      expect(typeof row.exercise_id).toBe("number");
      expect(typeof row.name_fa).toBe("string");
      expect(row.image_url).toMatch(/^\/static\/exercises\/\d+_0\.jpg$/);

      // فایل تصویر هم باید واقعاً ۲۰۰ باشد، نه فقط مسیر در JSON
      const img = await fetch(`${BASE}${row.image_url}`);
      expect(img.status).toBe(200);
      expect(img.headers.get("content-type")).toBe("image/jpeg");
    } finally {
      restore();
    }
  });

  it("پایگاه غذای ایرانی با FoodRow می‌خواند", async () => {
    const restore = installLiveFetch();
    try {
      // سرور CI ممکن است پایگاه غذا بذر نداشته باشد؛ در آن حالت فقط
      // قرارداد (آرایه بودن + عدم خطا) سنجیده می‌شود، نه تعداد.
      const foods = await browseFoods("", 5, TOKEN);
      expect(Array.isArray(foods)).toBe(true);
      if (foods.length === 0) return;
      expect(typeof foods[0].kcal_per_100g).toBe("number");
      expect(typeof foods[0].name_fa).toBe("string");
    } finally {
      restore();
    }
  });

  it("autoreg: کلاینت و موتور روی یک قرارداد توافق دارند", async () => {
    const restore = installLiveFetch();
    try {
      const r = await suggestNextWeight(
        { last_weight: 60, reps_done: 8, target_reps: 10, rpe: null },
        TOKEN,
      );
      expect(typeof r.next_weight).toBe("number");
      expect(["increase", "decrease", "hold"]).toContain(r.action);
      expect(r.rule_version).toBe("autoreg-1.0");
    } finally {
      restore();
    }
  });

  it("آمادگی و حجم برای عضو نمونه پاسخ معتبر می‌دهند", async () => {
    const restore = installLiveFetch();
    try {
      const mid = await memberId();
      const readiness = await fetchReadiness(mid, TOKEN);
      // یا امتیاز هست یا null + دلیل — هرگز عدد ساختگی
      if (readiness.readiness === null) {
        expect((readiness.reason ?? "").length).toBeGreaterThan(3);
      } else {
        expect(typeof readiness.readiness.score).toBe("number");
      }

      const volume = await fetchMemberVolume(mid, "intermediate", TOKEN);
      expect(Array.isArray(volume.muscles)).toBe(true);
    } finally {
      restore();
    }
  });

  it("پرداخت: ساخت تراکنش با PaymentRow می‌خواند", async () => {
    const restore = installLiveFetch();
    try {
      const p = await createPayment(
        {
          member_id: await memberId(),
          amount_rial: 123_000,
          method: "cash",
          description: "live contract",
        },
        TOKEN,
      );
      expect(typeof p.id).toBe("number");
      expect(p.amount_rial).toBe(123_000);
      expect(p.status).toBe("pending");
    } finally {
      restore();
    }
  });

  it("تغذیهٔ روزانه با totals می‌خواند (نه total_kcal)", async () => {
    const restore = installLiveFetch();
    try {
      const daily = await fetchDailyNutrition(await memberId(), "2026-11-15", TOKEN);
      expect(typeof daily.totals.kcal).toBe("number");
      expect(Array.isArray(daily.items)).toBe(true);
    } finally {
      restore();
    }
  });

  it("سرور زنده است و مسیر بدون توکن ۴۰۱ می‌دهد", async () => {
    const res = await fetch(`${BASE}/api/v1/admin/kpis`);
    expect(res.status).toBe(401);
  });
});
