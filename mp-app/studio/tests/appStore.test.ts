import { describe, expect, it, beforeEach } from "vitest";
import { useAppStore } from "../src/stores/appStore";

describe("appStore", () => {
  beforeEach(() => {
    useAppStore.setState({ page: "dashboard", selectedMemberId: null, search: "" });
  });

  it("changes page and resets selection", () => {
    useAppStore.getState().selectMember(3);
    useAppStore.getState().setPage("members");
    expect(useAppStore.getState().page).toBe("members");
    expect(useAppStore.getState().selectedMemberId).toBeNull();
  });

  it("filters members by name", () => {
    useAppStore.getState().setSearch("علی");
    const result = useAppStore.getState().filteredMembers();
    expect(result.length).toBeGreaterThan(0);
    expect(result.every((m) => m.name.includes("علی") || m.phone.includes("علی"))).toBe(true);
  });

  it("returns all members with empty search", () => {
    const all = useAppStore.getState().filteredMembers();
    expect(all.length).toBe(useAppStore.getState().members.length);
  });
});
