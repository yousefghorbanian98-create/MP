# مشخصات میکرو-ترنزیشن‌ها (Motion Spec) — Muscle Paradise

> نسخه: ۱.۰ | چرخه: M07 | مرجع واحد Studio (Framer Motion) و Client (flutter_animate)
> اصل: «حرکت باید معنا بدهد، نه اینکه معطل کند» — هیچ انیمیشنی بیش از ۵۰۰ms مانع کاربر نمی‌شود.

## ۱. مقیاس زمانی (از design-tokens.json)

| توکن | مقدار | کاربرد |
|------|-------|--------|
| `motion.fast` | 150ms | hover، toggle، focus ring، micro-feedback دکمه |
| `motion.base` | 250ms | ورود کارت، تغییر صفحه، tooltip |
| `motion.slow` | 450ms | ورود پلکانی لیست‌ها، نمودارها، counterها |

## ۲. easing استاندارد

| نام | مقدار | کاربرد |
|-----|-------|--------|
| `ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | ورود عناصر (طبیعی متوقف می‌شود) |
| `spring` | stiffness 260 / damping 24 | جابه‌جایی نشانگرها، toggleها، layout |
| `ease-in-out` | `easeInOut` | حلقه‌های مداوم (scan line، shimmer) |

## ۳. الگوهای مصوب

| الگو | Studio (Framer Motion) | Client (flutter_animate) |
|------|------------------------|---------------------------|
| ورود صفحه | `AnimatePresence` + fade/slide-y 14px | PageRoute با fade |
| ورود پلکانی لیست | `delay: i * 0.05–0.08s` | `.animate().fadeIn(delay: 80ms * i)` |
| نشانگر فعال | `layoutId` + spring | `NavigationBar` با indicator |
| شمارندهٔ KPI | `animate()` + `useMotionValue` | `TweenAnimationBuilder` |
| toggle/سوئیچ | `layout` + spring | `AnimatedSwitcher` + ScaleTransition |
| hover کارت | `whileHover: y -4` + glow | — (mobile) |
| skeleton | shimmer 1.6s linear | shimmer با flutter_animate |
| progress ring | SVG stroke-dashoffset | `TweenAnimationBuilder<double>` |
| اسکن چهره | scan-line 2.8s loop | shimmer loop |

## ۴. قوانین دسترس‌پذیری حرکت
- احترام به `prefers-reduced-motion`: در Studio انیمیشن‌های غیرضروری کاهش می‌یابد (الگو: `useReducedMotion`)
- هیچ انیمیشنی حاوی فلش‌شدن سریع (بیش از ۳ بار در ثانیه) نیست
- transitionها هرگز layout را نمی‌شکنند (transform/opacity اولویت دارند)
