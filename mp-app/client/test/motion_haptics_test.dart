/// M98 — دو لایهٔ UX-G3/Q5: `MpMotion` (کاهش حرکت) و `MpHaptics` (پالس لمسی).
///
/// چرا surface-channel: ادعای loop این است که پالس «واقعاً به پلتفرم می‌رود»، نه
/// اینکه یک تابع صدا زده می‌شود. پس mock روی `SystemChannels.platform` نشسته و
/// تعداد/نام فراخوانی‌ها خوانده می‌شود — بدون وابستگی به نام دقیق API در نسخه‌های
/// مختلف SDK (impactها در برخی نسخه‌ها `VibrationEffect.vibrate` می‌روند).
library;

import 'package:flutter/foundation.dart'
    show TargetPlatform, debugDefaultTargetPlatformOverride;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/haptics.dart';
import 'package:mp_client/core/motion.dart';

import 'haptics_recorder.dart';

Widget _withMotion({
  required bool disableAnimations,
  required Widget Function(BuildContext) builder,
}) {
  return MediaQuery(
    data: MediaQueryData(disableAnimations: disableAnimations),
    child: Builder(builder: builder),
  );
}

void main() {
  group('MpMotion — کاهش حرکت', () {
    testWidgets('disableAnimations=true → duration صفر و target صفر', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: _withMotion(
            disableAnimations: true,
            builder: (context) {
              expect(MpMotion.reduced(context), isTrue);
              expect(
                MpMotion.dur(context, const Duration(milliseconds: 250)),
                Duration.zero,
              );
              expect(MpMotion.target(context), 0);
              return const SizedBox.shrink();
            },
          ),
        ),
      );
    });

    testWidgets('بدون سیگنال → انیمیشن با همان duration قبلی می‌ماند', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: _withMotion(
            disableAnimations: false,
            builder: (context) {
              expect(MpMotion.reduced(context), isFalse);
              expect(
                MpMotion.dur(context, const Duration(milliseconds: 250)),
                const Duration(milliseconds: 250),
              );
              expect(MpMotion.target(context), 1);
              return const SizedBox.shrink();
            },
          ),
        ),
      );
    });

    testWidgets('هیچ MediaQuery‌ای نباشد → fallback امن (بی‌کاهش حرکت)', (
      tester,
    ) async {
      await tester.pumpWidget(
        Directionality(
          textDirection: TextDirection.rtl,
          child: Builder(
            builder: (context) {
              expect(MpMotion.reduced(context), isFalse);
              return const SizedBox.shrink();
            },
          ),
        ),
      );
    });
  });

  group('MpHaptics — پالس روی messenger پلتفرم', () {
    // چرا `test()` و نه `testWidgets()`: در تست ویجت زمان FakeAsync است و هر تخلیه‌ای
    // که روی `Future.delayed` واقعی بنشیند (مثل `pumpEventQueue()`) برنمی‌گردد —
    // run های 44295081645/44298469682 دقیقاً همین را خوردند. همین‌جا event loop
    // واقعی است و messenger بی‌واسطه خوانده می‌شود.
    // `debugDefaultTargetPlatformOverride` داخل بدنهٔ تست ست و همان‌جا با
    // `addTearDown` برمی‌گردد؛ در `testWidgets` این تغییر با invariant بایندینگ
    // درگیر می‌شد.
    late List<MethodCall> platformCalls;
    late TestDefaultBinaryMessenger messenger;

    setUp(() {
      platformCalls = <MethodCall>[];
      // بدون کست دوم: `TestDefaultBinaryMessengerBinding.defaultBinaryMessenger`
      // خودش `TestDefaultBinaryMessenger` است و کست اضافه، `flutter analyze` را با
      // UNNECESSARY_CAST (warning) قرمز می‌کند — این گیت warning‌ها را هم fail
      // می‌کند، پس «cast برای وضوح» اینجا مجاز نیست.
      messenger =
          (TestWidgetsFlutterBinding.ensureInitialized()
                  as TestDefaultBinaryMessengerBinding)
              .defaultBinaryMessenger;
      messenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        platformCalls.add(call);
        return null;
      });
      // `_platformFeedbackSupported` در `HapticFeedback` روی linux/macOS/windows
      // no-op است؛ روی runner لیناکسی CI بدون این override هیچ پیامی نمی‌رفت و
      // «صفر فراخوانی» بی‌معنی سبز می‌شد.
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
      addTearDown(() {
        debugDefaultTargetPlatformOverride = null;
        messenger.setMockMethodCallHandler(SystemChannels.platform, null);
      });
    });

    Future<void> drain() => Future<void>.delayed(Duration.zero);

    test('لایهٔ ما همان چیزی را می‌فرستد که خودِ API فلاتر می‌فرستد', () async {
      // baseline: روی همین SDK و همین runner، خودِ `HapticFeedback` چند پیام
      // می‌فرستد؟ اگر صفر شد، ادعا معلق می‌ماند (skip با دلیل) — نه سبزِ توخالی.
      await HapticFeedback.selectionClick();
      await HapticFeedback.mediumImpact();
      await HapticFeedback.heavyImpact();
      await drain();
      final baseline = platformCalls.length;
      if (baseline == 0) {
        markTestSkipped(
          'این Flutter روی این runner برای HapticFeedback پیامی نمی‌فرستد؛ '
          'تطبیق شمارش بی‌معنی است',
        );
        return;
      }
      platformCalls.clear();

      const haptics = SystemMpHaptics();
      haptics.select();
      haptics.success();
      haptics.warning();
      await drain();

      expect(
        platformCalls,
        hasLength(baseline),
        reason: 'لایه باید پیام‌ها را نه کم کند نه دو برابر',
      );
      expect(
        platformCalls.map((c) => c.method),
        everyElement(anyOf(contains('HapticFeedback'), contains('Vibration'))),
      );
      // «موفق/انتخاب» نباید پیامی یکسان باشند؛ این معنا فقط وقتی قابل‌سنجش است که
      // SDK بیشتر از یک پیام بفرستد (با یک پیام، جداسازی آرگومان تعریف‌نشده است).
      if (platformCalls.length > 1) {
        expect(
          platformCalls.map((c) => c.arguments).toSet().length,
          greaterThan(1),
          reason:
              'اگر همهٔ پالس‌ها یک آرگومان داشتند، موفق و انتخاب یکی می‌شدند',
        );
      }
    });

    test('enabled=false → هیچ فراخوانی پلتفرم نه', () async {
      const haptics = SystemMpHaptics(enabled: false);
      haptics.select();
      haptics.success();
      haptics.warning();
      await drain();
      expect(platformCalls, isEmpty);
    });

    test('رابط MpHaptics بدون پلتفرم هم قابل استفاده است (fake تست‌ها)', () {
      final fake = RecordingHaptics();
      fake.select();
      fake.success();
      fake.warning();
      expect(fake.events, ['select', 'success', 'warning']);
    });
  });
}
