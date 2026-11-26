import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiCard } from "../src/components/KpiCard";
import { Sidebar } from "../src/components/Sidebar";
import { Skeleton } from "../src/components/Feedback";

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

  it("renders Sidebar navigation and guards its pulse indicator for reduced motion", () => {
    const { container } = render(<Sidebar />);
    expect(screen.getByText("داشبورد")).toBeTruthy();
    expect(screen.getByText("اعضا")).toBeTruthy();
    expect(screen.getByText("Muscle Paradise")).toBeTruthy();
    const pulse = container.querySelector(".animate-pulse-soft");
    expect(pulse?.className.split(/\s+/)).toContain("motion-reduce:animate-none");
  });

  it("disables the skeleton pulse under prefers-reduced-motion", () => {
    const { container } = render(<Skeleton />);
    const skeleton = container.querySelector('[aria-busy="true"]');
    expect(skeleton?.className.split(/\s+/)).toContain("motion-reduce:animate-none");
  });
});
