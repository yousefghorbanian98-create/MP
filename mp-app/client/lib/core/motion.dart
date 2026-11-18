/// حرکت کم‌شده و زمان‌های مایکرو-انیمیشن (Q5 / M98).
///
/// سیگنال پلتفرم: Android «Reduce motion / animations off» و iOS «Reduce Motion»
/// هر دو به `MediaQueryData.disableAnimations` می‌رسند. تا پیش از این loop،
/// انیمیشن‌ها duration ثابت داشتند (`AnimatedSwitcher(duration: 250ms)`,
/// `.animate().fadeIn(duration: 400.ms)`) و کاربری که حرکت را در سیستم‌عامل
/// خاموش کرده، همان ترنزیشن‌ها را مجبوراً می‌دید.
///
/// این فایل دو چیز می‌دهد:
/// ۱) `MpMotion.reduced(context)` — خواندن سیگنال، با fallback امن؛
/// ۲) `MpMotion.dur(context, base)` — duration صفر وقتی حرکت کم شده.
///
/// برای `flutter_animate` از `target` استفاده می‌شود (`target: 0` یعنی همان
/// حالت نهایی بدون پخش انیمیشن) — بدون حذف خودِ انیمیشن، تا کد دو شاخه نشود.
///
/// محدودیت صادقانه: `HapticFeedback` «کاهش حرکت» نیست؛ لرزش عمداً از همین
/// فلگ پیروی نمی‌کند و کاربر/پلتفرم مسیر خودش را دارد (`MpHaptics.enabled`).
library;

import 'package:flutter/material.dart';

abstract final class MpMotion {
  /// آیا کاربر کاهش حرکت را فعال کرده است؟
  static bool reduced(BuildContext context) =>
      MediaQuery.maybeOf(context)?.disableAnimations ?? false;

  /// duration مناسب؛ صفر وقتی حرکت کم شده است.
  static Duration dur(BuildContext context, Duration base) =>
      reduced(context) ? Duration.zero : base;

  /// ضریب `target` در flutter_animate: ۰ یعنی بی‌انیمیشن، ۱ یعنی کامل.
  static double target(BuildContext context) => reduced(context) ? 0 : 1;
}
