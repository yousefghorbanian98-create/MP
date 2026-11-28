import { useSyncExternalStore } from "react";
import { canSeePage, type Role } from "./roleNav";
import { PAGE_IDS, useAppStore, type PageId } from "../stores/appStore";

const ROUTE_ORIGIN = "https://studio.invalid";
const LOCATION_CHANGE_EVENT = "mp:studio-location-change";

export const STAFF_PAGES: readonly PageId[] = PAGE_IDS;

export type MemberPage =
  | "home"
  | "today"
  | "progress"
  | "nutrition"
  | "classes"
  | "checkin"
  | "wallet"
  | "shop";

export type StudioRoute =
  | { type: "home"; path: "/" }
  | { type: "login"; path: "/login"; returnTo: string | null }
  | {
      type: "member";
      path:
        | "/member"
        | "/member/today"
        | "/member/progress"
        | "/member/nutrition"
        | "/member/classes"
        | "/member/checkin"
        | "/member/wallet"
        | "/member/shop";
      page: MemberPage;
    }
  | { type: "staff"; path: string; page: PageId }
  | { type: "not-found"; path: string };

export function isStaffRole(role: Role | null): role is Exclude<Role, "member" | "guest"> {
  return role !== null && role !== "member" && role !== "guest";
}

export function staffPath(page: PageId): string {
  return `/staff/${page}`;
}

function normalizePath(pathname: string): string {
  if (pathname === "/") return "/";
  return pathname.replace(/\/+$/, "") || "/";
}

function routeForPath(pathname: string): StudioRoute {
  const path = normalizePath(pathname);
  if (path === "/") return { type: "home", path: "/" };
  if (path === "/login") return { type: "login", path: "/login", returnTo: null };
  if (path === "/member") return { type: "member", path: "/member", page: "home" };
  if (path === "/member/today") return { type: "member", path: "/member/today", page: "today" };
  if (path === "/member/progress") return { type: "member", path: "/member/progress", page: "progress" };
  if (path === "/member/nutrition")
    return { type: "member", path: "/member/nutrition", page: "nutrition" };
  if (path === "/member/classes") return { type: "member", path: "/member/classes", page: "classes" };
  if (path === "/member/checkin") return { type: "member", path: "/member/checkin", page: "checkin" };
  if (path === "/member/wallet") return { type: "member", path: "/member/wallet", page: "wallet" };
  if (path === "/member/shop") return { type: "member", path: "/member/shop", page: "shop" };
  if (path === "/staff") return { type: "staff", path: staffPath("dashboard"), page: "dashboard" };

  const match = path.match(/^\/staff\/([a-z]+)$/);
  const page = match?.[1];
  if (page && STAFF_PAGES.includes(page as PageId)) {
    return { type: "staff", path: staffPath(page as PageId), page: page as PageId };
  }
  return { type: "not-found", path };
}

/**
 * Only same-origin, known application routes can be used as post-login destinations.
 * Query strings and fragments are intentionally excluded; current page routes do not
 * carry shareable domain state, tokens, or personal data in the URL.
 */
export function normalizeReturnTo(candidate: string | null | undefined): string | null {
  if (
    !candidate ||
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\") ||
    [...candidate].some((character) => {
      const code = character.charCodeAt(0);
      return code < 0x20 || code === 0x7f;
    })
  ) {
    return null;
  }

  let url: URL;
  try {
    url = new URL(candidate, ROUTE_ORIGIN);
  } catch {
    return null;
  }
  if (url.origin !== ROUTE_ORIGIN || url.search || url.hash) return null;

  const route = routeForPath(url.pathname);
  return route.type === "home" || route.type === "member" || route.type === "staff"
    ? route.path
    : null;
}

export function loginPath(returnTo?: string | null): string {
  const safeReturnTo = normalizeReturnTo(returnTo);
  return safeReturnTo
    ? `/login?returnTo=${encodeURIComponent(safeReturnTo)}`
    : "/login";
}

export function parseStudioRoute(location: string): StudioRoute {
  let url: URL;
  try {
    url = new URL(location, ROUTE_ORIGIN);
  } catch {
    return { type: "not-found", path: "/" };
  }
  if (url.origin !== ROUTE_ORIGIN) return { type: "not-found", path: normalizePath(url.pathname) };

  const route = routeForPath(url.pathname);
  if (route.type !== "login") return route;
  return { ...route, returnTo: normalizeReturnTo(url.searchParams.get("returnTo")) };
}

export function canonicalRouteHref(route: StudioRoute): string {
  return route.type === "login" ? loginPath(route.returnTo) : route.path;
}

export function homePathForRole(role: Role | null): string | null {
  if (isStaffRole(role)) return staffPath("dashboard");
  if (role === "member") return "/member";
  return null;
}

/** A login destination is honored only when the authenticated role may enter it. */
export function postLoginPath(returnTo: string | null, role: Role | null): string | null {
  const safeReturnTo = normalizeReturnTo(returnTo);
  if (safeReturnTo === "/") return homePathForRole(role);
  if (!safeReturnTo) return homePathForRole(role);

  const route = parseStudioRoute(safeReturnTo);
  if (route.type === "staff" && isStaffRole(role) && canSeePage(route.page, role)) {
    return route.path;
  }
  if (route.type === "member" && role === "member") return route.path;
  return homePathForRole(role);
}

function currentLocation(): string {
  if (typeof window === "undefined") return "/";
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

function subscribe(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener("popstate", listener);
  window.addEventListener(LOCATION_CHANGE_EVENT, listener);
  return () => {
    window.removeEventListener("popstate", listener);
    window.removeEventListener(LOCATION_CHANGE_EVENT, listener);
  };
}

/** Browser location as an external store, including programmatic and history changes. */
export function useStudioLocation(): string {
  return useSyncExternalStore(subscribe, currentLocation, () => "/");
}

export function navigateTo(path: string, replace = false): void {
  if (typeof window === "undefined") return;
  const url = new URL(path, window.location.origin);
  if (url.origin !== window.location.origin) {
    throw new Error("Studio navigation must stay on the current origin");
  }
  const destination = `${url.pathname}${url.search}${url.hash}`;
  if (replace) window.history.replaceState({}, "", destination);
  else window.history.pushState({}, "", destination);
  window.dispatchEvent(new Event(LOCATION_CHANGE_EVENT));
}

/** Page navigation updates the legacy UI selection and the shareable URL together. */
export function navigateToPage(page: PageId): void {
  useAppStore.getState().setPage(page);
  navigateTo(staffPath(page));
}
