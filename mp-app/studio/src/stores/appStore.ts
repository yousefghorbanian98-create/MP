import { create } from "zustand";

/**
 * وضعیت UI استودیو — **هیچ دادهٔ دامنه‌ای اینجا نیست** (M45-c1).
 *
 * قبلاً `members` از `data/mock.ts` می‌آمد و هر صفحه‌ای که آن را می‌خواند
 * دادهٔ ساختگی نشان می‌داد. از M45، داده فقط از API می‌آید و این استور
 * محدود به انتخاب صفحه/جست‌وجو/فیلتر است.
 */
export type PageId =
  | "dashboard"
  | "members"
  | "programs"
  | "nutrition"
  | "assessment"
  | "chat"
  | "checkin"
  | "finance"
  | "analytics"
  | "settings";

interface AppState {
  page: PageId;
  selectedMemberId: number | null;
  search: string;
  genderFilter: "all" | "male" | "female";
  setGenderFilter: (g: "all" | "male" | "female") => void;
  setPage: (page: PageId) => void;
  selectMember: (id: number | null) => void;
  setSearch: (q: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  page: "dashboard",
  selectedMemberId: null,
  search: "",
  genderFilter: "all",
  setGenderFilter: (genderFilter) => set({ genderFilter }),
  // M46-c2 — جست‌وجو به صفحه گره می‌خورد؛ عبارتِ صفحهٔ دیگر به این صفحه نشت نمی‌کند
  setPage: (page) => set({ page, selectedMemberId: null, search: "" }),
  selectMember: (id) => set({ selectedMemberId: id }),
  setSearch: (search) => set({ search }),
}));
