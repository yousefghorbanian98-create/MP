import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FoodLibrary } from "../src/components/FoodLibrary";

/**
 * G12 — پایگاه غذای ایرانی. سه چیز مهم:
 *   • دسته‌ها از خود داده ساخته می‌شوند (فهرست دستی ناهم‌خوان نمی‌شود)
 *   • چربیِ «نامعلوم» نامعلوم می‌ماند، صفر نمایش داده نمی‌شود
 *   • وزن خشک/خام علامت می‌خورد
 */

const foods = [
  {
    id: 1,
    name_fa: "سینه مرغ (پخته)",
    category: "پروتئین حیوانی",
    kcal_per_100g: 165,
    protein_g_per_100g: 31,
    carbs_g_per_100g: 0,
    fat_g_per_100g: 4.6,
    dry_or_raw: false,
  },
  {
    id: 2,
    name_fa: "برنج سفید (خشک)",
    category: "غلات",
    kcal_per_100g: 365,
    protein_g_per_100g: 7,
    carbs_g_per_100g: 80,
    fat_g_per_100g: 1.9,
    dry_or_raw: true,
  },
  {
    id: 3,
    name_fa: "خرما (مضافتی)",
    category: "میوه",
    kcal_per_100g: 277,
    protein_g_per_100g: 2,
    carbs_g_per_100g: 75,
    fat_g_per_100g: 0, // منبع چربی نمی‌داد ⇒ نامعلوم، نه صفر
    dry_or_raw: false,
  },
];

function mockFetch(rows: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(rows), { status: 200 }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("FoodLibrary (G12)", () => {
  it("lists the real catalog with per-100g numbers", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(foods));
    render(<FoodLibrary />);

    await waitFor(() => expect(screen.getByText("سینه مرغ (پخته)")).toBeTruthy());
    expect(screen.getByText(/۳ از ۳ غذا/)).toBeTruthy();
  });

  it("derives categories from the data itself", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(foods));
    render(<FoodLibrary />);

    await waitFor(() => expect(screen.getByRole("button", { name: /پروتئین حیوانی/ })).toBeTruthy());
    // هر سه دسته باید دکمهٔ فیلتر داشته باشند
    expect(screen.getByRole("button", { name: /غلات/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /میوه/ })).toBeTruthy();
  });

  it("filters by category", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(foods));
    const user = userEvent.setup();
    render(<FoodLibrary />);

    await waitFor(() => expect(screen.getByRole("button", { name: /غلات/ })).toBeTruthy());
    await user.click(screen.getByRole("button", { name: /غلات/ }));

    await waitFor(() => expect(screen.getByText(/۱ از ۳ غذا/)).toBeTruthy());
    expect(screen.getByText("برنج سفید (خشک)")).toBeTruthy();
    expect(screen.queryByText("سینه مرغ (پخته)")).toBeNull();
  });

  it("shows unknown fat as unknown, never as zero", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(foods));
    render(<FoodLibrary />);

    await waitFor(() => expect(screen.getByText("خرما (مضافتی)")).toBeTruthy());
    expect(screen.getByText("نامعلوم")).toBeTruthy();
  });

  it("flags dry or raw weights", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(foods));
    render(<FoodLibrary />);

    await waitFor(() => expect(screen.getByText("[خشک/خام]")).toBeTruthy());
    expect(screen.getByText(/۱ با وزن خشک\/خام/)).toBeTruthy();
  });

  it("says an empty search is empty instead of showing a blank table", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch([]));
    const user = userEvent.setup();
    render(<FoodLibrary />);

    await user.type(screen.getByPlaceholderText(/جستجو/), "پیتزا");

    await waitFor(() => expect(screen.getByText(/«پیتزا» در جدول غذایی نیست/)).toBeTruthy());
  });

  it("tells the operator to run the importer when the table is empty", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch([]));
    render(<FoodLibrary />);

    await waitFor(() =>
      expect(screen.getByText(/scripts\/import_food_catalog\.py/)).toBeTruthy(),
    );
  });
});
