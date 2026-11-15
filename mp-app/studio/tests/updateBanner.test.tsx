/**
 * M20 — بنر به‌روزرسانی (کامپوننت، نه فقط منطق).
 */
import { afterEach, describe, expect, it, vi } from "vitest";

/**
 * M20 — بنر به‌روزرسانی.
 *
 * باگ «کد مرده»: `UpdateBanner` کامل نوشته شده بود (با انیمیشن، دکمه،
 * postMessage به SW) ولی هیچ‌جا در App سوار نشده بود. یعنی کاربر هرگز
 * از نسخهٔ جدید باخبر نمی‌شد. این تست‌ها بنر را مستقیم می‌سنجند.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UpdateBanner } from "../src/components/UpdateBanner";

describe("UpdateBanner (M20)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("وقتی نسخهٔ جدید هست، پیام و دکمه را نشان می‌دهد", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              platform: "web",
              latest: "0.2.0",
              notes: "رفع باگ آمادگی",
              update_available: true,
              url: "",
            }),
            { status: 200 },
          ),
      ),
    );
    render(<UpdateBanner current="0.1.0" />);
    await waitFor(() => expect(screen.getByText(/نسخهٔ جدید 0.2.0 آماده است/)).toBeTruthy());
    expect(screen.getByRole("button", { name: "به‌روزرسانی" })).toBeTruthy();
  });

  it("وقتی نسخه به‌روز است، هیچ نواری نشان نمی‌دهد", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              platform: "web",
              latest: "0.1.0",
              notes: "",
              update_available: false,
              url: "",
            }),
            { status: 200 },
          ),
      ),
    );
    render(<UpdateBanner current="0.1.0" />);
    await new Promise((r) => setTimeout(r, 30));
    expect(screen.queryByRole("button", { name: "به‌روزرسانی" })).toBeNull();
  });

  it("دکمه، reload را فراخوانی می‌کند (نه یک دکمهٔ تشریفاتی)", async () => {
    const reload = vi.fn();
    vi.stubGlobal("location", { ...window.location, reload });
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              platform: "web",
              latest: "9.9.9",
              notes: "x",
              update_available: true,
              url: "",
            }),
            { status: 200 },
          ),
      ),
    );
    const user = userEvent.setup();
    render(<UpdateBanner current="0.1.0" />);
    await user.click(await screen.findByRole("button", { name: "به‌روزرسانی" }));
    await waitFor(() => expect(reload).toHaveBeenCalled(), { timeout: 1000 });
  });
});
