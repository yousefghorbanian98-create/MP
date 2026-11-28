/**
 * MEM-08 / PWA-37 — تغذیهٔ عضو: برنامه، وعده و ثبت روزانه **از هم تفکیک‌شده**.
 *
 * معیار پذیرش TODO: «plan، meal، food log و محاسبه از هم تفکیک؛ `meals: []`
 * برنامهٔ کامل نیست. محاسبه یا توصیهٔ حساس بدون داده/فرمول/منبع معتبر و review
 * لازم فعال نشود؛ ادعای پزشکی ممنوع.»
 *
 * قرارداد واقعی (با `grep -n` تولید شده، نه از حافظه):
 * - `modules/nutrition/schemas.py:38-51` → `PlanOut{status, daily_kcal, protein_g,
 *   carbs_g, fat_g, engine_version, meals[]}`.
 * - `modules/nutrition/service.py:169-284` → `daily_summary` با `data_state`
 *   (`logged`/`nothing_logged`)، `target_source` (`approved_plan`/`none`)، `totals`،
 *   `target`، `items[]` و `reason` که خودش می‌گوید «صفر یعنی ثبت‌نشده، نه نخورده».
 *
 * قاعده‌ها:
 * - هر عدد واحد دارد (`کیلوکالری`، `گرم`) و یک `منبع:` دیده‌شدنی.
 * - `meals: []` ⇒ «برنامهٔ کامل نیست»، نه یک برنامهٔ خالیِ سالم.
 * - `data_state === "nothing_logged"` ⇒ هیچ عدد مصرفی به‌عنوان «۰ خورده‌شده» نمایش
 *   داده نمی‌شود؛ متن صریح سرور نشان داده می‌شود.
 * - `target_source === "none"` ⇒ هدف صفر ساخته نمی‌شود و **مقایسه** انجام نمی‌شود.
 * - این فایل هیچ محاسبهٔ تغذیه‌ای و هیچ ادعای پزشکی ندارد؛ همهٔ اعداد از سرور است.
 */
import { useEffect, useState } from "react";
import {
  ApiError,
  ForbiddenError,
  fetchDailyFoodLog,
  fetchMe,
  fetchMemberNutritionPlans,
  type DailyFoodLog,
  type NutritionPlan,
} from "../lib/api";

const PLANS_SOURCE = "منبع: GET /api/v1/nutrition/plans/member/{member_id}";
const LOG_SOURCE = "منبع: GET /api/v1/nutrition/food-logs/member/{member_id}/daily";

const KCAL = "کیلوکالری";
const GRAM = "گرم";

const slotLabels: Record<string, string> = {
  breakfast: "صبحانه",
  lunch: "ناهار",
  dinner: "شام",
  snack: "میان‌وعده",
};

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; plans: NutritionPlan[]; log: DailyFoodLog };

function num(value: number, digits = 0): string {
  return value.toLocaleString("fa-IR", { maximumFractionDigits: digits });
}

function failureMessage(error: unknown): string {
  if (error instanceof ForbiddenError) return "دسترسی به تغذیهٔ این عضو مجاز نیست؛ داده‌ای نمایش داده نمی‌شود.";
  if (error instanceof ApiError) return error.message;
  return "تغذیه از سرور دریافت نشد";
}

function PlanCard({ plan }: { plan: NutritionPlan }) {
  const complete = plan.meals.length > 0;
  return (
    <article
      className="rounded-xl border border-primary/10 px-4 py-3"
      data-plan-status={plan.status}
      data-plan-complete={complete ? "yes" : "no"}
    >
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-semibold">
          برنامهٔ تغذیه #{plan.id.toLocaleString("fa-IR")} — وضعیت: {plan.status}
        </h4>
        <span className="text-[11px] text-ink-dim">موتور: {plan.engine_version}</span>
      </header>

      <dl className="mt-2 grid gap-2 text-xs sm:grid-cols-2">
        <div>
          <dt className="text-ink-dim">انرژی روزانه</dt>
          <dd className="font-semibold">
            {num(plan.daily_kcal)} {KCAL}
          </dd>
        </div>
        <div>
          <dt className="text-ink-dim">درشت‌مغذی‌ها</dt>
          <dd className="font-semibold">
            پروتئین {num(plan.protein_g)} {GRAM} · کربوهیدرات {num(plan.carbs_g)} {GRAM} · چربی{" "}
            {num(plan.fat_g)} {GRAM}
          </dd>
        </div>
      </dl>

      {complete ? (
        <ul className="mt-2 space-y-1 text-xs text-ink-dim">
          {plan.meals.map((meal) => (
            <li key={meal.id}>
              {slotLabels[meal.meal_slot] ?? meal.meal_slot}: {meal.name_fa} · {num(meal.kcal)} {KCAL} ·
              پروتئین {num(meal.protein_g, 1)} {GRAM}
            </li>
          ))}
        </ul>
      ) : (
        <p role="status" className="mt-2 text-xs text-amber-200">
          برنامهٔ کامل نیست: سرور برای این برنامه هیچ وعده‌ای برنگرداند (`meals: []`). اعداد بالا هدف
          روزانه‌اند، نه وعده‌های قابل‌اجرا.
        </p>
      )}
      <p className="mt-2 text-[11px] text-ink-dim">{PLANS_SOURCE}</p>
    </article>
  );
}

function DailyLogCard({ log }: { log: DailyFoodLog }) {
  const logged = log.data_state === "logged";
  const hasTarget = log.target_source === "approved_plan";
  return (
    <article
      className="rounded-xl border border-primary/10 px-4 py-3"
      data-log-state={log.data_state}
      data-target-source={log.target_source}
    >
      <h4 className="text-sm font-semibold">
        ثبت غذایی {log.date} — {logged ? "ثبت‌شده" : "بدون ثبت"}
      </h4>
      <p className="mt-1 text-xs text-ink-dim">{log.reason}</p>

      {logged ? (
        <>
          <p className="mt-2 text-xs font-semibold">
            جمع ثبت‌شده: {num(log.totals.kcal, 1)} {KCAL} · پروتئین {num(log.totals.protein_g, 1)} {GRAM} ·
            کربوهیدرات {num(log.totals.carbs_g, 1)} {GRAM} · چربی {num(log.totals.fat_g, 1)} {GRAM}
          </p>
          <ul className="mt-1 space-y-1 text-xs text-ink-dim">
            {log.items.map((item) => (
              <li key={item.id}>
                {slotLabels[item.meal_slot] ?? item.meal_slot}: {item.name_fa} ({num(item.grams)} {GRAM}) ·{" "}
                {num(item.kcal)} {KCAL}
                {item.warning ? ` — ${item.warning}` : ""}
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p role="status" className="mt-2 text-xs text-ink-dim">
          عدد مصرفی نمایش داده نمی‌شود: «۰» اینجا یعنی «ثبت نشده»، نه «نخورده». برای مقایسه، اول ثبت
          لازم است.
        </p>
      )}

      {hasTarget ? (
        <p className="mt-2 text-xs text-ink-dim">
          هدف روزانه از برنامهٔ تأییدشده (#{log.plan_id?.toLocaleString("fa-IR") ?? "نامعلوم"}):{" "}
          {num(log.target.kcal)} {KCAL} · پروتئین {num(log.target.protein_g)} {GRAM}
          {logged ? " — مقایسهٔ مصرف با هدف مجاز است." : ""}
        </p>
      ) : (
        <p role="status" className="mt-2 text-xs text-amber-200">
          هدفی از برنامهٔ تأییدشده نیامده (`target_source=none`)؛ پس هیچ «درصد رسیدن به هدف» یا مقایسه‌ای
          ساخته نمی‌شود.
        </p>
      )}

      <p className="mt-2 text-[11px] text-ink-dim">{LOG_SOURCE}</p>
      <p className="text-[11px] text-ink-dim">نسخهٔ قاعده: {log.rule_version}</p>
    </article>
  );
}

export function MemberNutrition({ memberId: memberIdProp }: { memberId?: number } = {}) {
  const [memberId, setMemberId] = useState<number | null>(memberIdProp ?? null);
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (memberIdProp !== undefined) return;
    const controller = new AbortController();
    fetchMe(undefined, controller.signal)
      .then((profile) => setMemberId(profile.id))
      .catch((error: unknown) => setState({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [memberIdProp]);

  useEffect(() => {
    if (memberId === null) return;
    const controller = new AbortController();
    setState({ kind: "loading" });
    Promise.all([
      fetchMemberNutritionPlans(memberId, undefined, controller.signal),
      fetchDailyFoodLog(memberId, undefined, undefined, controller.signal),
    ])
      .then(([plans, log]) => setState({ kind: "ready", plans, log }))
      .catch((error: unknown) => setState({ kind: "error", message: failureMessage(error) }));
    return () => controller.abort();
  }, [memberId]);

  if (state.kind === "error") {
    return (
      <section aria-labelledby="member-nutrition-title" className="space-y-3">
        <h3 id="member-nutrition-title" className="text-base font-semibold">
          تغذیه
        </h3>
        <p role="alert" className="text-sm text-danger">
          {state.message}
        </p>
      </section>
    );
  }

  if (state.kind === "loading") {
    return (
      <section aria-labelledby="member-nutrition-title" className="space-y-3">
        <h3 id="member-nutrition-title" className="text-base font-semibold">
          تغذیه
        </h3>
        <p role="status" className="text-sm text-ink-dim">
          در حال دریافت برنامهٔ تغذیه از سرور…
        </p>
      </section>
    );
  }

  const approved = state.plans.filter((plan) => plan.status === "approved");
  return (
    <section aria-labelledby="member-nutrition-title" className="space-y-4">
      <div>
        <h3 id="member-nutrition-title" className="text-base font-semibold">
          تغذیه
        </h3>
        <p className="mt-1 text-xs text-ink-dim">
          سه چیز جدا هستند: «برنامه» (هدف)، «وعده‌های برنامه» و «ثبت غذایی روز». هیچ محاسبه‌ای در کلاینت
          انجام نمی‌شود و هیچ ادعای پزشکی روی این صفحه نیست.
        </p>
      </div>

      <div className="space-y-2">
        <h4 className="text-sm font-semibold">برنامه‌های تغذیه ({num(state.plans.length)})</h4>
        {state.plans.length === 0 ? (
          <p role="status" className="text-sm text-ink-dim">
            سرور هیچ برنامهٔ تغذیه‌ای برای شما برنگرداند. این «صفر کالری» نیست؛ یعنی برنامه‌ای ثبت نشده است.
          </p>
        ) : (
          state.plans.map((plan) => <PlanCard key={plan.id} plan={plan} />)
        )}
        {state.plans.length > 0 && approved.length === 0 ? (
          <p role="status" className="text-xs text-amber-200">
            هیچ برنامهٔ تأییدشده‌ای بین این‌ها نیست؛ اهداف روزانه به‌عنوان هدفِ معتبر نمایش داده نمی‌شوند.
          </p>
        ) : null}
      </div>

      <DailyLogCard log={state.log} />
    </section>
  );
}
