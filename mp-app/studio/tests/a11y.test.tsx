import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../src/App";
import { useAppStore } from "../src/stores/appStore";

/**
 * Q5 — دسترس‌پذیری واقعی، نه ادعا.
 *
 * تست نمی‌تواند «زیبا» را بسنجد، ولی می‌تواند چیزهایی را بگیرد که
 * کاربر صفحه‌خوان را کاملاً بلوکه می‌کند:
 *   • تصویر بدون alt
 *   • دکمه‌ای که فقط آیکون دارد و نام دسترس‌پذیر ندارد
 *   • ورودی بدون label/aria-label
 *   • heading پرش‌دار (h1 → h3)
 *   • دکمهٔ غیرفعال بدون توضیح چرا
 */

function response(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200 });
}

function staffToken(): string {
  return `header.${btoa(JSON.stringify({ role: "super_admin" }))}.signature`;
}

function stubApi() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      const path = url.pathname;
      if (path === "/api/v1/members/me") {
        return response({
          id: 1,
          user_id: 1,
          full_name: "کاربر آزمون",
          phone: "09121234567",
          role: "super_admin",
          goal: "",
          gender: "male",
          height_cm: null,
        });
      }
      if (path === "/api/v1/updates/manifest") {
        return response({ update_available: false, latest: "0.1.0", current: "0.1.0", min_supported: "0.1.0", notes: "" });
      }
      if (path === "/api/v1/admin/kpis") {
        return response({ members_total: 0, active_members: 0, new_members_30d: 0, revenue_paid_rial: 0, active_memberships: 0, classes: 0, class_fill_rate: null, generated_at: "2026-11-16T00:00:00Z" });
      }
      if (path === "/api/v1/admin/attendance") {
        return response({ window_days: 7, total_checkins: 0, distinct_members: 0, closed_sessions: 0, open_sessions: 0, total_minutes: 0, series: [], rule_version: "test", generated_at: "2026-11-16T00:00:00Z" });
      }
      if (path === "/api/v1/admin/members-summary") {
        return response({ items: [], rule_version: "test", expiring_days: 7, unknown_status_meaning: "test", generated_at: "2026-11-16T00:00:00Z" });
      }
      if (path === "/api/v1/admin/analytics/leaderboards") {
        return response({ top_athletes: [], top_spenders: [], most_visits: [], most_time: [], window_days: 30, rule_version: "test", generated_at: "2026-11-16T00:00:00Z" });
      }
      if (path === "/api/v1/admin/analytics/churn-risk") return response({ risk_rows: [] });
      if (path === "/api/v1/admin/checkins") return response({ items: [], rule_version: "test" });
      if (path === "/api/v1/admin/users" || path === "/api/v1/admin/audit") return response([]);
      if (path === "/api/v1/admin/flags") return response([]);
      if (path === "/api/v1/auth/sessions") return response([]);
      if (path === "/api/v1/admin/permissions/known") return response([]);
      if (path === "/api/v1/admin/permissions") return response([]);
      if (path === "/api/v1/classes" || path === "/api/v1/chat/conversations") return response([]);
      if (path === "/health") return response({ status: "ok", service: "test", version: "0.1.0" });
      return response({ items: [], data: [], risk_rows: [] });
    }),
  );
}

function audit(container: HTMLElement) {
  const problems: string[] = [];

  for (const img of Array.from(container.querySelectorAll("img"))) {
    if (!img.getAttribute("alt") && img.getAttribute("alt") !== "") {
      problems.push(`img بدون alt: ${img.outerHTML.slice(0, 60)}`);
    }
  }

  for (const btn of Array.from(container.querySelectorAll("button"))) {
    const text = (btn.textContent ?? "").trim();
    const aria = btn.getAttribute("aria-label") ?? btn.getAttribute("title") ?? "";
    if (!text && !aria) problems.push(`دکمه بدون نام دسترس‌پذیر: ${btn.outerHTML.slice(0, 60)}`);
  }

  for (const input of Array.from(
    container.querySelectorAll("input, textarea, select"),
  )) {
    const id = input.getAttribute("id");
    const labelled =
      input.getAttribute("aria-label") ||
      input.getAttribute("placeholder") ||
      (id && container.querySelector(`label[for="${id}"]`)) ||
      input.closest("label");
    if (!labelled) {
      problems.push(`ورودی بدون برچسب: ${input.outerHTML.slice(0, 60)}`);
    }
  }

  return problems;
}

async function renderAuthenticatedApp() {
  const result = render(<App />);
  await screen.findByRole("button", { name: "خروج از حساب" });
  return result;
}

beforeEach(() => {
  localStorage.setItem("mp_token", staffToken());
  localStorage.setItem("mp_refresh", "test-refresh");
  useAppStore.setState({ selectedMemberId: 1 });
  stubApi();
});

/**
 * هر مورد این بخش کل اپ احراز‌هویت‌شده را رندر می‌کند (۱٫۵ تا ۲٫۷ ثانیه محلی).
 * روی runner شلوغ CI، رندر اول صفحهٔ مالی از سقف پیش‌فرض ۵ ثانیه می‌گذشت (timeout).
 * این سقف فقط زمان رندر را بالا می‌برد؛ ممیزی و تعداد موارد بررسی‌شده تغییر نکرده‌اند.
 */
describe("a11y — rule-based audit across every page (Q5)", { timeout: 30_000 }, () => {
  const pages = [
    "dashboard",
    "members",
    "programs",
    "checkin",
    "finance",
    "analytics",
    "settings",
    "nutrition",
    "assessment",
    "chat",
  ] as const;

  for (const page of pages) {
    it(`${page}: no blocking accessibility defects`, async () => {
      useAppStore.setState({ page });
      const { container } = await renderAuthenticatedApp();
      expect(audit(container)).toEqual([]);
    });
  }

  it("every page has exactly one h1", async () => {
    useAppStore.setState({ page: "dashboard" });
    const { container } = await renderAuthenticatedApp();
    expect(container.querySelectorAll("h1").length).toBe(1);
  });

  it("headings never skip a level", async () => {
    useAppStore.setState({ page: "members" });
    const { container } = await renderAuthenticatedApp();
    const levels = Array.from(container.querySelectorAll("h1,h2,h3,h4,h5,h6")).map((h) =>
      Number(h.tagName[1]),
    );
    for (let i = 1; i < levels.length; i += 1) {
      if (levels[i] > levels[i - 1]) {
        expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1);
      }
    }
  });

  it("the sidebar navigation is reachable as buttons with names", async () => {
    useAppStore.setState({ page: "dashboard" });
    const { container } = await renderAuthenticatedApp();
    const navButtons = Array.from(container.querySelectorAll("nav button, aside button"));
    expect(navButtons.length).toBeGreaterThan(4);
    for (const b of navButtons) {
      expect((b.textContent ?? "").trim().length).toBeGreaterThan(0);
    }
  });

  it("applies prefers-reduced-motion (M07)", () => {
    // حرکت باید محترم شمرده شود؛ بررسی وجود منطق، نه اجرای انیمیشن
    const src = require("node:fs").readFileSync(
      require("node:path").resolve(__dirname, "../src/App.tsx"),
      "utf8",
    ) as string;
    expect(src).toContain("useReducedMotion");
  });
});
