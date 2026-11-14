import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { KpiCard } from "../src/components/KpiCard";
import { Sidebar } from "../src/components/Sidebar";

const kpi = {
  id: "t",
  label: "درآمد",
  value: 100,
  unit: "",
  deltaPct: 5,
  spark: [1, 2, 3],
};

describe("UI components", () => {
  it("renders KpiCard with label", () => {
    render(<KpiCard kpi={kpi} index={0} />);
    expect(screen.getByText("درآمد")).toBeTruthy();
    expect(screen.getByText("نسبت به هفتهٔ قبل")).toBeTruthy();
  });

  it("renders Sidebar navigation", () => {
    render(<Sidebar />);
    expect(screen.getByText("داشبورد")).toBeTruthy();
    expect(screen.getByText("اعضا")).toBeTruthy();
    expect(screen.getByText("Muscle Paradise")).toBeTruthy();
  });
});
