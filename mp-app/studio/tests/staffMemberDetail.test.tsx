/**
 * STAFF-02 (PWA-41) — پروندهٔ عضو: detail از سرور، ویرایش با بازخوانی، کهنگی، سقف صفحه.
 *
 * دروازهٔ برداری این برش (سه کلاس خطا که دیگر نباید برگردند):
 *  ۱. detail از ردیف فهرست ساخته نمی‌شود: فرم ویرایش با `GET /members/{id}` پر
 *     می‌شود و ردیف فهرست فقط برای سرصفحه است.
 *  ۲. «ذخیره شد» پیش از بازخوانی گفته نمی‌شود: پس از PATCH یک GET تازه می‌آید و
 *     متن موفقیت فقط بعد از تطبیقِ پاسخ سرور ظاهر می‌شود.
 *  ۳. کهنگی و سقف صفحه از سرور می‌آیند: `generated_at` قدیمی ⇒ نشان stale،
 *     و `limit` در همان درخواست سرور فرستاده می‌شود (فیلتر/برش کلاینتی نیست).
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Members } from "../src/pages/Members";
import { setClock } from "../src/lib/clock";
import { useAppStore } from "../src/stores/appStore";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

interface Call {
  method: string;
  path: string;
  body: string | null;
}

function summaryRow() {
  return {
    member_id: 12,
    user_id: 30,
    full_name: "مینا آزمون",
    phone: "09120003333",
    goal: "قدرت",
    gender: "female",
    membership_id: 4,
    plan_name: "ماهانه",
    status: "active",
    days_left: 9,
    expires_at: "2026-12-07T00:00:00+00:00",
    is_active: true,
  };
}

function stub(opts: { generatedAt: string; patchFails?: boolean; normalizeGoal?: string }) {
  const calls: Call[] = [];
  let patched = false;
  let record = {
    id: 12,
    user_id: 30,
    branch_id: 1,
    goal: "قدرت",
    gender: "female",
    height_cm: 165,
    constraints: "[]",
  };
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = input instanceof Request ? input.url : String(input);
    const url = new URL(raw, window.location.href);
    const method = (init?.method ?? "GET").toUpperCase();
    calls.push({
      method,
      path: `${url.pathname}${url.search}`,
      body: typeof init?.body === "string" ? init.body : null,
    });

    if (url.pathname === "/api/v1/admin/members-summary") {
      return reply(200, {
        items: [summaryRow()],
        rule_version: "members-summary-1.0",
        expiring_days: 7,
        unknown_status_meaning: "بدون اشتراک",
        generated_at: opts.generatedAt,
      });
    }
    if (url.pathname === "/api/v1/members/12" && method === "GET") {
      // سرور می‌تواند مقدار را نرمال کند؛ کلاینت باید همان را نشان دهد.
      const normalize = Boolean(opts.normalizeGoal) && patched;
      return reply(200, normalize ? { ...record, goal: opts.normalizeGoal } : record);
    }
    if (url.pathname === "/api/v1/members/12" && method === "PATCH") {
      if (opts.patchFails) {
        return reply(403, { error: { message: "نقش شما اجازهٔ ویرایش این عضو را ندارد" } });
      }
      record = { ...record, ...JSON.parse(String(init?.body ?? "{}")) };
      patched = true;
      return reply(200, record);
    }
    if (url.pathname === "/api/v1/members/12/memberships") return reply(200, []);
    if (url.pathname.startsWith("/api/v1/assessments")) return reply(200, []);
    throw new Error(`Unexpected request: ${method} ${url.pathname}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

if (typeof window.matchMedia !== "function") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) =>
      ({
        matches: false,
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as unknown as MediaQueryList,
  });
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", `header.${btoa(JSON.stringify({ role: "manager" }))}.signature`);
  setClock("2026-11-28T12:00:00Z");
  // پنل پرونده فقط با یک عضو انتخاب‌شده رندر می‌شود؛ انتخاب از فهرست سرور است.
  useAppStore.setState({ page: "members", selectedMemberId: 12, search: "", genderFilter: "all" });
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  setClock(null);
});

describe("STAFF-02 — پروندهٔ عضو و ویرایش", () => {
  it("فرم ویرایش را با پروندهٔ سرور (GET /members/{id}) پر می‌کند", async () => {
    const calls = stub({ generatedAt: "2026-11-28T11:58:00+00:00" });
    render(<Members />);

    const goal = (await screen.findByTestId("member-goal")) as HTMLInputElement;
    await waitFor(() => expect(goal.value).toBe("قدرت"));
    expect((screen.getByTestId("member-height") as HTMLInputElement).value).toBe("165");
    expect(calls.some((c) => c.method === "GET" && c.path === "/api/v1/members/12")).toBe(true);
  }, 20000);

  it("پس از ذخیره، مقدار را از سرور بازمی‌خواند و فقط بعد از آن موفقیت می‌گوید", async () => {
    const calls = stub({ generatedAt: "2026-11-28T11:58:00+00:00" });
    render(<Members />);

    const goal = (await screen.findByTestId("member-goal")) as HTMLInputElement;
    await waitFor(() => expect(goal.value).toBe("قدرت")); // پرونده از سرور آمده
    fireEvent.change(goal, { target: { value: "استقامت" } });
    fireEvent.click(screen.getByRole("button", { name: /ذخیره و بازخوانی از سرور/ }));

    expect(await screen.findByTestId("member-save-note")).toBeTruthy();
    const patch = calls.find((c) => c.method === "PATCH" && c.path === "/api/v1/members/12");
    expect(patch).toBeTruthy();
    expect(JSON.parse(patch!.body!)).toEqual({ goal: "استقامت", constraints: "[]", height_cm: 165 });
    // بازخوانی پس از PATCH: GET تازه برای همان عضو.
    const getAfterPatch =
      calls.filter((c) => c.method === "GET" && c.path === "/api/v1/members/12").length;
    expect(getAfterPatch).toBeGreaterThanOrEqual(2);
    expect(screen.getByTestId("member-save-note").textContent).toContain("از سرور بازخوانی شد");
  }, 20000);

  it("اگر سرور مقدار دیگری برگرداند، همان را نشان می‌دهد و موفقیت ادعا نمی‌کند", async () => {
    // این تست را از M10 جدا می‌کند: بدون بازخوانی واقعی از سرور، UI مقدار ارسالی
    // خودش را «ذخیره‌شده» اعلام می‌کرد و مغایرت سرور هرگز دیده نمی‌شد.
    stub({ generatedAt: "2026-11-28T11:58:00+00:00", normalizeGoal: "استقامت (نرمال‌شده در سرور)" });
    render(<Members />);

    const goal = (await screen.findByTestId("member-goal")) as HTMLInputElement;
    await waitFor(() => expect(goal.value).toBe("قدرت"));
    fireEvent.change(goal, { target: { value: "استقامت" } });
    fireEvent.click(screen.getByRole("button", { name: /ذخیره و بازخوانی از سرور/ }));

    await waitFor(() =>
      expect(screen.getByTestId("member-save-note").textContent).toContain("سرور مقدار دیگری برگرداند"),
    );
    await waitFor(() =>
      expect((screen.getByTestId("member-goal") as HTMLInputElement).value).toBe(
        "استقامت (نرمال‌شده در سرور)",
      ),
    );
    expect(screen.getByRole("alert").textContent).toContain("نمی‌خواند");
  }, 20000);

  it("خطای PATCH را از پیام سرور نشان می‌دهد و موفقیت جعلی نمی‌سازد", async () => {
    stub({ generatedAt: "2026-11-28T11:58:00+00:00", patchFails: true });
    render(<Members />);

    await screen.findByTestId("member-goal");
    fireEvent.click(screen.getByRole("button", { name: /ذخیره و بازخوانی از سرور/ }));

    expect(await screen.findByText(/اجازهٔ ویرایش این عضو را ندارد/)).toBeTruthy();
    expect(screen.queryByText(/از سرور بازخوانی شد/)).toBeNull();
  }, 20000);

  it("دادهٔ قدیمی فهرست را «تازه نیست» اعلام می‌کند", async () => {
    stub({ generatedAt: "2026-11-28T11:40:00+00:00" });
    render(<Members />);

    const stale = await screen.findByTestId("members-stale");
    expect(stale.textContent).toContain("تازه نیست");
    expect(stale.textContent).toContain("۲۰ دقیقه");
  }, 20000);

  it("سقف صفحه را به سرور می‌فرستد (برش کلاینتی نیست)", async () => {
    const calls = stub({ generatedAt: "2026-11-28T11:58:00+00:00" });
    render(<Members />);

    await screen.findByTestId("member-goal");
    fireEvent.mouseDown(screen.getByTestId("members-limit").querySelector(".ant-select-selector")!);
    const option = await waitFor(() => {
      const found = document.querySelector(".ant-select-item-option[title='۵۰']");
      if (!found) throw new Error("limit option not open");
      return found as HTMLElement;
    });
    fireEvent.click(option);

    await waitFor(() =>
      expect(calls.some((c) => c.path === "/api/v1/admin/members-summary?limit=50")).toBe(true),
    );
  }, 20000);
});
