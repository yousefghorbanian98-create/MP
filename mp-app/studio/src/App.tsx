import { useEffect, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ToastViewport } from "./components/Feedback";
import { UpdateBanner } from "./components/UpdateBanner";
import { Sidebar } from "./components/Sidebar";
import { TopBar } from "./components/TopBar";
import { CheckIn } from "./pages/CheckIn";
import { Finance } from "./pages/Finance";
import { Expenses } from "./pages/Expenses";
import { Analytics } from "./pages/Analytics";
import { Dashboard } from "./pages/Dashboard";
import { Members } from "./pages/Members";
import { Assessment } from "./pages/Assessment";
import { Chat } from "./pages/Chat";
import { Nutrition } from "./pages/Nutrition";
import { Programs } from "./pages/Programs";
import { Settings } from "./pages/Settings";
import { Shop } from "./pages/Shop";
import { useAppStore, type PageId } from "./stores/appStore";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Login } from "./pages/Login";
import { canSeePage, parseRole } from "./lib/roleNav";
import {
  canonicalRouteHref,
  homePathForRole,
  isStaffRole,
  loginPath,
  navigateTo,
  parseStudioRoute,
  postLoginPath,
  useStudioLocation,
} from "./lib/navigation";
import { useMotionPreset } from "./lib/motion";

const pages: Record<PageId, () => JSX.Element> = {
  dashboard: Dashboard,
  members: Members,
  programs: Programs,
  nutrition: Nutrition,
  assessment: Assessment,
  chat: Chat,
  checkin: CheckIn,
  finance: Finance,
  expenses: Expenses,
  analytics: Analytics,
  settings: Settings,
  shop: Shop,
};

/** نشست پیش از هر route محافظت‌شده بررسی می‌شود؛ URL جای مجوز سمت سرور نیست. */
function AppContent() {
  const { status, signOut } = useAuth();
  const location = useStudioLocation();
  const route = useMemo(() => parseStudioRoute(location), [location]);
  const role = parseRole();
  const motionPreset = useMotionPreset(); // حالت نامعلوم نیز محافظه‌کارانه reduced است

  useEffect(() => {
    if (route.type === "staff" && useAppStore.getState().page !== route.page) {
      // Keep transient UI state aligned when the browser history changes routes.
      useAppStore.getState().setPage(route.page);
    }
  }, [route]);

  useEffect(() => {
    if (route.type === "not-found") return;
    const canonical = canonicalRouteHref(route);
    if (location !== canonical) navigateTo(canonical, true);
  }, [location, route]);

  useEffect(() => {
    if (status !== "unauthenticated") return;
    if (route.type === "home") navigateTo(loginPath("/"), true);
    else if (route.type === "staff" || route.type === "member") {
      navigateTo(loginPath(route.path), true);
    }
  }, [route, status]);

  useEffect(() => {
    if (status !== "authenticated") return;
    if (route.type === "home") {
      const destination = homePathForRole(role);
      if (destination) navigateTo(destination, true);
    } else if (route.type === "login") {
      const destination = postLoginPath(route.returnTo, role);
      if (destination) navigateTo(destination, true);
    }
  }, [role, route, status]);

  if (route.type === "not-found") return <NotFound />;
  if (status === "checking") {
    return <main role="status" className="flex min-h-screen items-center justify-center text-ink-dim">در حال بررسی نشست…</main>;
  }
  if (status === "unauthenticated") {
    if (route.type === "login") return <Login />;
    return <RoutePending />;
  }
  if (route.type === "home" || route.type === "login") return <RoutePending />;

  if (route.type === "member") {
    if (role !== "member") return <AccessDenied />;
    return <MemberRoutePending onSignOut={() => void signOut()} />;
  }

  if (!isStaffRole(role)) return <AccessDenied />;
  const Page = pages[route.page];
  const pageAllowed = canSeePage(route.page, role);

  return (
    <div className="flex min-h-screen gap-6 p-6">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <TopBar />
        <AnimatePresence mode="wait">
          <motion.div
            key={route.page}
            {...(motionPreset.reduced ? motionPreset.fade : motionPreset.rise)}
            exit={
              motionPreset.reduced
                ? { opacity: 0, transition: motionPreset.fade.transition }
                : { opacity: 0, y: -10 }
            }
          >
            {pageAllowed ? (
              <Page />
            ) : (
              <div className="glass-card p-5 text-sm text-ink-dim" role="alert">
                دسترسی به این صفحه برای نقش جاری مجاز نیست.
              </div>
            )}
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

function RoutePending() {
  return <main role="status" className="flex min-h-screen items-center justify-center text-ink-dim">در حال انتقال…</main>;
}

function AccessDenied() {
  return (
    <main dir="rtl" className="flex min-h-screen items-center justify-center p-5">
      <p className="glass-card max-w-lg p-5 text-sm text-ink-dim" role="alert">
        دسترسی به این مسیر برای نقش جاری مجاز نیست.
      </p>
    </main>
  );
}

function NotFound() {
  return (
    <main dir="rtl" className="flex min-h-screen flex-col items-center justify-center gap-4 p-5 text-center">
      <h1 className="text-xl font-bold">صفحه پیدا نشد</h1>
      <p className="text-sm text-ink-dim">این مسیر در استودیو تعریف نشده است.</p>
      <button type="button" className="btn-primary rounded-xl px-4 py-2" onClick={() => navigateTo("/")}>
        بازگشت به شروع
      </button>
    </main>
  );
}

/** Placeholder routes do not load member data until the dedicated shell is implemented. */
function MemberRoutePending({ onSignOut }: { onSignOut: () => void }) {
  return (
    <main dir="rtl" className="flex min-h-screen flex-col items-center justify-center gap-4 p-5 text-center">
      <h1 className="text-xl font-bold">فضای عضو</h1>
      <p className="max-w-lg text-sm text-ink-dim">
        مسیر عضو تعریف شده است؛ پوسته و تجربهٔ کامل عضو در این مرحله هنوز پیاده‌سازی نشده است.
      </p>
      <button type="button" className="btn-ghost rounded-xl px-4 py-2" onClick={onSignOut}>
        خروج از حساب
      </button>
    </main>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
