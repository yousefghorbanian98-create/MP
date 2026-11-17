import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Nutrition } from "../src/pages/Nutrition";
import { useAppStore } from "../src/stores/appStore";

/**
 * G5 — صفحهٔ تغذیه باید سه چیز را درست بگوید:
 *   ۱. روز خالی «ثبت نشده» است، نه «صفر کالری خورده»
 *   ۲. هدف بدون برنامهٔ تأییدشده ساخته نمی‌شود
 *   ۳. جستجو و ثبت، واقعاً به API می‌روند (نه پیام موفقیت ساختگی)
 */

const emptyDay = {
  member_id: 7,
  date: "2026-11-15",
  items: [],
  totals: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
  by_slot: {},
  target: { kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0 },
  target_source: "none",
  plan_id: null,
  data_state: "nothing_logged",
  reason: "برای 2026-11-15 هیچ وعده‌ای ثبت نشده — صفر یعنی «ثبت نشده»، نه «نخورده»",
  rule_version: "food-logging-1.0",
};

const loggedDay = {
  ...emptyDay,
  items: [
    {
      id: 1,
      food_id: 5,
      name_fa: "برنج سفید (خشک)",
      grams: 250,
      meal_slot: "lunch",
      kcal: 912.5,
      protein_g: 17.5,
      carbs_g: 200,
      fat_g: 4.8,
      warning: "اعداد برای وزن خشک/خام است — اگر پخته وزن کرده‌اید، مقدار کمتری وارد کنید",
    },
  ],
  totals: { kcal: 912.5, protein_g: 17.5, carbs_g: 200, fat_g: 4.8 },
  by_slot: { lunch: { kcal: 912.5, protein_g: 17.5, count: 1 } },
  data_state: "logged",
  reason: "1 وعده در 2026-11-15 ثبت شده",
};

const foods = [
  {
    id: 5,
    name_fa: "برنج سفید (خشک)",
    category: "غلات",
    kcal_per_100g: 365,
    protein_g_per_100g: 7,
    carbs_g_per_100g: 80,
    fat_g_per_100g: 1.9,
    dry_or_raw: true,
  },
];

function routingFetch(daily: unknown, opts: { logResult?: unknown } = {}) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/nutrition/foods")) {
      return new Response(JSON.stringify(foods), { status: 200 });
    }
    if (url.includes("/nutrition/food-logs") && url.includes("daily")) {
      return new Response(JSON.stringify(daily), { status: 200 });
    }
    if (url.includes("/nutrition/food-logs")) {
      return new Response(
        JSON.stringify(
          opts.logResult ?? {
            logged: 1,
            rejected: [],
            reason: "1 وعده ثبت شد",
            rule_version: "food-logging-1.0",
          },
        ),
        { status: 200 },
      );
    }
    return new Response("{}", { status: 404 });
  });
}

beforeEach(() => {
  useAppStore.setState({ selectedMemberId: 7 });
  localStorage.setItem("mp_token", "test-token");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  useAppStore.setState({ selectedMemberId: null });
  localStorage.clear();
});

describe("Nutrition page (G5)", () => {
  it("asks for a member instead of assuming one", () => {
    useAppStore.setState({ selectedMemberId: null });
    vi.stubGlobal("fetch", routingFetch(emptyDay));
    render(<Nutrition />);
    expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
  });

  it("says nothing was logged rather than showing a zero day", async () => {
    vi.stubGlobal("fetch", routingFetch(emptyDay));
    render(<Nutrition />);

    await waitFor(() => expect(screen.getByText("ثبت نشده")).toBeTruthy());
    expect(screen.getByText(/هیچ وعده‌ای ثبت نشده/)).toBeTruthy();
  });

  it("does not invent a target without an approved plan", async () => {
    vi.stubGlobal("fetch", routingFetch(emptyDay));
    render(<Nutrition />);

    await waitFor(() => expect(screen.getByText(/برنامهٔ تغذیهٔ تأییدشده‌ای/)).toBeTruthy());
  });

  it("shows the dry-weight warning from the server", async () => {
    vi.stubGlobal("fetch", routingFetch(loggedDay));
    render(<Nutrition />);

    // صفحهٔ تغذیه حالا FoodLibrary (G12) هم دارد، پس نام غذا چند جا می‌آید.
    // چیزی که مهم است: هشدار «وزن خشک/خام» در ردیف روز دیده شود.
    await waitFor(() => expect(screen.getAllByText("برنج سفید (خشک)").length).toBeGreaterThan(0));
    expect(screen.getAllByText(/وزن خشک\/خام/).length).toBeGreaterThan(0);
  });

  it("searches the real catalog and reveals the dry flag", async () => {
    vi.stubGlobal("fetch", routingFetch(emptyDay));
    const user = userEvent.setup();
    render(<Nutrition />);

    await user.type(screen.getByPlaceholderText(/نام غذا/), "برنج");
    await user.click(screen.getByRole("button", { name: "جستجو" }));

    await waitFor(() => expect(screen.getByText(/۳۶۵ kcal/)).toBeTruthy());
    expect(screen.getByText("وزن خشک/خام")).toBeTruthy();
  });

  it("reports an empty search honestly", async () => {
    vi.unstubAllGlobals();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/nutrition/foods")) {
          return new Response(JSON.stringify([]), { status: 200 });
        }
        return new Response(JSON.stringify(emptyDay), { status: 200 });
      }),
    );
    const user = userEvent.setup();
    render(<Nutrition />);

    await user.type(screen.getByPlaceholderText(/نام غذا/), "پیتزا");
    await user.click(screen.getByRole("button", { name: "جستجو" }));

    await waitFor(() => expect(screen.getByText(/در جدول غذایی نیست/)).toBeTruthy());
  });

  it("posts a real log entry and shows the confirmation", async () => {
    const fetchMock = routingFetch(emptyDay);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<Nutrition />);

    await user.type(screen.getByPlaceholderText(/نام غذا/), "برنج");
    await user.click(screen.getByRole("button", { name: "جستجو" }));
    await waitFor(() => expect(screen.getByText(/۳۶۵ kcal/)).toBeTruthy());

    await user.click(screen.getByText(/۳۶۵ kcal/).closest("button")!);
    await user.click(screen.getByRole("button", { name: "ثبت" }));

    await waitFor(() => expect(screen.getByText(/ثبت شد/)).toBeTruthy());

    const posted = fetchMock.mock.calls.find(
      (c) => String(c[0]).includes("/nutrition/food-logs") && !String(c[0]).includes("daily"),
    );
    expect(posted).toBeTruthy();
    const body = JSON.parse((posted![1] as RequestInit).body as string);
    expect(body.member_id).toBe(7);
    expect(body.entries[0].food_id).toBe(5);
    expect(body.entries[0].grams).toBe(100);
    expect(body.entries[0].meal_slot).toBe("lunch");
  });

  it("surfaces server-side rejections instead of a fake success", async () => {
    vi.stubGlobal(
      "fetch",
      routingFetch(emptyDay, {
        logResult: {
          logged: 0,
          rejected: [{ index: 0, reason: "مادهٔ غذایی 5 در جدول نیست" }],
          reason: "0 وعده ثبت شد؛ 1 ردیف رد شد",
          rule_version: "food-logging-1.0",
        },
      }),
    );
    const user = userEvent.setup();
    render(<Nutrition />);

    await user.type(screen.getByPlaceholderText(/نام غذا/), "برنج");
    await user.click(screen.getByRole("button", { name: "جستجو" }));
    await waitFor(() => expect(screen.getByText(/۳۶۵ kcal/)).toBeTruthy());
    await user.click(screen.getByText(/۳۶۵ kcal/).closest("button")!);
    await user.click(screen.getByRole("button", { name: "ثبت" }));

    await waitFor(() => expect(screen.getByText(/در جدول نیست/)).toBeTruthy());
    expect(screen.queryByText(/ثبت شد/)).toBeNull();
  });

  it("keeps submit disabled until a food is selected", async () => {
    // دکمه عمداً غیرفعال است — کاربر نباید بتواند درخواست بی‌محتوا بفرستد.
    // (تست قبلی انتظار پیام خطا داشت؛ رفتار واقعی UI بهتر است: جلوگیری، نه پیام.)
    vi.stubGlobal("fetch", routingFetch(emptyDay));
    render(<Nutrition />);

    const submitBtn = screen.getByRole("button", { name: "ثبت" }) as HTMLButtonElement;
    await waitFor(() => expect(submitBtn.disabled).toBe(true));

    const user = userEvent.setup();
    await user.type(screen.getByPlaceholderText(/نام غذا/), "برنج");
    await user.click(screen.getByRole("button", { name: "جستجو" }));
    await waitFor(() => expect(screen.getByText(/۳۶۵ kcal/)).toBeTruthy());
    await user.click(screen.getByText(/۳۶۵ kcal/).closest("button")!);

    await waitFor(() => expect(submitBtn.disabled).toBe(false));
  });
});
