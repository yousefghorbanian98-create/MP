# M109 — بدهیِ `dart format` (۶۵ فایل) بدون Codespace پرداخت شد؛ گیت کشنده شد

- تاریخ: ۲۰۲۶-۱۱-۱۹ · شاخه: `arena/4f336f66-mp` · PR: **#1** (merge → `d9a5bdc`، روی شاخه در `65bbb5e`)
- محرک: کاربر یک بار دیگر پرسید «یک بار دیگه سریع چک کن که اگر واقعا نمی‌شود خودم دست به کار شوم».
  این گزارش، هم پاسخِ capability است و هم لاگِ کاری که همان پاسخ آزاد کرد.

## ۱) بازپرسیِ «چند لایه» — و اینکه جواب قبلی‌ام ناقص بود

| لایه | آزمون | نتیجه |
|---|---|---|
| دیدن codespace‌های اکانت | `GET /user/codespaces` | **200 و `total_count: 0`** — پس در این اکانت هیچ Codespace‌ای ساخته نشده بود (نه «من نمی‌بینم») |
| ساختن codespace | `POST /user/codespaces` با body تهی | **422** (اعتبارسنجی) ⇒ اجازه **هست** |
| start/stop | `POST /user/codespaces/<ghost>/start` | **404** ⇒ اجازه هست |
| ورود SSH | `POST /user/keys` | **403 “Resource not accessible by integration”** ⇒ هیچ کلیدی مجاز نمی‌شود؛ `gh codespace ssh` عملاً غیرممکن |
| شبکهٔ SSH از sandbox | `/dev/tcp` | `ssh.dev.azure.com:22` بسته · `github.com:22`، `direct.github.dev:22`، `api.github.dev:443` باز |
| dispatch workflow | `POST …/actions/workflows/ci.yml/dispatches` | **422** ⇒ اجازه هست |
| PR / issue | `POST /repos/…/pulls`, `/issues` | **422** ⇒ اجازه هست |
| merge PR | `gh pr merge` / merge محلی | مجاز (repo `permissions.admin: true`) |

**نتیجه:** «codespace را من ران نمی‌کنم» درست بود — ولی *آن کار* به codespace نیاز نداشت. تنها چیزی که
واقعاً به انسان نیاز دارد **دستگاه** است (§۶ runbook)، نه `dart format`.

## ۲) کاری که CI کرد

workflow جدید `client-format-fix` (dispatch-only؛ `contents: write` + `pull-requests: write` + `metadata: read`)
روی همان `3.50.0` / `ab2912035e…` که `.devcontainer/Dockerfile` پین کرده — و **قبل از هر کاری drift پین را
چک می‌کند**، چون خروجیِ فرمت به نسخهٔ SDK وابسته است:

1. شمارش بدهی (`--output=none --set-exit-if-changed`) → ۶۵
2. `dart format lib test tools`
3. idempotency: اجرای دوم هیچ چیزی را عوض نکرد
4. رفتار: `flutter pub get` + `flutter analyze --no-fatal-infos` + `flutter test --coverage` — سبز
5. stage: `git add -u -- '*.dart'` و **رد** اگر هر ورودیِ staged چیزی جز `M *.dart` باشد
6. اثبات: برای هر فایل، `git show HEAD:path` در برابر `git show :path` (خودِ blobِ staged)
7. commit + push شاخهٔ `ci/m109-dart-format` + **PR**، بدون هیچ commitی روی شاخهٔ session

## ۳) شواهد

| شاهد | عدد |
|---|---|
| annotationِ proof (run `44348498677`) | `layout proof PASS — staged=66 whitespace-only=1 comma-moved=65` |
| بازسنجی مستقل در sandbox (روی commit واقعی `d9a5bdc`) | `files=66 statuses=['M'] whitespace-only=1 comma-moved=65 REJECTED=0` · `66 files changed, 4965 insertions(+), 2731 deletions(-)` · **۰ فایل غیر از `.dart`** |
| بدهیِ پیشین (`client-pinned`، run `44325309997`) | ۶۵ فایل unformatted → **۰** پس از merge |

**چرا ۶۶ و نه ۶۵؟** شمارشِ گیت فایل‌هایی را می‌شمارد که `--set-exit-if-changed` «Changed» می‌گوید؛ یک
فایل تنها با حذف whitespace انتهایی/خط خالی درست شد و در شمارشِ قبل نمی‌گنجید. فایل‌های تغییریافته و
فایل‌هایِ «باید فرمت شوند» یکی نیستند؛ عددِ مرجع همان ۰ پس از فرمت است.

## ۴) سه باگی که همین loop بیرون داد (همه در همان workflow بسته شدند)

1. **`git add -A` در CI — بزرگ‌ترینش.** اجرای اول (`44346976960`) سه فایل بی‌ربط را داخل commitِ
   «فقط فرمت» گذاشت: `mp-app/client/coverage/lcov.info` (خروجی `flutter test --coverage`)،
   `pubspec.lock` (خروجی `flutter pub get`)، و **`analysis_options.yaml` که خودِ flutter** بلوک
   `analyzer: exclude: build/**, android/**` را در آن تزریق می‌کند. نه proof مقصر بود نه formatter:
   proof **زودتر** از گام‌های ابزار اجرا می‌شد و **روی درخت** قضاوت می‌کرد، نه روی چیزی که commit می‌شود.
   اگر من PR را بی‌بازبینی merge می‌کردم، یک commit «استایل» سه تغییر معنادار با خودش می‌برد.
2. **قاعدهٔ «فقط whitespace» برای dart کافی نیست.** tall-style formatter کامای انتهایی را وقتی فهرست
   را می‌شکند جابه‌جا می‌کند؛ ۶۵ از ۶۶ فایل به همان دلیل رد شدند. جواب، شل‌کردنِ چک نبود — **شمارشِ
   جدا** بود (`whitespace-only` در برابر `comma-moved`) تا هر دو عدد دیده شوند و چیزی قاپ زده نشود.
3. **دو نقصِ زیرساختی که شکست‌ها را کور می‌کرد:** GitHub workflow تازه را تا یک‌بار اجرا نشدن
   dispatch-پذیر نمی‌کند (`main` این مخزن فقط README.md دارد → `gh workflow run` 404 می‌داد؛ bootstrap با
   `push` به همان فایل)، و هیچ شکستی در job بدون `::error` چیزی برای خواندن نمی‌گذارد (لاگ این jobها از
   API خالی برمی‌گردد — R-036).
4. **و یک حدسِ غلطِ من، همان‌جا اصلاح شد:** شکستِ «Commit and open the PR» را به «نبودِ
   `metadata: read`» نسبت دادم و همان را به فایل اضافه کردم — نتیجه بدتر شد: `metadata` کلیدِ مجازِ
   `permissions` نیست و GitHub کل فایل را رد کرد (run `44349667465`: «failed to parse workflow:
   Unexpected value 'metadata'»، **صفر job**). راهِ درست و مستقیم: PR با `POST /repos/{}/{}/pulls`
   ساخته می‌شود که تنها `pull-requests: write` می‌خواهد، و `gh pr create` (با preflight‌های
   کاربر-محورش) کنار می‌رود. نشانهٔ «۰ job + name = path» یعنی **فایل parse نشد** — نه اینکه کارها
   شکست خوردند؛ این تشخیص را برای دفعهٔ بعد اینجا می‌نویسم.

## ۵) حالا چه چیزی عوض شد

- `ci.yml` → `client-pinned`: «dart format audit (غیربلاکینگ)» جایش را به **«dart format gate (M109 —
  کشنده)»** داد؛ `|| echo` حذف شد، و annotation حالا `dart format: clean (fatal gate since M109)` را
  می‌گوید (یا عدد فایل‌ها را با `::error`).
- `mp-app/client`: ۶۶ فایل فرمت‌شده. هیچ رفتار، هیچ API، هیچ رشته‌ای تغییر نکرد (بند ۳).
- بدهیِ «advisory» در TODO/LOOP-PLAN بسته شد؛ ریلِ Codespace به **§۶ گوشی** تقلیل یافت.

## ۶) بازگشت (rollback)

PR #1 را revert کن (`git revert -m 1 65bbb5e`) و در `ci.yml` گیت را به `|| echo` برگردان — همین. workflow
`client-format-fix.yml` بی‌ضرر است (dispatch-only و بدون تغییر خروجی اگر بدهی صفر باشد).

## ۷) تصمیمِ بازِ باقی‌مانده

`flutter` هر بار `analysis_options.yaml` را با بلوک `analyzer: exclude:` بازنویسی می‌کند. دو راه وجود دارد:
آن exclusion را commit کرد (و `flutter analyze` در هر محیطی از build/ و android/ رد می‌شود) یا گذاشتنِ
وضعیت موجود. هیچ‌کدام «تعمیر» نیست؛ یک تصمیمِ مالک است، و چون تحلیلِ lint را عوض می‌کند در صف مالک
نشست، نه در یک commitِ مکانیکی.
