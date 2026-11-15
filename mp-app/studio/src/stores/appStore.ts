import { create } from "zustand";
import { members as mockMembers, type MemberRow } from "../data/mock";

export type PageId = "dashboard" | "members" | "programs" | "checkin" | "finance" | "analytics" | "settings";

interface AppState {
  page: PageId;
  members: MemberRow[];
  selectedMemberId: number | null;
  search: string;
  genderFilter: "all" | "male" | "female";
  setGenderFilter: (g: "all" | "male" | "female") => void;
  setPage: (page: PageId) => void;
  selectMember: (id: number | null) => void;
  setSearch: (q: string) => void;
  filteredMembers: () => MemberRow[];
}

export const useAppStore = create<AppState>((set, get) => ({
  page: "dashboard",
  members: mockMembers,
  selectedMemberId: null,
  search: "",
  genderFilter: "all",
  setGenderFilter: (genderFilter) => set({ genderFilter }),
  setPage: (page) => set({ page, selectedMemberId: null }),
  selectMember: (id) => set({ selectedMemberId: id }),
  setSearch: (search) => set({ search }),
  filteredMembers: () => {
    const { members, search, genderFilter } = get();
    const q = search.trim();
    if (!q) return members;
    return members.filter(
      (m) =>
        (m.name.includes(q) || m.phone.includes(q)) &&
        (genderFilter === "all" || m.gender === genderFilter),
    );
  },
}));
