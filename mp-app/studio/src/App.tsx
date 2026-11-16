import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ToastViewport } from "./components/Feedback";
import { UpdateBanner } from "./components/UpdateBanner";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { CheckIn } from "./pages/CheckIn";
import { Finance } from "./pages/Finance";
import { Analytics } from "./pages/Analytics";
import { Dashboard } from "./pages/Dashboard";
import { Members } from "./pages/Members";
import { Assessment } from "./pages/Assessment";
import { Chat } from "./pages/Chat";
import { Nutrition } from "./pages/Nutrition";
import { Programs } from "./pages/Programs";
import { Settings } from "./pages/Settings";
import { Shop } from "./pages/Shop";
import { useAppStore } from "./stores/appStore";

const pages = {
  dashboard: Dashboard,
  members: Members,
  programs: Programs,
  nutrition: Nutrition,
  assessment: Assessment,
  chat: Chat,
  checkin: CheckIn,
  finance: Finance,
  analytics: Analytics,
  settings: Settings,
  shop: Shop,
} as const;

/** لایهٔ اصلی — انتقال صفحات با انیمیشن نرم (AnimatePresence). */
export default function App() {
  const page = useAppStore((s) => s.page);
  const Page = pages[page];
  const reduced = useReducedMotion(); // احترام به prefers-reduced-motion (M07)

  return (
    <div className="flex min-h-screen gap-6 p-6">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <TopBar />
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={reduced ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduced ? undefined : { opacity: 0, y: -10 }}
            transition={{ duration: reduced ? 0 : 0.3, ease: "easeOut" }}
          >
            <Page />
          </motion.div>
        </AnimatePresence>
        <UpdateBanner current={__APP_VERSION__} />
        <ToastViewport />
        <footer className="mt-10 pb-2 text-center text-xs text-ink-dim">
          Muscle Paradise — سیستم‌عامل باشگاه · ساخته‌شده با عشق به جزئیات 💚
        </footer>
      </main>
    </div>
  );
}
