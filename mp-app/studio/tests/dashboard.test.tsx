import { afterEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Dashboard } from "../src/pages/Dashboard";
import { useAppStore } from "../src/stores/appStore";

/**
 * M45-c1 / G10 — داشبورد KPI.
 *
 * باگ «کد مرده»: `KpiCard` ساخته و تست شده بود ولی داشبورد کارت‌ها را
 * دستی بازتولید می‌کرد؛ یعنی کامپوننت هیچ‌جا مصرف نمی‌شد و دو نسخه از
 * یک قاعده («نامعلوم، نه صفر») در دو جا نگه‌داری می‌شد. این تست ثابت
 * می‌کند داشبورد همان کامپوننت مشترک را رندر می‌کند.
 */

const kpis = {
  members_total: 40,
  active_members: 12,
  new_members_30d: 3,
  revenue_paid_rial: 1500000,
  classes: 4,
  class_fill_rate: null,
  rule_version: "kpis-1.0",
};

const attendance = {
  total_checkins: 0,
  distinct_members: 0,
  closed_sessions: 0,
  open_sessions: 0,
  series: [],
  rule_version: "attendance-1.0",
};

const members = {
  items: [
    {
      member_id: 7,
      user_id: 17,
      full_name: "آوا رضایی",
      phone: "09120000007",
      goal: "strength",
      gender: "female",
      membership_id: 3,
      plan_name: "ماهانه",
      status: "active",
      days_left: 12,
      expires_at: "2026-12-05",
      is_active: true,
    },
  ],
  rule_version: "members-1.0",
  expiring_days: 7,
  unknown_status_meaning: "no membership",
};

function routeFetch(url: string) {
  if (url.includes("/admin/kpis")) return new Response(JSON.stringify(kpis), { status: 200 });
  if (url.includes("/admin/attendance"))
    return new Response(JSON.stringify(attendance), { status: 200 });
  if (url.includes("/admin/members-summary"))
    return new Response(JSON.stringify(members), { status: 200 });
  if (url.includes("/classes")) return new Response("[]", { status: 200 });
  return new Response("{}", { status: 200 });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  useAppStore.setState({ page: "dashboard", selectedMemberId: null, genderFilter: "all", search: "" });
});

describe("Dashboard KPI cards (M45-c1)", () => {
  it("اعداد واقعی KPI را نشان می‌دهد و «نامعلوم» را برای ظرفیت ثبت‌نشده", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => routeFetch(String(input))),
    );
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("اعضای فعال")).toBeTruthy());
    expect(screen.getByText("۱۲")).toBeTruthy();
    expect(screen.getByText("از ۴۰ عضو ثبت‌شده")).toBeTruthy();
    // ضریب پرشدن داده ندارد ⇒ نامعلوم، نه ۰٪
    expect(screen.getByText("نامعلوم")).toBeTruthy();
    expect(screen.getByText("نامعلوم — ظرفیتی ثبت نشده")).toBeTruthy();
  });

  it("نبود داده را با پیام روشن اعلام می‌کند نه عدد ساختگی", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => routeFetch(String(input))),
    );
    render(<Dashboard />);
    await waitFor(() =>
      expect(screen.getByText(/هیچ چک‌اینی در ۷ روز اخیر ثبت نشده/)).toBeTruthy(),
    );
  });

  it("opens the selected member from the dashboard table", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => routeFetch(String(input))),
    );
    render(<Dashboard />);

    const name = await screen.findByText("آوا رضایی");
    fireEvent.click(name.closest("button")!);

    await waitFor(() => {
      expect(useAppStore.getState().page).toBe("members");
      expect(useAppStore.getState().selectedMemberId).toBe(7);
    });
  });
});
