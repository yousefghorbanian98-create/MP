/// بازخورد لمسی (UX-G3 / M98) — یک لایهٔ نازکِ قابل‌تزریق.
///
/// چرا لایه، نه فراخوانی مستقیم `HapticFeedback` در ویجت‌ها:
/// ۱) تست ویجت باید بتواند «آیا واقعاً pulse فرستاده شد» را قطعیت بسنجد؛ اگر
///    هر صفحه مستقیم API پلتفرم را صدا بزند، باید `SystemChannels.platform` را
///    mock کنیم و رفتار کانال با نسخهٔ SDK عوض می‌شود (impactها در Flutterهای
///    تازه از `VibrationEffect` می‌روند، نه `HapticFeedback.vibrate`).
/// ۲) «بی‌صدا بودن» یک انتخاب کاربر/دستگاه است، نه سه‌سومِ صفحات. این‌جا یک‌جا
///    خاموش می‌شود.
/// ۳) پلتفرم رومیزی/PWA هیچ موتور لرزشی ندارد؛ فراخوانی باید بی‌ضرر باشد، نه
///    exception.
///
/// هر pulse به‌صورت fire-and-forget شلیک می‌شود و خطا را می‌بلعد: اگر لرزش شکست، ثبت بازخورد یا لغو
/// رزرو نباید شکست بخورد.
///
/// چرا `void` و نه `Future<void>`: نسخهٔ اول `await ref.read(hapticsProvider).success()`
/// بود و CI همان را گرفت — در تست ویجت (و روی دستگاهی که کانال پاسخ نمی‌دهد)
/// `await` روی کانال پلتفرم می‌تواند هرگز resolve نشود، پس `setState` بعدش اجرا
/// نمی‌شد و متن «اعمال شد» غیب می‌شد (`set_feedback_sheet_test.dart:100`).
/// بازخورد نباید هرگز بین نتیجهٔ سرویس و به‌روزرسانی UI فاصله بیاندازد.
library;

import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

abstract interface class MpHaptics {
  /// انتخاب/تغییر مقدار (اسلایدر، تب، عدد) — سبک‌ترین pulse.
  void select();

  /// عملیات موفق (ثبت شد، لغو شد، پرداخت شد).
  void success();

  /// عملیات ناموفق یا نتیجه‌ای که کاربر باید بازبینی کند.
  void warning();
}

/// پیاده‌سازی پیش‌فرض روی API فلاتر.
class SystemMpHaptics implements MpHaptics {
  const SystemMpHaptics({this.enabled = true});

  final bool enabled;

  @override
  void select() => _fire(HapticFeedback.selectionClick);

  @override
  void success() => _fire(HapticFeedback.mediumImpact);

  @override
  void warning() => _fire(HapticFeedback.heavyImpact);

  void _fire(Future<void> Function() pulse) {
    if (!enabled) return;
    // خطای کانال (MissingPluginException روی دسکتاپ/وب، پاسخ‌ندادن در تست) همین‌جا
    // بلعیده می‌شود تا هیچ فراخوانی معلق بی‌صدا بالا نماند.
    unawaited(
      pulse().catchError((Object _) {
        return;
      }),
    );
  }
}

/// در تست با یک fake جایگزین می‌شود؛ در اپ همان `SystemMpHaptics` است.
final hapticsProvider = Provider<MpHaptics>((ref) => const SystemMpHaptics());
