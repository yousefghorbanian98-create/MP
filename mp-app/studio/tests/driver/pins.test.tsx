// P‑B‑1 (الزامی از داوری P‑A): تاریخ پیش‌فرض چهار پنل با خودِ درایور پین می‌شود.
// مستقل از منطقهٔ دستگاه: ساعت فقط با clock درایور (src/lib/clock.ts) ست می‌شود.
import { describe, expect, it } from "vitest";
import { parseArgv, runSteps } from "../../scripts/agent_drive.mjs";

const urls = (state: Record<string, unknown>) =>
  ((state.calls as { method: string; url: string }[]) ?? []).map((c) => `${c.method} ${c.url}`);

describe("D‑24 پین‌شده با درایور: «امروز» در منطقهٔ فروشگاه", () => {
  it("Nutrition: 20:30Z ⇒ date=2026-03-21، و 20:00Z ⇒ date=2026-03-20", async () => {
    const a = await runSteps(parseArgv(["clock", "2026-03-20T20:30:00Z", "render", "Nutrition", "state"]));
    expect(a.ok).toBe(true);
    expect(urls(a.state).some((u) => u.includes("/daily?date=2026-03-21"))).toBe(true);
    const b = await runSteps(parseArgv(["clock", "2026-03-20T20:00:00Z", "render", "Nutrition", "state"]));
    expect(urls(b.state).some((u) => u.includes("/daily?date=2026-03-20"))).toBe(true);
  });

  it("PeriodReportPanel: 20:30Z ⇒ anchor=2026-03-21", async () => {
    const r = await runSteps(parseArgv(["clock", "2026-03-20T20:30:00Z", "render", "PeriodReportPanel", "state"]));
    expect(r.ok).toBe(true);
    expect(urls(r.state).some((u) => u.includes("anchor=2026-03-21"))).toBe(true);
  });

  it("Expenses: 20:30Z ⇒ to=2026-03-21 و from=2026-02-19 (۳۰ روز قبل)", async () => {
    const r = await runSteps(parseArgv(["clock", "2026-03-20T20:30:00Z", "render", "Expenses", "state"]));
    expect(r.ok).toBe(true);
    const u = urls(r.state).find((x) => x.includes("/expenses?")) ?? "";
    expect(u).toContain("to=2026-03-21");
    expect(u).toContain("from=2026-02-19");
  });

  it("AdaptiveNutritionPanel: ثبت وزن با 20:30Z ⇒ logged_for_date=2026-03-21", async () => {
    const r = await runSteps(
      parseArgv([
        "clock", "2026-03-20T20:30:00Z",
        "render", "AdaptiveNutritionPanel",
        "type", "وزن", "80",
        "tap", "ثبت وزن",
        "state", "calls",
      ]),
    );
    expect(r.ok).toBe(true);
    const post = (r.state.calls as { method: string; url: string; body: unknown }[]).find(
      (c) => c.method === "POST" && c.url.includes("/weight-logs"),
    );
    expect(post).toBeDefined();
    expect(JSON.stringify(post?.body)).toContain("2026-03-21");
  });
});
