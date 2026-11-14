import { create } from "zustand";
import { members as mockMembers, type MemberRow } from "../data/mock";

export type PageId = "dashboard" | "members" | "programs" | "checkin" | "settings";

interface AppState {
  page: PageId;
  members: MemberRow[];
  selectedMemberId: number | null;
  search: string;
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
  setPage: (page) => set({ page, selectedMemberId: null }),
  selectMember: (id) => set({ selectedMemberId: id }),
  setSearch: (search) => set({ search }),
  filteredMembers: () => {
    const { members, search } = get();
    const q = search.trim();
    if (!q) return members;
    return members.filter((m) => m.name.includes(q) || m.phone.includes(q));
  },
}));
