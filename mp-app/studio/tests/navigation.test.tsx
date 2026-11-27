import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  STAFF_PAGES,
  navigateToPage,
  normalizeReturnTo,
  parseStudioRoute,
  postLoginPath,
  useStudioLocation,
} from "../src/lib/navigation";
import { useAppStore } from "../src/stores/appStore";

function RouteProbe() {
  const location = useStudioLocation();
  const route = parseStudioRoute(location);
  const label = route.type === "staff" ? route.path : route.type;
  return (
    <>
      <output aria-label="مسیر جاری">{label}</output>
      <button type="button" onClick={() => navigateToPage("members")}>رفتن به اعضا</button>
    </>
  );
}

beforeEach(() => {
  window.history.replaceState({}, "", "/staff/dashboard");
  useAppStore.setState({ page: "dashboard", selectedMemberId: null, search: "" });
});

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("Studio URL routes", () => {
  it("maps login, member, and staff paths without treating unknown paths as pages", () => {
    expect(parseStudioRoute("/login?returnTo=%2Fstaff%2Fmembers")).toEqual({
      type: "login",
      path: "/login",
      returnTo: "/staff/members",
    });
    expect(parseStudioRoute("/member")).toEqual({ type: "member", path: "/member", page: "home" });
    expect(parseStudioRoute("/member/today")).toEqual({
      type: "member",
      path: "/member/today",
      page: "today",
    });
    expect(parseStudioRoute("/staff/finance")).toEqual({
      type: "staff",
      path: "/staff/finance",
      page: "finance",
    });
    expect(parseStudioRoute("/staff/")).toEqual({
      type: "staff",
      path: "/staff/dashboard",
      page: "dashboard",
    });
    expect(parseStudioRoute("/staff/not-a-page").type).toBe("not-found");
    expect(parseStudioRoute("/staff/members/12").type).toBe("not-found");
  });

  it("maps every PageId to its own canonical staff URL", () => {
    for (const page of STAFF_PAGES) {
      expect(parseStudioRoute(`/staff/${page}`)).toEqual({
        type: "staff",
        path: `/staff/${page}`,
        page,
      });
    }
  });

  it("rejects external, malformed, query-bearing, and unknown login destinations", () => {
    expect(normalizeReturnTo("/staff/members")).toBe("/staff/members");
    expect(normalizeReturnTo("/")).toBe("/");
    expect(normalizeReturnTo("//attacker.example/path")).toBeNull();
    expect(normalizeReturnTo("https://attacker.example/")).toBeNull();
    expect(normalizeReturnTo("/\\attacker.example/path")).toBeNull();
    expect(normalizeReturnTo("/staff/not-a-page")).toBeNull();
    expect(normalizeReturnTo("/staff/members?member_id=12")).toBeNull();
    expect(normalizeReturnTo("/staff/members#private")).toBeNull();
    expect(normalizeReturnTo("/member/today")).toBe("/member/today");
    expect(normalizeReturnTo("/member/today?member_id=2")).toBeNull();
    expect(postLoginPath("/staff/settings", "manager")).toBe("/staff/dashboard");
    expect(postLoginPath("/staff/members", "member")).toBe("/member");
    expect(postLoginPath("/member/today", "member")).toBe("/member/today");
    expect(postLoginPath("/member/today", "manager")).toBe("/staff/dashboard");
  });

  it("keeps the address bar, active route, and browser back/forward in sync", async () => {
    render(<RouteProbe />);
    expect(screen.getByLabelText("مسیر جاری").textContent).toBe("/staff/dashboard");

    fireEvent.click(screen.getByRole("button", { name: "رفتن به اعضا" }));
    await waitFor(() => expect(window.location.pathname).toBe("/staff/members"));
    expect(screen.getByLabelText("مسیر جاری").textContent).toBe("/staff/members");

    const waitForPopState = () =>
      new Promise<void>((resolve) => {
        window.addEventListener("popstate", () => resolve(), { once: true });
      });
    await act(async () => {
      const popped = waitForPopState();
      window.history.back();
      await popped;
    });
    await waitFor(() => expect(window.location.pathname).toBe("/staff/dashboard"));
    expect(screen.getByLabelText("مسیر جاری").textContent).toBe("/staff/dashboard");

    await act(async () => {
      const popped = waitForPopState();
      window.history.forward();
      await popped;
    });
    await waitFor(() => expect(window.location.pathname).toBe("/staff/members"));
    expect(screen.getByLabelText("مسیر جاری").textContent).toBe("/staff/members");
  });
});
