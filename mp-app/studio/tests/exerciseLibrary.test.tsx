import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ExerciseLibrary } from "../src/components/ExerciseLibrary";

/**
 * G9 — کتابخانهٔ حرکات.
 *
 * نکتهٔ مهم: پیش از این `video_url` همیشه خالی بود و هیچ‌جا مصرف نمی‌شد؛
 * یعنی یک فیلد دکوراتیو. این تست‌ها ثابت می‌کنند تصویر واقعاً در UI
 * استفاده می‌شود و Alt متنی درست دارد (a11y، نه تصویر تزئینی).
 */

const exercises = [
  {
    exercise_id: 1,
    name_fa: "اسکوات پشت",
    name_en: "Barbell Squat",
    muscle_group: "legs",
    equipment: "barbell",
    difficulty: "intermediate",
    instructions_fa: "",
    image_url: "/static/exercises/1_0.jpg",
    image_url_alt: "/static/exercises/1_1.jpg",
    gif_url: "/static/exercises/1.gif",
  },
  {
    exercise_id: 2,
    name_fa: "پرس سینه",
    name_en: "Barbell Bench Press",
    muscle_group: "chest_shoulders",
    equipment: "barbell",
    difficulty: "intermediate",
    instructions_fa: "",
    image_url: "/static/exercises/2_0.jpg",
    image_url_alt: "/static/exercises/2_1.jpg",
    gif_url: "",
  },
];

function mockFetch(rows: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(rows), { status: 200 }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("ExerciseLibrary (G9)", () => {
  it("هر حرکت با تصویر واقعی و alt معنادار نمایش داده می‌شود", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(exercises));
    render(<ExerciseLibrary />);

    await waitFor(() => expect(screen.getByText("اسکوات پشت")).toBeTruthy());
    // M60/R6: وقتی انیمیشن هست، حالت بسته GIF نشان می‌دهد (نه فریم شروع).
    const img = screen.getByAltText("انیمیشن اجرای اسکوات پشت") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe("/static/exercises/1.gif");
    // تصویر تزئینی نیست: متن جانشین دارد
    expect(img.getAttribute("alt")).not.toBe("");
  });

  it("کلیک، فریم پایان را نشان می‌دهد (نه یک دکمهٔ بی‌اثر)", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch(exercises));
    const user = userEvent.setup();
    render(<ExerciseLibrary />);

    const card = await screen.findByRole("button", { name: /اسکوات پشت/ });
    await user.click(card);

    const img = screen.getByAltText("اجرای اسکوات پشت — فریم پایان") as HTMLImageElement;
    expect(img.getAttribute("src")).toBe("/static/exercises/1_1.jpg");
    expect(screen.getByText("Barbell Squat")).toBeTruthy();
  });

  it("گروه‌های عضلانی از خود داده ساخته می‌شوند و فیلتر کار می‌کند", async () => {
    localStorage.setItem("mp_token", "t");
    const fetchMock = mockFetch(exercises);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<ExerciseLibrary />);

    const legs = await screen.findByRole("button", { name: /پا \(۱\)/ });
    expect(screen.getByRole("button", { name: /سینه و سرشانه \(۱\)/ })).toBeTruthy();

    await user.click(legs);
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("muscle_group=legs"),
        expect.anything(),
      ),
    );
  });

  it("خطای شبکه پیام فارسی نشان می‌دهد، نه صفحهٔ خالی", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("network down");
      }),
    );
    render(<ExerciseLibrary />);

    await waitFor(() => expect(screen.getByText(/اتصال به سرور برقرار نشد/)).toBeTruthy());
  });

  it("فهرست خالی، پیام روشن می‌دهد", async () => {
    localStorage.setItem("mp_token", "t");
    vi.stubGlobal("fetch", mockFetch([]));
    render(<ExerciseLibrary />);
    await waitFor(() => expect(screen.getByText("حرکتی با این فیلتر پیدا نشد.")).toBeTruthy());
  });

  /**
   * M60/R6 — انیمیشن اجرا.
   *
   * GIF فقط وقتی استفاده می‌شود که سرور مسیر داده باشد؛ حرکتی که GIF ندارد
   * باید تصویر ثابت بگیرد، نه `src` خالی (که یعنی آیکون شکسته).
   */
  it("حرکت با GIF، انیمیشن می‌گیرد و حرکت بدون آن تصویر ثابت", async () => {
    vi.stubGlobal("fetch", mockFetch(exercises));
    render(<ExerciseLibrary />);
    await waitFor(() => expect(screen.getByText("اسکوات پشت")).toBeTruthy());

    const withGif = screen.getByAltText("انیمیشن اجرای اسکوات پشت") as HTMLImageElement;
    expect(withGif.getAttribute("src")).toBe("/static/exercises/1.gif");

    const withoutGif = screen.getByAltText("اجرای پرس سینه — فریم شروع") as HTMLImageElement;
    expect(withoutGif.getAttribute("src")).toBe("/static/exercises/2_0.jpg");
  });

  it("با کلیک، انیمیشن به فریم پایان ثابت تبدیل می‌شود", async () => {
    vi.stubGlobal("fetch", mockFetch(exercises));
    render(<ExerciseLibrary />);
    await waitFor(() => expect(screen.getByText("اسکوات پشت")).toBeTruthy());
    screen.getByAltText("انیمیشن اجرای اسکوات پشت").click();
    await waitFor(() => {
      const img = screen.getByAltText("اجرای اسکوات پشت — فریم پایان") as HTMLImageElement;
      expect(img.getAttribute("src")).toBe("/static/exercises/1_1.jpg");
    });
  });
});
