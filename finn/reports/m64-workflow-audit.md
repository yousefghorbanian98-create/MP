# M64 — بازبینی و محدودسازی مسیرهای خودکار GitHub

> تاریخ: 2026-11-16 | شاخه: `arena/4f336f66-mp` | بررسی محلی؛ **هیچ workflowای اجرا نشد**.

## تغییر و پذیرش

- `.github/workflows/ci.yml`: سطح مجوز workflow به `contents: read` محدود شد؛ تشخیص‌های خطای backend/Flutter دیگر branch را fetch/reset/commit/push نمی‌کنند و فقط به artifact با retention هفت‌روزه می‌روند.
- `.github/workflows/apk.yml`: build جاب `contents: read` و `persist-credentials: false` دارد. diagnostics فقط artifact هفت‌روزه است. تحویل دستی روی branch فقط در جاب جداگانهٔ `workflow_dispatch` با `actions:read` + `contents:write` انجام می‌شود؛ upload به GitHub Release فقط در جاب tag با همین مجوزهای محدود است. `issues:write` حذف شد.
- `.github/workflows/deploy.yml`: build فقط `contents:read`؛ جاب deploy و rollback مجوز `GITHUB_TOKEN` ندارند (`permissions: {}`)، اما webhook محافظت‌شدهٔ Dokploy همچنان قابلیت deploy دارد.
- `.github/workflows/container.yml`: `contents:read` + `packages:write` فقط برای push به GHCR باقی است.

## جدول سطح اثر

| Workflow | اثر مجازِ باقی‌مانده | قید/شاهد |
|---|---|---|
| `ci.yml` | هیچ write روی repository؛ upload diagnostics | `contents:read`; هیچ `git fetch/reset/commit/push` در فایل باقی نمانده |
| `apk.yml` build | read source + upload artifact | `contents:read`, checkout با `persist-credentials:false`; بدون commit/release در build job |
| `apk.yml` manual delivery | commit/push APK فقط پس از workflow_dispatch موفق روی همان ref غیر tag | جاب جدا، `actions:read` + `contents:write`; اجرا نشد |
| `apk.yml` release | upload artifact به Release موجود فقط روی tag | جاب جدا، `actions:read` + `contents:write`; اجرا نشد |
| `container.yml` | push image به GHCR | `packages:write` لازم برای هدف workflow؛ هیچ دسترسی `contents:write` ندارد |
| `deploy.yml` | deploy از طریق secret webhook در triggerهای تعریف‌شده | `GITHUB_TOKEN` در deploy/rollback خنثی است؛ secret وبهوک همچنان deploy-capable است و به n8n داده نشده |

## بررسی ایستا و محدودیت شاهد

- `js-yaml` parser از طریق `npm exec` هر چهار فایل `.github/workflows/*.yml` را بدون خطای syntax parse کرد.
- بازبینی `rg` روی permission/write paths: CI diagnostics دیگر git-write ندارند؛ تنها repo-write موجود در APK جاب تحویل دستیِ جداست؛ Release/tag، GHCR و Dokploy به‌صورت مجزا مشخص شدند.
- هیچ build/test/CI، push، release یا deploy اجرا نشد. این گزارش صحت اجرای واقعی GitHub runner یا تنظیمات branch protection/secrets در GitHub را اثبات نمی‌کند.
- **هیچ n8n notifier متصل نشده است.** پیش از notifier احتمالی هنوز باید read-only GitHub credential محدود به همین repo (`actions:read`)، فیلدهای پیام حداقلی، destination تیم و دسترسی واقعی در GitHub جدا بررسی شوند؛ log/artifact/source به notifier داده نشود.
- نتیجه: مسیرهای شکست CI write ندارند و جاب build APK از جاب‌های نوشتنی جداست. این بازبینی مجوز اجرای هیچ فرایند release/deploy یا فعال‌سازی n8n نیست.
