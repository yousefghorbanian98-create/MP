# گزارش code-reviewer — M06 (فرانت‌اند) + بازرسی UI

## ⚠️ بازرسی UI (قول به کاربر — قبل از ساخت)
- موکاپ‌های تولیدشده و نمایش‌داده‌شده: `docs/MuscleParadise/ui-previews/`
  1. `01-studio-dashboard.png` — داشبورد Studio
  2. `02-client-today-workout.png` — برنامهٔ امروز موبایل
  3. `03-kiosk-face-gate.png` — کیوسک/گیت چهره
- UI واقعی دقیقاً مطابق همان زبان بصری ساخته شد؛ Live Preview از Vite dev server فعال است.

## دامنهٔ بازبینی
MP Studio (React+Vite+Zustand+Tailwind+Framer Motion+recharts)، MP Client (Flutter+Riverpod+flutter_animate)، طراحی RTL/تم

## یافته‌ها
| # | سطح | یادداشت |
|---|-----|---------|
| 1 | ✅ OK | RTL کامل فارسی: `dir="rtl"` در Studio + `Directionality.rtl` در Client |
| 2 | ✅ OK | حالت تاریک default در هر دو (برند #0B0F14) |
| 3 | ✅ OK | کنتراست WCAG محاسبه‌شده: متن ۱۷.۷:۱، زمرد ۷.۴:۱، طلا ۱۳.۷:۱ — همه PASS |
| 4 | ✅ OK | میکرو-ترنزیشن‌ها: AnimatedCounter، نشانگر layoutId سایدبار، stagger ورود لیست‌ها، AnimatePresence صفحات، shimmer skeleton، سوئیچ spring — و در Flutter: flutter_animate (fade/slide/shimmer/AnimatedSwitcher) |
| 5 | ✅ OK | فونت Vazirmatn (fontsource در Studio، asset در Client) |
| 6 | ✅ OK | طراحی شیشه‌ای (glassmorphism) یکپارچه در هر دو پوسته |
| 7 | ℹ️ Info | تست‌های Flutter در CI اجرا می‌شوند (D-002) — ۲ تست ویجت + ۲ تست واحد نوشته شد |

## Blockerها: **ندارد** ✅
## گیت‌ها: Studio: ۵ تست Vitest سبز + build موفق | تایپ‌اسکریپت سالم | کنتراست PASS
