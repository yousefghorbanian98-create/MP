/**
 * M60/R3 — تست قاعدهٔ «چه نقشی چه صفحه‌ای را می‌بیند».
 *
 * چرا این تست لازم است: قاعده دو بار در دو زبان نوشته شده (اینجا و در
 * `mp-app/backend/security/rbac.py`) و اگر از هم دور شوند، دوباره به همان
 * حالت قبل می‌رسیم: منویی که صفحه‌ای باز می‌کند که سرور همهٔ درخواست‌هایش را
 * ۴۰۳ می‌دهد.
 *
 * نکتهٔ مهمی که در این جلسه یاد گرفتیم: نسخهٔ اول `roleFromToken` هر حالت
 * خرابی را «guest» می‌کرد و نتیجه‌اش منوی خالی برای توکن غیر-JWT بود. تست‌های
 * زیر همین را قفل می‌کنند: «توکن خراب ≠ بدون توکن».
 */
import { render, screen } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it } from "vitest";
import { Sidebar } from "../src/components/Sidebar";
import {
  PAGE_RULES,
  ROLE_LABELS,
  canSeePage,
  parseRole,
  roleFromToken,
  visiblePages,
  type Role,
} from "../src/lib/roleNav";

const tokenFor = (role: string) => `h.${btoa(JSON.stringify({ role }))}.s`;

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  localStorage.clear();
});

describe("roleNav — قاعدهٔ دسترسی", () => {
  it("نقش را از payload توکن می‌خواند", () => {
    localStorage.setItem("mp_token", tokenFor("reception"));
    expect(roleFromToken()).toBe("reception");
    expect(parseRole()).toBe("reception");
  });

  it("توکن ناموجود → نقش ناشناخته، نه member", () => {
    expect(roleFromToken()).toBe("guest");
    expect(parseRole()).toBeNull();
  });

  it("توکن خراب/غیر-JWT → ناشناخته (null)، نه یک نقش حدسی", () => {
    localStorage.setItem("mp_token", "tok-123"); // همان چیزی که تست‌های قدیمی می‌گذارند
    expect(parseRole()).toBeNull();
    expect(roleFromToken()).toBe("guest");
  });

  it("نقش ناشناخته در payload → ناشناخته، نه عبور", () => {
    localStorage.setItem("mp_token", tokenFor("hacker"));
    expect(parseRole()).toBeNull();
  });

  it("صفحهٔ ناشناخته برای هیچ نقشی باز نیست (fail-closed)", () => {
    for (const role of Object.keys(ROLE_LABELS) as Role[]) {
      expect(canSeePage("does-not-exist", role)).toBe(false);
    }
  });

  // ── قواعد صریح کارفرما و یافتهٔ M60/R3 ──
  it("مالی برای reception/coach/member بسته است و برای manager/admin باز", () => {
    expect(canSeePage("finance", "reception")).toBe(false);
    expect(canSeePage("finance", "coach")).toBe(false);
    expect(canSeePage("finance", "member")).toBe(false);
    expect(canSeePage("finance", "manager")).toBe(true);
    expect(canSeePage("finance", "admin")).toBe(true);
    expect(canSeePage("finance", "super_admin")).toBe(true);
  });

  it("تنظیمات فقط برای super_admin و admin", () => {
    expect(canSeePage("settings", "manager")).toBe(false);
    expect(canSeePage("settings", "coach")).toBe(false);
    expect(canSeePage("settings", "admin")).toBe(true);
    expect(canSeePage("settings", "super_admin")).toBe(true);
  });

  it("هر صفحهٔ تعریف‌شده دست‌کم یک نقش دارد (قاعدهٔ تهی = صفحهٔ مرده)", () => {
    for (const [page, rule] of Object.entries(PAGE_RULES)) {
      expect(rule.roles.length, page).toBeGreaterThan(0);
      expect(rule.why.length, page).toBeGreaterThan(5);
    }
  });

  it("super_admin همهٔ صفحه‌ها را می‌بیند", () => {
    expect(visiblePages("super_admin")).toEqual(Object.keys(PAGE_RULES));
  });

  it("member به مالی/تنظیمات/اعضا دسترسی ندارد", () => {
    const pages = visiblePages("member");
    expect(pages).not.toContain("finance");
    expect(pages).not.toContain("settings");
    expect(pages).not.toContain("members");
    expect(pages).toContain("programs");
  });
});

describe("Sidebar — منو تابع نقش", () => {
  it("پذیرش منوی مالی را نمی‌بیند (باگ M60/R3)", () => {
    localStorage.setItem("mp_token", tokenFor("reception"));
    render(<Sidebar />);
    expect(screen.queryByText("مالی")).toBeNull();
    expect(screen.queryByText("تنظیمات")).toBeNull();
    expect(screen.getByText("داشبورد")).toBeTruthy();
  });

  it("مالک مالی و تنظیمات را می‌بیند", () => {
    localStorage.setItem("mp_token", tokenFor("super_admin"));
    render(<Sidebar />);
    expect(screen.getByText("مالی")).toBeTruthy();
    expect(screen.getByText("تنظیمات")).toBeTruthy();
  });

  it("بدون توکن منو خالی نمی‌شود، ولی مالی/تنظیمات پنهان است", () => {
    render(<Sidebar />);
    expect(screen.getByText("داشبورد")).toBeTruthy();
    expect(screen.queryByText("مالی")).toBeNull();
    expect(screen.queryByText("تنظیمات")).toBeNull();
  });
});
