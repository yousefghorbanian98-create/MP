/**
 * MEM-10 / PWA-39 — QR حضور.
 *
 * سه حالت قرارداد (replay / انقضا / عضو دیگر) در backend آزموده شده‌اند
 * (`tests/integration/test_m65_qr_security.py:144,160,131`)؛ این تست‌ها UI را
 * قفل می‌کنند و **ادعای اثبات حضور نمی‌سازند**:
 * - توکن در حافظه است، در localStorage ذخیره نمی‌شود.
 * - هیچ متن «حضور ثبت شد ✅» بدون تأیید سرور وجود ندارد؛ تاریخچه فقط از سرور می‌آید.
 * - face recognition صدا زده نمی‌شود (هیچ درخواستی به `/face/checkin` نمی‌رود).
 * - ۴۰۳ ⇒ fail-closed.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemberCheckin } from "../src/components/MemberCheckin";

function reply(status: number, body: unknown): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response;
}

const history = (items: unknown[] = [], hasMore = false) => ({
  items,
  limit: 10,
  offset: 0,
  has_more: hasMore,
  rule_version: "member-checkin-history-1.0",
  generated_at: "2026-11-27T10:00:00Z",
});

const row = {
  checkin_id: 5,
  method: "qr",
  result: "ok",
  denial_reason: "",
  checked_in_at: "2026-11-27T08:15:00Z",
  checked_out_at: null,
  is_open: true,
};

function installApi(handler: (path: string) => Response) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const raw = input instanceof Request ? input.url : String(input);
      const url = new URL(raw, window.location.href);
      calls.push(`${url.pathname}${url.search}`);
      return handler(url.pathname);
    }),
  );
  return calls;
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("mp_token", "member-access-token");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("member check-in QR (MEM-10)", () => {
  it("shows server history with its source and never claims presence by itself", async () => {
    const calls = installApi((path) => {
      if (path === "/api/v1/membership/me/checkins") return reply(200, history([row]));
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberCheckin />);

    expect(await screen.findByText(/تاریخچهٔ حضور/)).toBeTruthy();
    expect(screen.getByText(/روش: qr · نتیجه: ok/)).toBeTruthy();
    expect(screen.getByText(/منبع: GET \/api\/v1\/membership\/me\/checkins/)).toBeTruthy();
    // ادعای اثبات حضور در این نما نیست.
    expect(screen.getByText(/QR به‌تنهایی حضور یا هویت را اثبات نمی‌کند/)).toBeTruthy();
    expect(calls.some((path) => path.includes("/face/checkin"))).toBe(false);
  });

  it("issues a QR token, keeps it out of localStorage and warns about final confirmation", async () => {
    const calls = installApi((path) => {
      if (path === "/api/v1/membership/me/checkins") return reply(200, history());
      if (path === "/api/v1/face/qr-token") return reply(200, { payload: "signed.qr.token", member_id: 17 });
      throw new Error(`unexpected API path: ${path}`);
    });

    const { container } = render(<MemberCheckin />);
    fireEvent.click(await screen.findByRole("button", { name: "دریافت کد QR" }));

    await waitFor(() => expect(container.querySelector('[data-qr-payload]')).toBeTruthy());
    expect(screen.getByText("signed.qr.token")).toBeTruthy();
    expect(screen.getByText(/تأیید نهایی توسط مربی\/سیستم/)).toBeTruthy();
    expect(localStorage.length).toBe(1); // فقط mp_token؛ توکن QR ذخیره نشده
    expect(JSON.stringify(localStorage)).not.toContain("signed.qr.token");
    expect(calls).toContain("/api/v1/face/qr-token");
  });

  it("says 'nothing recorded' instead of zero presence", async () => {
    installApi((path) => {
      if (path === "/api/v1/membership/me/checkins") return reply(200, history([], false));
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberCheckin />);
    expect(await screen.findByText(/این «حضور صفر» نیست/)).toBeTruthy();
  });

  it("fails closed on 403", async () => {
    installApi((path) => {
      if (path === "/api/v1/membership/me/checkins") return reply(403, { error: { message: "forbidden" } });
      throw new Error(`unexpected API path: ${path}`);
    });

    render(<MemberCheckin />);
    expect((await screen.findByRole("alert")).textContent).toContain("دسترسی به تاریخچهٔ حضور مجاز نیست");
  });
});
