#!/usr/bin/env python3
"""M60 / R6 — انیمیشن حرکات: ساخت GIF از دو فریم شروع/پایان.

# چرا این کار ممکن شد (و قبلاً «مسدود» خطاب شده بود)

تصمیم قبلی ام «R6 مسدود است: ویدئوی تمرین نیاز به ffmpeg/منبع ویدئو دارد».
بازبینی نشان داد هر حرکت **دو فریم** دارد (`NN_0.jpg` شروع، `NN_1.jpg` پایان)
— یعنی همان چیزی که یک نمایش اجرای حرکت لازم دارد. با PIL (که در venv هست)
و یک درون‌یابی میان‌گذاری، یک GIF واقعی و صادقانه ساخته می‌شود.

# صداقت دربارهٔ محتوا

این GIF «ویدئوی تمرین» نیست: یک **میان‌گذاری دو فریم** است، نه فیلم برداشته‌شده.
روی خودِ تصویر هم یک برچسب دارد («فریم شروع ← پایان؛ انیمیشن تقریبی») تا
کسی با یک انیمیشن ساخته‌شده از دو عکس، تکنیک را یاد نگیرد. اگر بعداً ویدئوی
واقعی اضافه شود، همین مسیر (`media.gif_url`) بدون تغییر API جایگزین می‌شود.

# اجرا

    python scripts/build_exercise_gifs.py            # بساز
    python scripts/build_exercise_gifs.py --check    # فقط بگو چی هست/چی نیست
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

STATIC = Path(__file__).resolve().parents[1] / "static" / "exercises"
# اندازه‌ها با محدودیت مخزن انتخاب شده‌اند، نه سلیقه‌ای:
# ۶ فریم رفت‌وبرگشت × ۳۰۰px × پالت ۶۴رنگ ≈ ۱۰۰–۲۰۰KB برای هر حرکت.
# نسخهٔ اول (۱۰ فریم، ۲۵۶ رنگ، بهینه‌سازی پیش‌فرض) ۱۹٫۷MB شد — بی‌فایده برای
# یک مخزن گیت و برای دانلود در اپ روی شبکهٔ باشگاه.
FRAMES = 6
DURATION_MS = 120
SIZE = 240  # روی موبایل هم کافی است؛ ۳۰۰px در GIF گران تمام می‌شود
COLORS = 96


def _label(img: Image.Image, text: str) -> None:
    """برچسب پایین تصویر — تا این GIF با ویدئوی واقعی اشتباه نشود.

    متن **انگلیسی** است چون فونت پیش‌فرض PIL گلیف فارسی ندارد و تلاش اول
    متن فارسی را به مربع تبدیل کرد (دیده شد در تصویر خروجی). گزینهٔ دوم
    بارگذاری یک فونت فارسی است، ولی فایل فونت در مخزن نیست و دانلودش از
    این محیط مسدود — پس صادقانه‌ترین انتخاب، برچسب ASCII است.
    """
    draw = ImageDraw.Draw(img)
    # جعبهٔ نیمه‌شفاف پایین تصویر برای خوانایی روی هر پس‌زمینه‌ای
    box_h = 26
    box = img.crop((0, img.height - box_h, img.width, img.height)).convert("RGBA")
    overlay = Image.new("RGBA", box.size, (0, 0, 0, 150))
    img.paste(Image.alpha_composite(box, overlay).convert("RGB"), (0, img.height - box_h))
    draw.text((6, img.height - box_h + 8), text, fill=(255, 255, 255))


def build_one(stem: str) -> tuple[Path, int, float] | None:
    """یک GIF برای حرکت؛ خروجی (مسیر، تعداد فریم، حجم KB) یا None اگر فریم ناقص است."""
    start, end = STATIC / f"{stem}_0.jpg", STATIC / f"{stem}_1.jpg"
    if not (start.is_file() and end.is_file()):
        return None
    a = Image.open(start).convert("RGB").resize((SIZE, SIZE))
    b = Image.open(end).convert("RGB").resize((SIZE, SIZE))

    frames: list[Image.Image] = []
    # رفت و برگشت: شروع → پایان → شروع (یک تکرار کامل و قابل‌تماشا)
    for i in range(FRAMES):
        t = i / (FRAMES - 1)
        frames.append(Image.blend(a, b, t))
    for i in range(FRAMES - 2, 0, -1):
        t = i / (FRAMES - 1)
        frames.append(Image.blend(a, b, t))

    labelled = []
    for idx, f in enumerate(frames):
        img = f.copy()
        if idx == 0:
            hint = "  [START]"
        elif idx == FRAMES - 1:
            hint = "  [END]"
        else:
            hint = ""
        _label(img, "approximate motion - 2 frames" + hint)
        labelled.append(img)

    out = STATIC / f"{stem}.gif"
    buf = io.BytesIO()
    # تبدیل به پالت مشترک: بدون این، هر فریم پالت خودش را دارد و حجم چند برابر
    # می‌شود (GIF فقط ۲۵۶ رنگ در هر فریم دارد، ولی پالت تکراری هم ذخیره می‌شود).
    palette = labelled[0].quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)
    labelled = [f.quantize(palette=palette) for f in labelled]
    labelled[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=labelled[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
    )
    buf.seek(0)
    # دوباره باز کن تا خروجی واقعاً یک GIF معتبر باشد، نه بایت‌های خوش‌بینانه
    check = Image.open(io.BytesIO(buf.getvalue()))
    assert check.format == "GIF", check.format
    assert getattr(check, "n_frames", 1) == len(labelled), (check.n_frames, len(labelled))
    out.write_bytes(buf.getvalue())
    return out, len(labelled), len(buf.getvalue()) / 1024


def main() -> int:
    ap = argparse.ArgumentParser(description="ساخت GIF حرکات از دو فریم")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    stems = sorted({p.stem.rsplit("_", 1)[0] for p in STATIC.glob("*_0.jpg")})
    if args.check:
        missing = [s for s in stems if not (STATIC / f"{s}.gif").is_file()]
        print(f"{len(stems)} حرکت · {len(missing)} بدون GIF")
        return 1 if missing else 0

    built = 0
    total_kb = 0.0
    for stem in stems:
        res = build_one(stem)
        if res is None:
            print(f"! {stem}: فریم ناقص", file=sys.stderr)
            continue
        path, n, kb = res
        built += 1
        total_kb += kb
        print(f"✓ {path.name}  {n} فریم  {kb:.1f} KB")
    print(f"\n{built} GIF · {total_kb:.0f} KB مجموع")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
