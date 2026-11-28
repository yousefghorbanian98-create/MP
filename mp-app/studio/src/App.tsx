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
import { MemberAccount } from "./pages/MemberAccount";
import { MemberSecurity } from "./components/MemberSecurity";
import { MemberCheckin } from "./components/MemberCheckin";
import { MemberClasses } from "./components/MemberClasses";
import { MemberJp7Trend } from "./components/MemberJp7Trend";
import { MemberNutrition } from "./components/MemberNutrition";
import { MemberShop } from "./components/MemberShop";
import { MemberPayments } from "./components/MemberPayments";
import { MemberWallet } from "./components/MemberWallet";
import { MemberTodayProgram } from "./components/MemberTodayProgram";
import { canSeePage, parseRole } from "./lib/roleNav";
import {
  canonicalRouteHref,
  homePathForRole,
  isStaffRole,
  loginPath,
  navigateTo,
  type MemberPage,
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
    return <MemberShell page={route.page} onSignOut={() => void signOut()} />;
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

const memberNavigation: { page: MemberPage; href: string; label: string }[] = [
  { page: "home", href: "/member", label: "خانه" },
  { page: "today", href: "/member/today", label: "امروز" },
  { page: "progress", href: "/member/progress", label: "ارزیابی و روند" },
  { page: "nutrition", href: "/member/nutrition", label: "تغذیه" },
  { page: "classes", href: "/member/classes", label: "کلاس و رزرو" },
  { page: "checkin", href: "/member/checkin", label: "حضور" },
  { page: "payments", href: "/member/payments", label: "پرداخت و فیش" },
  { page: "wallet", href: "/member/wallet", label: "کیف پول" },
  { page: "shop", href: "/member/shop", label: "فروشگاه" },
];

/** Member account uses its own authenticated API vertical slice; today stays an honest placeholder. */
function MemberShell({ page, onSignOut }: { page: MemberPage; onSignOut: () => void }) {
  const titles: Record<MemberPage, string> = {
    home: "خانهٔ عضو",
    today: "امروز",
    progress: "ارزیابی و روند",
    nutrition: "تغذیه",
    classes: "کلاس و رزرو",
    checkin: "حضور (QR)",
    payments: "پرداخت و فیش",
    wallet: "کیف پول",
    shop: "فروشگاه",
  };
  const title = titles[page];

  return (
    <main dir="rtl" className="min-h-screen px-4 py-6 sm:px-6">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
        <header className="glass-card flex flex-wrap items-center justify-between gap-4 p-5">
          <div>
            <p className="text-xs font-semibold text-accent-soft">Muscle Paradise</p>
            <h1 className="mt-1 text-xl font-bold">فضای عضو</h1>
          </div>
          <button type="button" className="btn-ghost rounded-xl px-4 py-2 text-sm" onClick={onSignOut}>
            خروج از حساب
          </button>
        </header>

        <nav aria-label="ناوبری عضو" className="glass-card flex gap-2 p-2">
          {memberNavigation.map((item) => (
            <a
              key={item.page}
              href={item.href}
              aria-current={page === item.page ? "page" : undefined}
              onClick={(event) => {
                if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                event.preventDefault();
                if (page !== item.page) navigateTo(item.href);
              }}
              className={`focus-ring flex-1 rounded-xl px-4 py-3 text-center text-sm font-semibold transition-colors ${
                page === item.page ? "bg-primary/25 text-ink" : "text-ink-dim hover:bg-surface/70 hover:text-ink"
              }`}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <section className="glass-card min-h-48 p-5" aria-labelledby="member-page-title">
          <h2 id="member-page-title" className="text-lg font-bold">{title}</h2>
          {page === "home" ? (
            <div className="mt-4 space-y-6">
              <MemberAccount />
              <MemberSecurity />
            </div>
          ) : page === "progress" ? (
            <div className="mt-4">
              <MemberJp7Trend />
            </div>
          ) : page === "nutrition" ? (
            <div className="mt-4">
              <MemberNutrition />
            </div>
          ) : page === "classes" ? (
            <div className="mt-4">
              <MemberClasses />
            </div>
          ) : page === "checkin" ? (
            <div className="mt-4">
              <MemberCheckin />
            </div>
          ) : page === "payments" ? (
            <div className="mt-4">
              <MemberPayments />
            </div>
          ) : page === "wallet" ? (
            <div className="mt-4">
              <MemberWallet />
            </div>
          ) : page === "shop" ? (
            <div className="mt-4">
              <MemberShop />
            </div>
          ) : (
            <div className="mt-4">
              <MemberTodayProgram />
            </div>
          )}
        </section>
        <ToastViewport />
      </div>
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
