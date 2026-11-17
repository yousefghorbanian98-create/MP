import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiCard } from "../src/components/KpiCard";
import { Sidebar } from "../src/components/Sidebar";

describe("UI components", () => {
  it("renders KpiCard with a real value", () => {
    render(<KpiCard label="درآمد" value={100} unit="ریال" hint="پرداخت‌های paid" index={0} />);
    expect(screen.getByText("درآمد")).toBeTruthy();
    expect(screen.getByText("پرداخت‌های paid")).toBeTruthy();
  });

  it("shows unknown instead of zero when value is null (E05)", () => {
    render(<KpiCard label="ضریب پرشدن" value={null} index={0} />);
    expect(screen.getByText("نامعلوم")).toBeTruthy();
  });

  it("does not render a fabricated delta when there is no history", () => {
    render(<KpiCard label="اعضا" value={5} index={0} />);
    expect(screen.queryByText(/نسبت به هفتهٔ قبل/)).toBeNull();
  });

  it("renders Sidebar navigation", () => {
    render(<Sidebar />);
    expect(screen.getByText("داشبورد")).toBeTruthy();
    expect(screen.getByText("اعضا")).toBeTruthy();
    expect(screen.getByText("Muscle Paradise")).toBeTruthy();
  });
});
