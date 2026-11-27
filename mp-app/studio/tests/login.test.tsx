import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Login } from "../src/pages/Login";

const { signInMock } = vi.hoisted(() => ({ signInMock: vi.fn() }));

vi.mock("../src/auth/AuthContext", () => ({
  useAuth: () => ({ signIn: signInMock, notice: null }),
}));

function reply(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function enterValidPhone() {
  fireEvent.change(screen.getByLabelText("شمارهٔ موبایل"), { target: { value: "09121234567" } });
}

beforeEach(() => {
  localStorage.clear();
  signInMock.mockReset();
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  localStorage.clear();
});

describe("Login OTP form", () => {
  it("rejects an invalid phone without making a request", async () => {
    const fetchMock = vi.mocked(fetch);
    render(<Login />);
    fireEvent.change(screen.getByLabelText("شمارهٔ موبایل"), { target: { value: "0912" } });
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    expect((await screen.findByRole("alert")).textContent).toContain("شمارهٔ موبایل باید ۱۱ رقم");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the server rate-limit response and keeps the code step closed", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(reply(429, { error: { message: "ارسال کد فعلاً محدود شده است" } }));
    render(<Login />);
    enterValidPhone();
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    expect((await screen.findByRole("alert")).textContent).toContain("ارسال کد فعلاً محدود شده است");
    expect(screen.queryByLabelText("کد یک‌بارمصرف")).toBeNull();
  });

  it("shows loading while the OTP request is pending", async () => {
    const fetchMock = vi.mocked(fetch);
    let resolveRequest!: (response: Response) => void;
    fetchMock.mockReturnValueOnce(new Promise<Response>((resolve) => { resolveRequest = resolve; }));
    render(<Login />);
    enterValidPhone();
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    const loadingButton = screen.getByRole("button", { name: "در حال ارسال…" }) as HTMLButtonElement;
    expect(loadingButton.disabled).toBe(true);
    resolveRequest(reply(200, { phone: "09121234567", expires_in: 120 }));
    expect(await screen.findByLabelText("کد یک‌بارمصرف")).toBeTruthy();
  });

  it("shows a server-returned development code in a development build", async () => {
    vi.stubEnv("DEV", true);
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(reply(200, {
      phone: "09121234567",
      expires_in: 120,
      dev_code: "654321",
    }));
    render(<Login />);
    enterValidPhone();
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    expect(await screen.findByText(/کد آزمایشی محیط توسعه/)).toBeTruthy();
    expect(screen.getByText("654321")).toBeTruthy();
  });

  it("does not display a server-returned development code in a production build", async () => {
    vi.stubEnv("DEV", false);
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(reply(200, {
      phone: "09121234567",
      expires_in: 120,
      dev_code: "654321",
    }));
    render(<Login />);
    enterValidPhone();
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));

    expect(await screen.findByLabelText("کد یک‌بارمصرف")).toBeTruthy();
    expect(screen.queryByText(/کد آزمایشی محیط توسعه/)).toBeNull();
    expect(screen.queryByText("654321")).toBeNull();
  });

  it("surfaces an incorrect or expired OTP error without persisting a session", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(reply(200, { phone: "09121234567", expires_in: 120 }));
    signInMock.mockRejectedValueOnce(new Error("کد اشتباه یا منقضی شده است"));
    render(<Login />);
    enterValidPhone();
    fireEvent.click(screen.getByRole("button", { name: "دریافت کد ورود" }));
    fireEvent.change(await screen.findByLabelText("کد یک‌بارمصرف"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "ورود امن" }));

    expect((await screen.findByRole("alert")).textContent).toContain("کد اشتباه یا منقضی شده است");
    expect(signInMock).toHaveBeenCalledWith("09121234567", "123456");
    expect(localStorage.getItem("mp_token")).toBeNull();
    expect(localStorage.getItem("mp_refresh")).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
