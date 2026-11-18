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
/// هر pulse fire-and-forget است و خطا را می‌بلعد: اگر لرزش شکست، ثبت بازخورد یا
/// لغو رزرو نباید شکست بخورد.
library;

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

abstract interface class MpHaptics {
  /// انتخاب/تغییر مقدار (اسلایدر، تب، عدد) — سبک‌ترین pulse.
  Future<void> select();

  /// عملیات موفق (ثبت شد، لغو شد، پرداخت شد).
  Future<void> success();

  /// عملیات ناموفق یا نتیجه‌ای که کاربر باید بازبینی کند.
  Future<void> warning();
}

/// پیاده‌سازی پیش‌فرض روی API فلاتر.
class SystemMpHaptics implements MpHaptics {
  const SystemMpHaptics({this.enabled = true});

  final bool enabled;

  @override
  Future<void> select() => _run(HapticFeedback.selectionClick);

  @override
  Future<void> success() => _run(HapticFeedback.mediumImpact);

  @override
  Future<void> warning() => _run(HapticFeedback.heavyImpact);

  Future<void> _run(Future<void> Function() pulse) async {
    if (!enabled) return;
    try {
      await pulse();
    } catch (_) {
      // MissingPluginException روی دسکتاپ/وب و رد شدن کانال در تست‌ها: بی‌صدا.
    }
  }
}

/// در تست با یک fake جایگزین می‌شود؛ در اپ همان `SystemMpHaptics` است.
final hapticsProvider = Provider<MpHaptics>((ref) => const SystemMpHaptics());
