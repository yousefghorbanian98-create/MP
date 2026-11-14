# بودجهٔ عملکرد Muscle Paradise (M12)

| مسیر | SLO | اندازه‌گیری |
|------|-----|-------------|
| گیت ورود (چهره/QR) | ۹۹٪ زیر ۲ ثانیه | Prometheus + k6 (M14) |
| API خواندنی (لیست‌ها) | p95 < 300ms | کش Valkey (TTL 30s) |
| صفحهٔ «امروز» (Flutter) | < 1s با آفلاین | drift cache + lazy loading |
| build استودیو | < 5s (Vite) | CI |

## قواعد کش (لایهٔ ۱۲)
1. فقط دادهٔ عمومی/کم‌تغییر کش می‌شود (لیست اعضا، کتابخانهٔ حرکات) — دادهٔ شخصی فقط با invalidation صریح
2. **هر نوشتن = invalidation** (تست `test_stale_member_list_not_served_after_create`)
3. TTL کوتاه (۳۰s) به‌عنوان کمربند ایمنی دوم
4. fallback درون‌حافظه‌ای وقتی Valkey در دسترس نیست (NFR-6)

## Lazy loading (Flutter — M06/M12)
- لیست‌های بلند با `ListView.builder` (ساخت در لحظهٔ نمایش)
- تصاویر با cache + اندازهٔ مناسب (ffmpeg در M11)
