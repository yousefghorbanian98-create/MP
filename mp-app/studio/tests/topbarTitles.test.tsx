import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { TopBar } from "../src/components/TopBar";
import { useAppStore, type PageId } from "../src/stores/appStore";

/**
 * باگ QA: عنوان بالای صفحه برای صفحه‌های بدون ورودی در جدول عنوان‌ها
 * به «داشبورد» برمی‌گشت (مثلاً «تغذیه» با عنوان «داشبورد»).
 * این تست تضمین می‌کند هر صفحه عنوان مخصوص خودش را دارد.
 */

vi.mock("../src/auth/AuthContext", () => ({
  useAuth: () => ({ signOut: vi.fn() }),
}));
vi.mock("../src/lib/api", async (orig) => {
  const mod = (await orig()) as Record<string, unknown>;
  return { ...mod, fetchMe: () => new Promise(() => {}) };
});

const expected: Record<PageId, string> = {
  dashboard: "داشبورد",
  members: "مدیریت اعضا",
  programs: "برنامه‌های تمرین",
  nutrition: "تغذیه",
  assessment: "ارزیابی",
  chat: "چت",
  checkin: "حضور و چک‌این",
  finance: "مالی و پرداخت",
  expenses: "هزینه‌ها",
  analytics: "تحلیل‌ها",
  settings: "تنظیمات",
  shop: "فروشگاه",
};

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("TopBar — عنوان هر صفحه", () => {
  for (const [page, title] of Object.entries(expected)) {
    it(`صفحهٔ ${page} عنوان «${title}» را نشان می‌دهد`, () => {
      window.history.replaceState({}, "", `/staff/${page}`);
      useAppStore.setState({ page: page as PageId, search: "" });
      render(<TopBar />);
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(title);
    });
  }
});
