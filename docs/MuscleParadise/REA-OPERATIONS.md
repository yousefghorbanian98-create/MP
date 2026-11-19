# REA — راهنمای عملیاتی در لوپ FINN

> نسخه: ۱.۰ | تاریخ: ۲۰۲۶-۱۱-۱۵ | منبع رسمی: `github.com/morluto/rea` (MIT) — پکیج npm: `rea-agents`
> نقش در FINN: ابزار **Inspect** — کشف گپ، باگ، و رفتار رقبا **با شاهد (Evidence)**، نه با حدس.

---

## ۰. چرا این سند وجود دارد

بازبینی `REA-REVIEW-2026-11-15.md` با عنوان «بازبینی REA» نوشته شد، اما در آن زمان REA **نصب نبود**:
عامل نقش REA را به‌صورت متنی بازی کرده بود و «شاهد»ها خروجی `pytest`/`ruff` خودمان بودند، نه شاهد
ابزاری مستقل. نتیجه‌اش بد نبود (۵ باگ واقعی پیدا و رفع شد)، اما سه محدودیت داشت:

1. هیچ تحلیل **باینری/بستهٔ منتشرشده** انجام نشده بود — یعنی نمی‌شد ادعا کرد APKِ ساخته‌شده همان چیزی است که سورس می‌گوید.
2. مقایسه با رقبا از منابع عمومی متنی (README، وب‌سایت) بود، نه از رفتار واقعی محصول.
3. هر یافته شاهدِ ماشینیِ قابل‌ارجاع (Evidence ID + digest) نداشت.

از ۲۰۲۶-۱۱-۱۵ REA نسخهٔ ۶.۹.۰ نصب است و این سه محدودیت رفع شده است.

---

## ۱. وضعیت نصب در این محیط

| مورد | مقدار |
|---|---|
| نسخهٔ REA | `6.9.0` |
| اجراپذیر | `~/toolchain/rea/node_modules/.bin/rea` |
| Node لازم | `^22.23.4 \|\| ^24.22.1 \|\| >=26.12.1` — سیستم `22.22.3` بود ← portable `24.22.3` در `~/toolchain/node-linux-x64/bin/node` |
| Node سیستم | **کافی نیست** — همیشه با Node پرتابل صدا بزنید، وگرنه REA با پیام نسخه خارج می‌شود |
| skill | `tools/rea-skill/reverse-engineer-anything/` (۹ فایل، شامل ۸ مرجع تخصصی) |
| MCP | `.mcp.json` پروژه (gitignored — مسیر مطلق دارد) |
| موتور native | ❌ Hopper/Ghidra/IDA/JADX/Kuna نصب نیست (عمدی: نیاز نداریم) |

### فراخوانی صحیح

```bash
REA=~/toolchain/rea/node_modules/.bin/rea
NODE=~/toolchain/node-linux-x64/bin/node
"$NODE" "$REA" --version
"$NODE" "$REA" capabilities
```

> ⚠️ `~/.claude.json` دست‌نخورده ماند (بدون ثبت سراسری MCP). ثبت فقط پروژه‌ای است تا مخزن خودش مرجع باشد.

---

## ۲. مدل ذهنی REA (سه لایه)

```
هدف (target)  →  ابزار (tool)  →  شاهد (Evidence)
```

هر خروجی یک **Evidence record** با این ساختار است:

| فیلد | معنا |
|---|---|
| `evidence_id` | هش SHA-256 رکورد — قابل ارجاع در گزارش‌ها |
| `subject.digest.sha256` | هش خود فایل هدف (تضمین یکسانی ورودی) |
| `provider.id` | ابزاری که تحلیل کرده (`apk-signature`, `flutter`, `ghidra`, …) |
| `normalized_result` | یافته‌های ساخت‌یافته |
| `coverage` | `complete` / `partial` — **هرگز partial را کامل گزارش نکن** |
| `limitations` / `unknowns` | آنچه اثبات نشده — باید در گزارش بماند |

**سه تفکیک اجباری در هر گزارش REA:**

- **observation** — چیزی که ابزار مستقیم دید.
- **inference** — نتیجه‌گیری ما از آن (می‌تواند غلط باشد).
- **unknown** — چیزی که اثبات نشد.

---

## ۳. کدام توانایی در این محیط کار می‌کند؟

REA پیش‌فرض همهٔ ابزارها را آگهی می‌کند؛ در این محیط ~۳۰ ابزار واقعاً قابل‌استفاده است.

### ✅ بدون هیچ موتور native (فوراً قابل استفاده)

| حوزه | فرمان | کاربرد در MP |
|---|---|---|
| **Flutter build identity** | `identify-flutter-build` | اثبات اینکه APKِ منتشرشده با کدام Dart/engine ساخته شده (تست‌شده: `dart_version: 3.14.0`) |
| **APK signature** | `inspect-apk-signature` | v1/v2/v3، اثر انگشت گواهی، چرخش کلید — چک‌لیست انتشار |
| **APK manifest/resources** | `decode-android-resources` | نیاز به apktool (نصب نیست) |
| **JavaScript/Electron static** | `analyze-javascript-application` | **تحلیل باندل Studio** (Electron) — مسیر رانتایم، IPC، preload |
| **SQLite** | `inspect-sqlite-database` | **مهم:** تحلیل DB واقعی محصول (schema + نمونه سطر) |
| **HAR/network** | `compare-static-and-observed-endpoints` | مقایسهٔ endpointهای اعلام‌شده با فراخوانی واقعی |
| **Website/SPA** | `capture-browser-scenario`, `analyze-web-bundle` | نیاز به Chromium — در CI می‌شود، در این sandbox نه |
| **PE/ELF/WASM/GGUF/archives** | `inspect_artifact` و مشتقات | تحلیل عمومی باینری |
| **Process capture** | `capture-process` | نیاز به PTY — برای اسکریپت‌های CLI کار می‌کند |

### ❌ نیاز به موتور native (نصب نمی‌کنیم)

Ghidra / Hopper / IDA / Kuna → `decompile`, `trace_native_values`, Deep native analysis.
**تصمیم:** در MP لازم نیست. سورس کامل داریم؛ تحلیل native فقط برای رقبای بسته‌بندی‌شده لازم است که طبق
`COMPETITIVE-BENCHMARK-2026-11-14.md` از **منابع عمومی** استفاده می‌کنیم، نه دیکامپایل.

---

## ۴. پروتکل استفاده در هر چرخه (Inspect فاز)

```
Forge  →  Inspect (REA)  →  Normalize  →  Next
```

### ۴.۱ Inspect حداقلی — همهٔ چرخه‌ها

هر میکرو-چرخهٔ Mxx باید با این‌ها بسته شود:

```bash
# ۱) ثبات مصنوعات: هش فایل‌های تغییرکرده
sha256sum <changed files>

# ۲) اگر APK ساخته شد: هویت build را اثبات کن
"$NODE" "$REA" identify-flutter-build mp-app/client/release/app-arm64-v8a-release.apk

# ۳) اگر DB اسکیما تغییر کرد: DB واقعی را باز بخوان
"$NODE" "$REA" inspect-sqlite-database <path-to.db> --tables <new_table>
```

### ۴.۲ Inspect سنگین — تبلیغ چرخه‌ای (هر ۱۰ چرخه یا پایان هر فاز)

```bash
# Studio: باندل واقعی، نه src/
"$NODE" "$REA" analyze-javascript-application \
  /path/to/studio/release/linux-unpacked/resources/app.asar --json \
  --evidence_output finn/reports/rea/<cycle>-studio.json

# Backend: endpoint های اعلام‌شده در برابر فراخوانی‌شده
"$NODE" "$REA" compare-static-and-observed-endpoints \
  --static <js-analysis.json> --observed <har.json>
```

### ۴.۳ قواعد سخت‌گیرانه (از SKILL.md خود REA)

1. **قبل از هر تحلیل، digest هدف را ثبت کن** — بدون آن، یافته بازتولیدپذیر نیست.
2. **تحلیل یکسان را تکرار نکن** — اگر ورودی و پرسش یکی است، خروجی یکی است؛ اگر جواب کافی نبود، **پرسش را باریک کن**، نه کل تحلیل را.
3. **`detail: "summary"` اول** — برای اهداف بزرگ (باندل Studio ~۱۰ MB، APK ~۲۰ MB). سپس `inspect_analysis_view` روی `parent_evidence_id`.
4. **partial را کامل اعلام نکن** — `coverage: partial` باید در گزارش بماند.
5. **static ≠ runtime** — هرگز نگو «اجرا شد» وقتی ابزار فقط فایل را خواند. فقط ابزارهای `capture-*`/`observe-*` اجرا می‌کنند.
6. **Evidence ID را در گزارش بنویس** — گزارش بدون ID، ادعا است.

---

## ۵. محدودهٔ مجاز (این از قانون پروژه می‌آید، نه REA)

| هدف | مجاز؟ | مبنا |
|---|---|---|
| کد، APK، DB، باندل **خودمان** | ✅ آزاد | مالکیت پروژه |
| رقبای **متن‌باز** (wger، FitTrackee، GymOps...) | ✅ تحلیل سورس | مجوز OSS، D-022/E12 |
| رقبا از **منابع عمومی** (وب‌سایت، مستندات، App Store metadata) | ✅ | `COMPETITIVE-BENCHMARK-2026-11-14.md` |
| دیکامپایل/مهندسی معکوس **رقبای بسته** | ❌ ممنوع | D-022 + E12 + ریسک حقوقی |
| کپی محتوای مالکیتی رقبا | ❌ ممنوع | D-024 |

**خط قرمز:** REA توانایی دیکامپایل رقبای بسته را دارد. داشتن ابزار ≠ داشتن مجوز. قواعد بالا مقدم است.

---

## ۶. نوع سؤالاتی که در MP با REA جواب می‌گیریم

### الف) باگ‌یابی (جای بهتر از حدس)

| پرسش | ابزار |
|---|---|
| «آیا APKِ منتشر‌شده با آخرین سورس هم‌خوان است؟» | `identify-flutter-build` + مقایسه با CI build log |
| «این endpoint واقعاً کجا صداش می‌زنن؟» | `analyze-javascript-application` → trace از UI به فراخوانی |
| «DBِ تولید چه اسکیمایی دارد؟ آیا migration واقعاً اجرا شد؟» | `inspect-sqlite-database` |
| «کدام کد مرده است؟» | `analyze-javascript-application` → unreferenced modules |

### ب) کشف گپ

| پرسش | ابزار |
|---|---|
| «رقبای متن‌باز چه چیزهایی دارند که ما نداریم؟» | کلون OSS + تحلیل ساختاری (نه REA — کد سورس، ابزار عادی کافی است) |
| «رقبا در کلاینت خود چه قابلیت‌هایی نشان می‌دهند؟» | `capture-browser-scenario` (CI) + منابع عمومی |
| «چه endpointهایی وجود دارد ولی UI به آن‌ها وصل نیست؟» | `compare-static-and-observed-endpoints` |

### ج) بازبینی انتشار (قبل از هر release)

```bash
# چک‌لیست REA قبل از tag
"$NODE" "$REA" inspect-apk-signature <apk>
"$NODE" "$REA" identify-flutter-build <apk>
"$NODE" "$REA" audit-release-exposure <apk>       # چه چیزی از آرتیفکت قابل بازیابی است
```

`audit-release-exposure` مهم است: نشان می‌دهد آیا source map، debug symbol یا secret در بستهٔ منتشرشده مانده.

---

## ۷. خروجی استاندارد گزارش REA در FINN

هر گزارش در `finn/reports/rea/<cycle>-<topic>.md` با این قالب:

```markdown
# REA — Mxx / <موضوع>
- تاریخ: YYYY-MM-DD
- هدف: <path> — sha256: <digest>
- ابزار: <provider> v<version>
- پرسش: <یک جمله مشخص>

## مشاهدات (observation)
- <یافته> — Evidence: `ev_<hash>`

## استنباط (inference)
- <نتیجه> ← مبتنی بر <observation #n>

## نادانسته‌ها (unknown)
- <چیزی که اثبات نشد> — علت: <coverage partial / نیاز به provider>

## اقدام
- [ ] <تغییر لازم> — فایل: <path>
```

---

## ۸. عیب‌یابی سریع

| نشانه | علت | راه‌حل |
|---|---|---|
| `REA requires Node.js 22.x (>=22.23.4)...` | Node سیستم قدیمی | با `~/toolchain/node-linux-x64/bin/node` صدا بزن |
| `provider ... not_configured` | موتور native نیست | طبیعی است — سراغ ابزارهای بدون provider برو |
| `resource_constraint` / پاسخ بزرگ قطع شد | خروجی بزرگ‌تر از پنجرهٔ MCP | `detail: "summary"` + `inspect_analysis_view` روی `parent_evidence_id` |
| `VALIDATION_ERROR ... client.0` | مقدار `--client` اشتباه | مقدارهای مجاز: `claude_code`, `codex`, `cursor`, … (با `_`) |
| تحلیل JS روی `.asar` خطا داد | باید extract شود | `npx asar extract <asar> <dir>` سپس تحلیل دایرکتوری |

---

## ۹. تفاوت REA با ابزارهای دیگر لوپ

| ابزار | چه می‌دهد | چه نمی‌دهد |
|---|---|---|
| `pytest` | درستی منطق در سورس | رفتار بستهٔ منتشرشده |
| `ruff` / `tsc` | سلامت نحوی | کد مرده، مسیر واقعی رانتایم |
| **REA** | **شاهد از مصنوع واقعی + رفتار قابل‌مشاهده** | قضاوت محصولی، تصمیم طراحی |
| `code-reviewer` (ECC) | نقد کیفی کد | هش، digest، اثبات |
| `security-reviewer` (ECC) | الگوهای آسیب‌پذیری | افشای واقعی در باینری (← `audit-release-exposure`) |

**جمع‌بندی:** REA جای `pytest` را نمی‌گیرد؛ آنچه تست نمی‌تواند ثابت کند را ثابت می‌کند.
