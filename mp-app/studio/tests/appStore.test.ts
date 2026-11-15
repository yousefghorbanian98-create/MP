import { describe, expect, it, beforeEach } from "vitest";
import { useAppStore } from "../src/stores/appStore";

describe("appStore (M45 — only UI state, no domain data)", () => {
  beforeEach(() => {
    useAppStore.setState({
      page: "dashboard",
      selectedMemberId: null,
      search: "",
      genderFilter: "all",
    });
  });

  it("changes page and resets selection", () => {
    useAppStore.getState().selectMember(3);
    useAppStore.getState().setPage("members");
    expect(useAppStore.getState().page).toBe("members");
    expect(useAppStore.getState().selectedMemberId).toBeNull();
  });

  it("keeps search and gender filter as pure UI state", () => {
    useAppStore.getState().setSearch("علی");
    useAppStore.getState().setGenderFilter("female");
    expect(useAppStore.getState().search).toBe("علی");
    expect(useAppStore.getState().genderFilter).toBe("female");
  });

  it("holds no domain data — members must come from the API", () => {
    const state = useAppStore.getState() as unknown as Record<string, unknown>;
    expect(state.members).toBeUndefined();
    expect(state.filteredMembers).toBeUndefined();
  });
});
