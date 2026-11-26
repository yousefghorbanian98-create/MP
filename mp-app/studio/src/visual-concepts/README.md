# Muscle Paradise — UI/UX Concept Lab

این صفحه یک پیش‌نمایش مستقل برای مقایسهٔ سه جهت بصری است؛ به برنامهٔ اصلی، API، احراز هویت یا ذخیره‌سازی داده وصل نیست و هیچ‌یک از CTAها عملیات محصولی انجام نمی‌دهند.

## اجرای محلی

از پوشهٔ `mp-app/studio`:

```bash
npm ci
npm run dev -- --host 0.0.0.0
```

سپس مسیر `/visual-concepts.html` را باز کنید.

## استفادهٔ مجدد از OSS موجود در Studio

هیچ dependency تازه‌ای اضافه نشده است. این نمونه مستقیماً از پکیج‌های موجود در `package.json` استفاده می‌کند:

- [Ant Design](https://github.com/ant-design/ant-design) — MIT: `Button`, `Card`, `Tag`, `Segmented`, `Progress`, `Drawer`, `Modal`, `Input` و پیام‌های تعاملی.
- [Motion](https://github.com/motiondivision/motion) (پکیج نصب‌شده با نام `framer-motion`) — MIT: `motion` و `AnimatePresence` با helper مشترک `useMotionPreset` برای ورود صفحه/کارت‌ها و احترام محافظه‌کارانه به کاهش حرکت.
- [Ant Design Icons](https://github.com/ant-design/ant-design-icons) — MIT: آیکون‌های ناوبری و کنش‌ها.
- Vazirmatn از پکیج محلی `@fontsource-variable/vazirmatn`؛ بدون فونت/CDN راه‌دور.
- توکن‌های برند/حرکت از `mp-app/shared/design-tokens.json` و `mp-app/shared/motion-spec.md` الگو گرفته‌اند.

`web-interface-guidelines` و `modern-web-guidance` در این طرح مرجع کیفیت‌اند، نه dependency یا منبع کد کامپوننت. گزینه‌ها پیشنهاد طراحی‌اند و انتخاب نهایی، تعیین مقصد CTAها، قرارداد API و فلوچارت کامل را جایگزین نمی‌کنند.
