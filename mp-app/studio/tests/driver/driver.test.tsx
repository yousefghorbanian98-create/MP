// P‑2 · درایور قطعی UI — red‑first: این تست‌ها پیش از engine نوشته شدند.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parseArgv, runSteps } from "../../scripts/agent_drive.mjs";

const sha = (s: string) => createHash("sha256").update(s).digest("hex");

describe("درایور: تجزیهٔ فرمان (C1)", () => {
  it("افعال را به ترتیب با آرگومان‌هایشان می‌خواند", () => {
    const steps = parseArgv([
      "render", "Nutrition",
      "clock", "2026-03-20T20:30:00Z",
      "type", "وزن", "80",
      "tap", "ثبت وزن",
      "state", "calls.0.url",
      "snapshot", "/tmp/x.txt",
    ]);
    expect(steps.map((s) => s.verb)).toEqual(["render", "clock", "type", "tap", "state", "snapshot"]);
    expect(steps[2].args).toEqual(["وزن", "80"]);
    expect(steps[4].args).toEqual(["calls.0.url"]);
  });

  it("state بدون مسیر پذیرفته می‌شود", () => {
    expect(parseArgv(["render", "Shop", "state"]).at(-1)).toMatchObject({ verb: "state", args: [] });
  });

  it("فعل ناشناخته DRV-001 می‌دهد", () => {
    expect(() => parseArgv(["fly", "Shop"])).toThrow(/DRV-001/);
  });
});

describe("درایور: خطاهای شناسه‌دار (C5)", () => {
  it("صفحهٔ ناشناخته ⇒ DRV-002 با مسیر و پیشنهاد", async () => {
    const r = await runSteps(parseArgv(["render", "NoSuchPage"]));
    expect(r.ok).toBe(false);
    expect(r.error?.code).toBe("DRV-002");
    expect(r.error?.step).toBe(0);
    expect(r.error?.hint.length).toBeGreaterThan(0);
  });

  it("کنش پیش از render ⇒ DRV-005", async () => {
    const r = await runSteps(parseArgv(["tap", "ثبت"]));
    expect(r.error?.code).toBe("DRV-005");
  });

  it("برچسبِ ناموجود برای tap ⇒ DRV-003", async () => {
    const r = await runSteps(parseArgv(["render", "Shop", "tap", "برچسب-که-نیست-۹۹۹"]));
    expect(r.error?.code).toBe("DRV-003");
    expect(r.error?.step).toBe(1);
  });

  it("ساعت نامعتبر ⇒ DRV-004", async () => {
    const r = await runSteps(parseArgv(["clock", "not-a-date"]));
    expect(r.error?.code).toBe("DRV-004");
  });

  it("clock +N بدون ساعت قبلی ⇒ DRV-004 (نه ساعت واقعی)", async () => {
    const r = await runSteps(parseArgv(["clock", "+60000"]));
    expect(r.error?.code).toBe("DRV-004");
  });
});

describe("درایور: قطعیّت و پوشش صفحه‌ها (C2/C4/C8)", () => {
  it("دو اجرای یکسان ⇒ خروجیِ بایت‌به‌بایت یکسان", async () => {
    const argv = ["clock", "2026-03-20T10:00:00Z", "render", "Expenses", "state"];
    const a = JSON.stringify(await runSteps(parseArgv(argv)));
    const b = JSON.stringify(await runSteps(parseArgv(argv)));
    expect(sha(a)).toBe(sha(b));
  });

  it("کلیدهای state مرتب‌اند (C4)", async () => {
    const r = await runSteps(parseArgv(["clock", "2026-03-20T10:00:00Z", "render", "Shop", "state"]));
    const keys = Object.keys(r.state);
    expect(keys).toEqual([...keys].sort());
  });

  it("صفحهٔ فرم‌دار Shop: فهرست محصول از API خوانده می‌شود", async () => {
    const r = await runSteps(parseArgv(["render", "Shop", "state"]));
    expect(r.ok).toBe(true);
    expect(JSON.stringify(r.state)).toContain("/shop/products");
  });

  it("صفحهٔ جدولی Expenses: درخواست دوره با from/to می‌رود", async () => {
    const r = await runSteps(parseArgv(["clock", "2026-03-20T10:00:00Z", "render", "Expenses", "state"]));
    expect(r.ok).toBe(true);
    expect(JSON.stringify(r.state)).toContain("/expenses?from=");
  });

  it("snapshot متن DOM می‌نویسد، نه باینری (C4)", async () => {
    const out = "/tmp/mp-driver-snapshot-test.txt";
    const r = await runSteps(parseArgv(["render", "Expenses", "snapshot", out]));
    expect(r.ok).toBe(true);
    const txt = readFileSync(out, "utf8");
    expect(txt.includes("\u0000")).toBe(false);
    expect(txt).toContain("هزینه");
  });
});
