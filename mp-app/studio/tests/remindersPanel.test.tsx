import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { RemindersPanel } from "../src/components/RemindersPanel";
import { useAppStore } from "../src/stores/appStore";

/**
 * G11 — پنل یادآوری.
 *
 * محافظت اصلی: «هیچ یادآوری» با «دادهٔ ناکافی» یکی نمایش داده نشود.
 * اگر کاربر فکر کند «همه‌چیز خوب است» در حالی که تاریخ عضویت ثبت نشده،
 * یادآوری تمدید هرگز ساخته نمی‌شود و او غافلگیر می‌شود.
 */

function payload(over: Record<string, unknown> = {}) {
  return {
    member_id: 1,
    generated_at: "2026-11-15T12:00:00Z",
    reminders: [
      {
        key: "renewal",
        priority: "high",
        title: "تمدید عضویت",
        body: "عضویت شما ۲ روز دیگر به پایان می‌رسد.",
        due_in_days: 2,
        rule: "membership_end - now <= 7d",
      },
      {
        key: "inactivity",
        priority: "normal",
        title: "برگشت به تمرین",
        body: "۱۴ روز از آخرین تمرین گذشته است.",
        due_in_days: 0,
        rule: "days_since_last_workout >= 10",
      },
    ],
    skipped: [{ key: "reassessment", reason: "هیچ ارزیابی ثبت نشده" }],
    counts: { due: 2, skipped: 1 },
    thresholds: { renewal_lead_days: 7, inactivity_days: 10, reassess_days: 90 },
    rule_version: "reminders-1.0",
    created_notifications: 2,
    data_sources: { membership: true, workout_feedback: true, assessment: false },
    ...over,
  };
}

function stub(body: unknown, status = 200) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      calls.push(String(input));
      return new Response(JSON.stringify(body), { status });
    }),
  );
  return calls;
}

beforeEach(() => {
  useAppStore.setState({ selectedMemberId: 1 });
  localStorage.setItem("mp_token", "t");
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
  useAppStore.setState({ selectedMemberId: null });
});

describe("RemindersPanel (G11)", () => {
  it("asks for a member instead of guessing", () => {
    useAppStore.setState({ selectedMemberId: null });
    stub({});
    render(<RemindersPanel />);
    expect(screen.getByText(/یک عضو را از صفحهٔ «اعضا» انتخاب کنید/)).toBeTruthy();
  });

  it("shows each reminder with its priority and rule", async () => {
    stub(payload());
    render(<RemindersPanel />);

    await waitFor(() => expect(screen.getByText("تمدید عضویت")).toBeTruthy());
    expect(screen.getByText("فوری")).toBeTruthy();
    expect(screen.getByText("عادی")).toBeTruthy();
    expect(screen.getByText(/membership_end - now <= 7d/)).toBeTruthy();
    expect(screen.getAllByText(/۲ روز دیگر/).length).toBeGreaterThan(0);
  });

  it("distinguishes 'nothing due' from 'not enough data'", async () => {
    stub(payload({ reminders: [], skipped: [{ key: "renewal", reason: "تاریخ پایان عضویت ثبت نشده" }] }));
    render(<RemindersPanel />);

    await waitFor(() => expect(screen.getByText(/یادآوری‌ای لازم نیست/)).toBeTruthy());
    expect(screen.getByText(/دادهٔ ناکافی/)).toBeTruthy();
    expect(screen.getByText(/تاریخ پایان عضویت ثبت نشده/)).toBeTruthy();
  });

  it("shows the thresholds so the user can audit the rules", async () => {
    stub(payload());
    render(<RemindersPanel />);
    await waitFor(() => expect(screen.getByText(/آستانه‌ها/)).toBeTruthy());
    expect(screen.getByText(/بی‌تحرکی ۱۰ روز/)).toBeTruthy();
    expect(screen.getByText(/ارزیابی ۹۰ روز/)).toBeTruthy();
  });

  it("shows an error instead of an empty panel when the API fails", async () => {
    stub({ error: { message: "عضو یافت نشد" } }, 404);
    render(<RemindersPanel />);
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toContain("عضو یافت نشد");
  });

  it("re-fetches when reload is pressed", async () => {
    const calls = stub(payload());
    render(<RemindersPanel />);
    await waitFor(() => expect(screen.getByText("تمدید عضویت")).toBeTruthy());

    const before = calls.length;
    fireEvent.click(screen.getByRole("button", { name: "بازخوانی" }));
    await waitFor(() => expect(calls.length).toBe(before + 1));
  });

  it("does not invent a 'high' label for normal-priority reminders", async () => {
    stub(payload({ reminders: [{ ...payload().reminders[1] }] }));
    render(<RemindersPanel />);
    await waitFor(() => expect(screen.getByText("برگشت به تمرین")).toBeTruthy());
    expect(screen.queryByText("فوری")).toBeNull();
  });
});
