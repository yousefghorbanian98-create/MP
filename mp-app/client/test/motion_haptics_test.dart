/// M98 — دو لایهٔ UX-G3/Q5: `MpMotion` (کاهش حرکت) و `MpHaptics` (پالس لمسی).
///
/// چرا surface-channel: ادعای loop این است که پالس «واقعاً به پلتفرم می‌رود»، نه
/// اینکه یک تابع صدا زده می‌شود. پس mock روی `SystemChannels.platform` نشسته و
/// تعداد/نام فراخوانی‌ها خوانده می‌شود — بدون وابستگی به نام دقیق API در نسخه‌های
/// مختلف SDK (impactها در برخی نسخه‌ها `VibrationEffect.vibrate` می‌روند).
library;

import 'package:flutter/foundation.dart' show TargetPlatform, debugDefaultTargetPlatformOverride;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/haptics.dart';
import 'package:mp_client/core/motion.dart';

import 'haptics_recorder.dart';

Widget _withMotion({required bool disableAnimations, required Widget Function(BuildContext) builder}) {
  return MediaQuery(
    data: MediaQueryData(disableAnimations: disableAnimations),
    child: Builder(builder: builder),
  );
}

void main() {
  group('MpMotion — کاهش حرکت', () {
    testWidgets('disableAnimations=true → duration صفر و target صفر', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: _withMotion(
          disableAnimations: true,
          builder: (context) {
            expect(MpMotion.reduced(context), isTrue);
            expect(MpMotion.dur(context, const Duration(milliseconds: 250)), Duration.zero);
            expect(MpMotion.target(context), 0);
            return const SizedBox.shrink();
          },
        ),
      ));
    });

    testWidgets('بدون سیگنال → انیمیشن با همان duration قبلی می‌ماند', (tester) async {
      await tester.pumpWidget(MaterialApp(
        home: _withMotion(
          disableAnimations: false,
          builder: (context) {
            expect(MpMotion.reduced(context), isFalse);
            expect(MpMotion.dur(context, const Duration(milliseconds: 250)),
                const Duration(milliseconds: 250));
            expect(MpMotion.target(context), 1);
            return const SizedBox.shrink();
          },
        ),
      ));
    });

    testWidgets('هیچ MediaQuery‌ای نباشد → fallback امن (بی‌کاهش حرکت)', (tester) async {
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
    late List<MethodCall> platformCalls;

    setUp(() {
      platformCalls = <MethodCall>[];
      // `_platformFeedback` در `HapticFeedback` روی android/iOS/fuchsia کار می‌کند و
      // روی linux/macOS/windows no-op است؛ runner لیناکسی CI بدون این override هیچ
      // فراخوانی‌ای نمی‌دید و تست «پالس رفت» عمداً سبزِ توخالی می‌شد.
      debugDefaultTargetPlatformOverride = TargetPlatform.android;
    });
    tearDown(() => debugDefaultTargetPlatformOverride = null);

    Future<void> bind(WidgetTester tester) async {
      final messenger = tester.binding.defaultBinaryMessenger;
      messenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        platformCalls.add(call);
        return null;
      });
      // بدون پارامتر نوع: `setMockMethodCallHandler` در SDK این نسخه ژنریک نیست
      // و `…<void>` در CI خطای کامپایل می‌داد (WRONG_NUMBER_OF_TYPE_ARGUMENTS).
      addTearDown(() => messenger.setMockMethodCallHandler(SystemChannels.platform, null));
    }

    // تخلیهٔ صف رویداد بدون `pumpEventQueue()`: آن تابع زیر FakeAsyncِ testWidgets
    // روی `Future.delayed` واقعی منتظر می‌ماند و زمان فقط با pump جلو می‌رود — یعنی
    // بن‌بست تا timeout ده‌دقیقه‌ای (همین، `flutter test` را در run 44295370497
    // بی‌حرکت کرد). `runAsync` یک دور event loop واقعی به messenger می‌دهد.
    Future<void> drain(WidgetTester tester) async {
      await tester.runAsync(() => Future<void>.delayed(Duration.zero));
      await tester.pump();
    }

    testWidgets('هر سه پالس یک فراخوانی پلتفرم می‌فرستد', (tester) async {
      await bind(tester);
      const haptics = SystemMpHaptics();
      haptics.select();
      haptics.success();
      haptics.warning();
      await drain(tester);

      expect(platformCalls, hasLength(3));
      expect(
        platformCalls.map((c) => c.method),
        everyElement(anyOf(contains('HapticFeedback'), contains('Vibration'))),
      );
      // پالس‌ها باید از هم distinguishable باشند (select ≠ impact)
      expect(
        platformCalls.map((c) => c.arguments).toSet().length,
        greaterThan(1),
        reason: 'اگر هر سه یک arg داشتند، «موفق/ناموفق/انتخاب» یکی می‌شد',
      );
    });

    testWidgets('enabled=false → هیچ فراخوانی پلتفرم نه', (tester) async {
      await bind(tester);
      const haptics = SystemMpHaptics(enabled: false);
      haptics.select();
      haptics.success();
      haptics.warning();
      await drain(tester);
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
