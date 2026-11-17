import { afterEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { Programs } from "../src/pages/Programs";
import { useAppStore } from "../src/stores/appStore";

/**
 * M61 / D7 — پنل حجم باید برای **عضو انتخاب‌شده** درخواست بدهد.
 *
 * باگ اثبات‌شده: `Programs.tsx` پنل را با `items[0].member_id` سوار می‌کرد.
 * یعنی مربی عضو B را از صفحهٔ «اعضا» انتخاب می‌کرد و گزارش حجم عضو A را
 * می‌دید — و `ReadinessPanel` که کنارش نشسته بود، درست از عضو B می‌خواند.
 * دو پنل هم‌سایه با دو عضو مختلف = باگ دادهٔ آموزشی.
 *
 * این تست همان چیزی را می‌سنجد که کاربر آسیب می‌دید: **کدام member_id به
 * API رفت**، نه اینکه «پنل رندر شد».
 */

const programs = {
  items: [
    { id: 11, member_id: 7, member_name: "عضو اول", status: "draft", safety_flags: [], weeks_count: 8, goal: "hypertrophy", engine_version: "workout-1.0" },
    { id: 12, member_id: 9, member_name: "عضو دوم", status: "draft", safety_flags: [], weeks_count: 8, goal: "strength", engine_version: "workout-1.0" },
  ],
};

const emptyVolume = {
  member_id: 0,
  program_id: null,
  week_number: 1,
  level: "intermediate",
  reason: "",
  rule_version: "volume-report-1.0",
  muscles: [],
};

function installFetch() {
  const calls: string[] = [];
  const fn = vi.fn((url: string) => {
    calls.push(url);
    if (url.includes("/volume")) return new Response(JSON.stringify(emptyVolume), { status: 200 });
    if (url.includes("/readiness"))
      return new Response(JSON.stringify({ readiness: null }), { status: 200 });
    if (url.includes("/programs")) return new Response(JSON.stringify(programs), { status: 200 });
    return new Response("[]", { status: 200 });
  });
  vi.stubGlobal("fetch", fn);
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  act(() => useAppStore.setState({ selectedMemberId: null, page: "dashboard" }));
});

describe("Programs — پنل حجم به عضو انتخاب‌شده گره می‌خورد", () => {
  it("با انتخاب عضو #9، درخواست حجم برای 9 می‌رود، نه برای اولین برنامه", async () => {
    localStorage.setItem("mp_token", "t");
    const calls = installFetch();
    // انتخاب عضو در act انجام می‌شود تا به‌روزرسانی‌های async پنل‌ها
    // بیرون از چرخهٔ React نمانند (هشدار «not wrapped in act»).
    act(() => useAppStore.setState({ selectedMemberId: 9 }));

    render(<Programs />);

    await waitFor(() => {
      expect(calls.some((u) => u.includes("/volume"))).toBe(true);
    });

    const volumeUrls = calls.filter((u) => u.includes("/volume"));
    // همهٔ درخواست‌های حجم باید به 9 باشند — هیچ‌کدام به 7 (اولین برنامه)
    expect(volumeUrls.every((u) => u.includes("/programs/member/9/volume"))).toBe(true);
    expect(volumeUrls.some((u) => u.includes("/member/7/volume"))).toBe(false);
  });

  it("بدون انتخاب عضو، هیچ درخواست حجمی فرستاده نمی‌شود و راهنما نشان داده می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    const calls = installFetch();

    render(<Programs />);

    await waitFor(() => {
      expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
    });
    expect(calls.some((u) => u.includes("/volume"))).toBe(false);
  });
});
