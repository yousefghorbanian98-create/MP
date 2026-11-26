import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CheckIn } from "../src/pages/CheckIn";

let requests: string[] = [];
let originalMatchMedia: PropertyDescriptor | undefined;
let mediaMatches = false;
const mediaListeners = new Set<() => void>();
let setMotionPreference = (_matches: boolean): void => undefined;

beforeEach(() => {
  requests = [];
  localStorage.setItem("mp_token", "staff-session");
  originalMatchMedia = Object.getOwnPropertyDescriptor(window, "matchMedia");
  mediaMatches = false;
  mediaListeners.clear();
  const queryList = {
    get matches() {
      return mediaMatches;
    },
    media: "(prefers-reduced-motion: reduce)",
    onchange: null,
    addEventListener: vi.fn((_type: string, listener: () => void) => mediaListeners.add(listener)),
    removeEventListener: vi.fn((_type: string, listener: () => void) => mediaListeners.delete(listener)),
    addListener: vi.fn((listener: () => void) => mediaListeners.add(listener)),
    removeListener: vi.fn((listener: () => void) => mediaListeners.delete(listener)),
    dispatchEvent: vi.fn(),
  } as unknown as MediaQueryList;
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn(() => queryList),
  });
  setMotionPreference = (matches: boolean) => {
    mediaMatches = matches;
    for (const listener of [...mediaListeners]) listener();
  };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      requests.push(typeof input === "string" ? input : input.toString());
      return new Response(
        JSON.stringify({ items: [], rule_version: "checkins-1.0", generated_at: "2026-11-23T00:00:00Z" }),
        { status: 200 },
      );
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  if (originalMatchMedia) {
    Object.defineProperty(window, "matchMedia", originalMatchMedia);
  } else {
    Reflect.deleteProperty(window, "matchMedia");
  }
  localStorage.clear();
});

describe("CheckIn operational screen", () => {
  it("loads the real check-in feed and keeps the unmeasured SLO free of a fake percentage", async () => {
    render(<CheckIn />);

    await waitFor(() => expect(requests.some((url) => url.includes("/admin/checkins?limit=20"))).toBe(true));
    expect(screen.getByText("اندازه‌گیری‌نشده")).toBeTruthy();
    expect(screen.getByText(/شبیه‌سازی بصری — دوربین واقعی در این نسخه وصل نیست/)).toBeTruthy();
    expect(screen.getByText("هیچ ورودی ثبت نشده — دادهٔ نمایشی ساخته نمی‌شود.")).toBeTruthy();
    expect(screen.getByTestId("scan-motion")).toBeTruthy();
    expect(screen.queryByTestId("scan-static")).toBeNull();
    expect(screen.queryByText(/93%|۹۳٪/)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "توقف اسکن" }));
    expect(screen.getByText("اسکن متوقف شد")).toBeTruthy();
    expect(screen.getByRole("button", { name: "شروع اسکن" })).toBeTruthy();
  });

  it("uses a stationary scan cue in reduced mode and follows live changes without losing control focus", async () => {
    setMotionPreference(true);
    render(<CheckIn />);

    await waitFor(() => expect(requests.some((url) => url.includes("/admin/checkins?limit=20"))).toBe(true));
    expect(screen.getByTestId("scan-static")).toBeTruthy();
    expect(screen.queryByTestId("scan-motion")).toBeNull();

    const stopButton = screen.getByRole("button", { name: "توقف اسکن" });
    stopButton.focus();
    act(() => setMotionPreference(false));
    expect(screen.queryByTestId("scan-static")).toBeNull();
    expect(screen.getByTestId("scan-motion")).toBeTruthy();
    expect(document.activeElement).toBe(stopButton);

    act(() => setMotionPreference(true));
    expect(screen.getByTestId("scan-static")).toBeTruthy();
    expect(screen.queryByTestId("scan-motion")).toBeNull();
    expect(document.activeElement).toBe(stopButton);

    fireEvent.click(stopButton);
    expect(screen.getByText("اسکن متوقف شد")).toBeTruthy();
    expect(screen.queryByTestId("scan-static")).toBeNull();
  });
});
