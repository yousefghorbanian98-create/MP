/// M98 — دو لایهٔ UX-G3/Q5: `MpMotion` (کاهش حرکت) و `MpHaptics` (پالس لمسی).
///
/// چرا surface-channel: ادعای loop این است که پالس «واقعاً به پلتفرم می‌رود»، نه
/// اینکه یک تابع صدا زده می‌شود. پس mock روی `SystemChannels.platform` نشسته و
/// تعداد/نام فراخوانی‌ها خوانده می‌شود — بدون وابستگی به نام دقیق API در نسخه‌های
/// مختلف SDK (impactها در برخی نسخه‌ها `VibrationEffect.vibrate` می‌روند).
library;

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
    });

    Future<void> bind(WidgetTester tester) async {
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        (call) async {
          platformCalls.add(call);
          return null;
        },
      );
      addTearDown(() =>
          tester.binding.defaultBinaryMessenger.setMockMethodCallHandler<void>(
              SystemChannels.platform, null));
    }

    testWidgets('هر سه پالس یک فراخوانی پلتفرم می‌فرستد', (tester) async {
      await bind(tester);
      const haptics = SystemMpHaptics();
      await haptics.select();
      await haptics.success();
      await haptics.warning();
      await tester.pump();

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
      await haptics.select();
      await haptics.success();
      await haptics.warning();
      await tester.pump();
      expect(platformCalls, isEmpty);
    });

    test('رابط MpHaptics بدون پلتفرم هم قابل استفاده است (fake تست‌ها)', () async {
      final fake = RecordingHaptics();
      await fake.select();
      await fake.success();
      await fake.warning();
      expect(fake.events, ['select', 'success', 'warning']);
    });
  });
}
