import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CouponPanel } from "../src/components/CouponPanel";

/**
 * G2 — پنل کد تخفیف: ساخت کد درصدی با سقف استفاده و فهرست کدها.
 * تخفیف در سرور محاسبه می‌شود؛ این تست فقط درخواستِ ارسالی را می‌سنجد.
 */

const created = {
  id: 3,
  code: "SPRING10",
  kind: "percent",
  value: 10,
  expires_at: null,
  max_uses: 50,
  used_count: 0,
  is_active: true,
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("CouponPanel", () => {
  it("کد درصدی با سقف استفاده را به API می‌فرستد و فهرست را تازه می‌کند", async () => {
    const posts: unknown[] = [];
    let listed: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (init?.method === "POST" && url.endsWith("/payments/coupons")) {
          posts.push(JSON.parse(String(init.body)));
          listed = [created];
          return new Response(JSON.stringify(created), { status: 201 });
        }
        if (url.endsWith("/payments/coupons")) {
          return new Response(JSON.stringify(listed), { status: 200 });
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<CouponPanel />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("کد"), "spring10");
    await user.clear(screen.getByLabelText("سقف استفاده"));
    await user.type(screen.getByLabelText("سقف استفاده"), "50");
    await user.click(screen.getByRole("button", { name: "ساخت کد" }));

    await waitFor(() => expect(posts).toHaveLength(1));
    expect(posts[0]).toMatchObject({ code: "spring10", kind: "percent", value: 10, max_uses: 50 });
    expect(await screen.findByText("SPRING10")).toBeTruthy();
  });

  it("خطای سرور به‌صورت هشدار نمایش داده می‌شود", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method === "POST") {
          return new Response(
            JSON.stringify({ error: { code: "conflict", message: "این کد تخفیف قبلاً ثبت شده است" } }),
            { status: 409 },
          );
        }
        return new Response("[]", { status: 200 });
      }),
    );

    render(<CouponPanel />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("کد"), "DUP");
    await user.click(screen.getByRole("button", { name: "ساخت کد" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
