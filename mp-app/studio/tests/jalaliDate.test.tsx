import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import { JalaliDateField, isoFromLocal, toDateObject } from "../src/components/ui/JalaliDateField";

/**
 * Q11 — تقویم جلالی واقعاً جلالی است، نه یک input تاریخ میلادی با ظاهر فارسی.
 *
 * سه چیز سنجیده می‌شود:
 *   ۱. تبدیل میلادی→جلالی درست است (۱۴۰۵/۰۸/۲۸ برای ۲۰۲۶-۱۱-۱۹).
 *   ۲. رفت‌وبرگشت مقدار بدون جابه‌جایی روز است (تلهٔ کلاسیک تایم‌زون).
 *   ۳. فیلد در UI همان تاریخ جلالی را نشان می‌دهد و برچسب دسترس‌پذیر دارد.
 */
describe("Q11 — فیلد تاریخ جلالی", () => {
  it("۲۰۲۶-۱۱-۱۹ را ۱۴۰۵/۰۸/۲۸ نشان می‌دهد", () => {
    const object = toDateObject("2026-11-19");
    expect(object).toBeTruthy();
    expect(object!.format("YYYY/MM/DD")).toBe("۱۴۰۵/۰۸/۲۸");
    expect(object!.calendar.name).toBe(persian.name);
    expect(object!.locale.name).toBe(persian_fa.name);
  });

  it("رفت‌وبرگشت ISO بدون جابه‌جایی روز", () => {
    for (const iso of ["2026-01-01", "2026-03-20", "2026-03-21", "2026-12-31"]) {
      const roundTrip = isoFromLocal(toDateObject(iso)!.toDate());
      expect(roundTrip).toBe(iso);
    }
  });

  it("رشتهٔ نامعتبر باعث کرش نمی‌شود", () => {
    expect(toDateObject("")).toBeUndefined();
    expect(toDateObject("1405/08/28")).toBeUndefined();
  });

  it("فیلد با برچسب و مقدار جلالی رندر می‌شود", () => {
    render(<JalaliDateField label="تاریخ" value="2026-11-19" onChange={() => undefined} />);
    const input = screen.getByLabelText("تاریخ") as HTMLInputElement;
    expect(input.value).toBe("۱۴۰۵/۰۸/۲۸");
  });
});
