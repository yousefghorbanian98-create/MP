import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { VolumePanel } from "../src/components/VolumePanel";

/**
 * G2 — پنل حجم باید از پاسخ واقعی API چیزی نشان دهد که به کاربر دروغ نگوید:
 *   • اگر بازخوردی ثبت نشده، «منبع: برنامه» بنویسد، نه «گزارش عضو»
 *   • اگر عضوی زیر MV است، همان را بگوید و پیشنهاد افزایش بدهد
 *   • هر عدد باید هم‌شکل با نشانگرهای همان گروه باشد
 */

const realPayload = {
  member_id: 1,
  program_id: 5,
  week_number: 4,
  level: "intermediate",
  reason: "5 گروه عضلانی از هفتهٔ 4 برنامهٔ #5 بررسی شد — ست سخت = RIR ≤ ۳",
  rule_version: "volume-report-1.0",
  muscles: [
    {
      muscle: "quads",
      level: "intermediate",
      planned_sets: 8,
      effective_sets: 1,
      source_of_number: "reported_hard_sets",
      data_state: "reported",
      hard_sets: 1,
      soft_sets: 0,
      unknown_rir_sets: 0,
      landmarks: {
        muscle: "quads",
        level: "intermediate",
        mv: 6,
        mev: 8,
        mav_min: 9,
        mav_max: 17,
        mrv: 20,
        hard_set_max_rir: 3,
        source: "Israetel/RP volume landmarks",
        rule_version: "volume-landmarks-1.0",
      },
      status: "below_mv",
      suggestion: {
        delta_sets: 0,
        reason: "درد عضلانی 8/۱۰ — بازیابی مقدم بر پیشرفت است",
        rule_version: "volume-landmarks-1.0",
      },
      rule_version: "volume-landmarks-1.0",
    },
    {
      muscle: "chest",
      level: "intermediate",
      planned_sets: 9,
      effective_sets: 9,
      source_of_number: "planned",
      data_state: "no_feedback",
      hard_sets: 0,
      soft_sets: 0,
      unknown_rir_sets: 0,
      landmarks: {
        muscle: "chest",
        level: "intermediate",
        mv: 4,
        mev: 8,
        mav_min: 8,
        mav_max: 19,
        mrv: 22,
        hard_set_max_rir: 3,
        source: "Israetel/RP volume landmarks",
        rule_version: "volume-landmarks-1.0",
      },
      status: "mav",
      suggestion: {
        delta_sets: 1,
        reason: "در MAV — افزایش تدریجی",
        rule_version: "volume-landmarks-1.0",
      },
      rule_version: "volume-landmarks-1.0",
    },
  ],
};

function mockFetch(payload: unknown, ok = true) {
  return vi.fn(async () =>
    new Response(JSON.stringify(payload), {
      status: ok ? 200 : 500,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("VolumePanel (G2)", () => {
  it("labels the source of the number honestly", async () => {
    vi.stubGlobal("fetch", mockFetch(realPayload));
    render(<VolumePanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("quads")).toBeTruthy());

    expect(screen.getByText(/منبع: گزارش عضو/)).toBeTruthy();
    expect(screen.getByText(/منبع: برنامه/)).toBeTruthy();
  });

  it("shows the real landmark numbers from the payload", async () => {
    vi.stubGlobal("fetch", mockFetch(realPayload));
    render(<VolumePanel memberId={1} />);

    await waitFor(() => expect(screen.getByText(/MV 6 · MEV 8/)).toBeTruthy());
    expect(screen.getByText(/MRV 20/)).toBeTruthy();
  });

  it("renders the low-volume warning and the soreness override", async () => {
    vi.stubGlobal("fetch", mockFetch(realPayload));
    render(<VolumePanel memberId={1} />);

    await waitFor(() => expect(screen.getByText("زیر MV")).toBeTruthy());
    expect(screen.getByText(/بازیابی مقدم بر پیشرفت است/)).toBeTruthy();
  });

  it("does not invent rows when the member has no program", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({
        member_id: 9,
        program_id: null,
        level: "intermediate",
        muscles: [],
        reason: "برای این عضو هیچ برنامه‌ای ثبت نشده — گزارش حجم ساخته نمی‌شود",
        rule_version: "volume-report-1.0",
      }),
    );
    render(<VolumePanel memberId={9} />);

    await waitFor(() => expect(screen.getByText(/هیچ برنامه‌ای ثبت نشده/)).toBeTruthy());
    expect(screen.queryByText("quads")).toBeNull();
  });

  it("surfaces API errors instead of showing an empty success", async () => {
    vi.stubGlobal("fetch", mockFetch({ detail: "خطای سرور" }, false));
    render(<VolumePanel memberId={1} />);

    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  });
});
