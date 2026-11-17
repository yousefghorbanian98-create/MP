# سیستم دیزاین Muscle Paradise — MP Design System

> نسخه: ۱.۰ | چرخه: M07 | منبع حقیقت: `mp-app/shared/design-tokens.json`

## ۱. اصول
1. **تاریک، همیشه** — حالت تاریک پیش‌فرض برند است (#0B0F14)
2. **شیشه‌ای اما خوانا** — glassmorphism فقط با حفظ کنتراست WCAG AA
3. **حرکت با معنا** — طبق `mp-app/shared/motion-spec.md`
4. **فارسی RTL اول** — همه چیز ابتدا برای فارسی طراحی می‌شود؛ Vazirmatn

## ۲. توکن‌ها (همگام: design-tokens.json ↔ tailwind.config.js ↔ Flutter theme)

| دسته | توکن‌ها |
|------|---------|
| رنگ | bg `#0B0F14` · surface `#111827` · primary `#00B86A` · accent `#FFD700` · danger `#F87171` |
| تایپوگرافی | Vazirmatn — display 32 / title 24 / heading 18 / body 14 / caption 12 |
| فاصله | xs 4 / sm 8 / md 16 / lg 24 / xl 32 |
| شعاع | sm 8 / md 12 / lg 16 / full 999 |
| سایه | glow (زمردی) / glow-gold / glass |

## ۳. کامپوننت‌ها (Studio)
| کامپوننت | کلاس/فایل | قاعده |
|----------|-----------|--------|
| کارت شیشه‌ای | `.glass-card` / `.glass-card-hover` | مرز زمردی ۱۵٪، blur، hover glow |
| دکمه | `.btn-primary` / `.btn-ghost` | active:scale 0.98 — micro-feedback |
| pill وضعیت | `.pill-green/.pill-gold/.pill-red` | وضعیت‌های سه‌گانه |
| skeleton | `.skeleton` | shimmer |
| شمارنده | `AnimatedCounter` | فقط اعداد فارسی (fa-IR) |
| نشانگر nav | `Sidebar` + layoutId | spring حرکت می‌کند |

**قانون (M07):** فقط یک سیستم کامپوننت (shadcn/ui + Tailwind — D-005)؛ هرگز DaisyUI همزمان.

## ۴. کنتراست (WCAG AA — محاسبه‌شده، چرخهٔ M06)
| جفت رنگ | نسبت | حد |
|---------|------|-----|
| متن `#F3F6F8` روی `#0B0F14` | 17.71:1 | 4.5 ✓ |
| زمرد `#00B86A` روی `#0B0F14` | 7.38:1 | 3.0 ✓ |
| طلا `#FFD700` روی `#0B0F14` | 13.70:1 | 3.0 ✓ |
| متن کمکی `#9CA3AF` روی `#0B0F14` | 7.57:1 | 4.5 ✓ |

## ۵. همگام‌سازی توکن‌ها (مکانیکی)
تست `mp-app/studio/tests/design-tokens.test.ts` تطابق tailwind.config.js با design-tokens.json را چک می‌کند — هرگونه واگرایی = تست قرمز = چرخه قبول نیست.
