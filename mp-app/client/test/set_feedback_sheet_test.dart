/// تست‌های فرم بازخورد ست + «چرا این تغییر؟» (M39-c1/c2).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/features/feedback/feedback_providers.dart';
import 'package:mp_client/core/haptics.dart';
import 'package:mp_client/features/feedback/set_feedback_sheet.dart';

import 'haptics_recorder.dart';

void main() {
  Future<void> pumpSheet(
    WidgetTester tester, {
    List<Map<String, dynamic>>? captured,
    RecordingHaptics? haptics,
  }) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          if (haptics != null) hapticsProvider.overrideWith((ref) => haptics),
          submitSetFeedbackProvider.overrideWithValue((entries) async {
            captured?.addAll(entries);
            return {
              'suggestions': [
                {
                  'movement_id': 'pushup-l1',
                  'next_weight': 0,
                  'weight_action': 'keep_bodyweight',
                  'next_sets': null, // M48-c1: deload عدد مطلق نمی‌دهد
                  'volume_action': 'deload',
                  'reason':
                      'درد عضلانی ۸/۱۰ ≥ ۷ ← کاهش یک ست جلسهٔ بعد (بازیابی)',
                  'rule_version': 'set-feedback-1.0',
                },
              ],
              'applied': {
                'weeks_updated': 2,
                'rows_changed': 4,
                'matched': [],
                'unmatched_movements': <String>[],
                'rule_version': 'feedback-apply-1.0',
              },
            };
          }),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: SetFeedbackSheet(movementName: 'شنای سوئدی سطح ۱'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('renders feedback form with sliders and submit', (tester) async {
    await pumpSheet(tester);
    expect(
      find.textContaining('بازخورد ست — شنای سوئدی سطح ۱'),
      findsOneWidget,
    );
    // M48-c1 — دو فیلد: وزنه + تکرار (پیش‌تر فقط تکرار بود و weight همیشه ۰ می‌رفت)
    expect(find.byType(TextField), findsNWidgets(2));
    expect(find.byType(Slider), findsNWidgets(2));
    expect(find.widgetWithText(FilledButton, 'ثبت بازخورد'), findsOneWidget);
  });

  testWidgets('submit shows why-card with data-rule-decision chain', (
    tester,
  ) async {
    final captured = <Map<String, dynamic>>[];
    final haptics = RecordingHaptics();
    await pumpSheet(tester, captured: captured, haptics: haptics);
    // فیلد دوم = تکرار (فیلد اول وزنه است)
    await tester.enterText(find.byType(TextField).at(1), '12');
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pumpAndSettle();
    expect(find.textContaining('چرا این تغییر؟'), findsOneWidget);
    expect(find.textContaining('کاهش یک ست'), findsWidgets);
    expect(find.textContaining('set-feedback-1.0'), findsOneWidget);
    expect(captured, hasLength(1));
    expect(captured.first['reps_done'], 12);
    // M98/UX-G3 — ثبت موفق باید لمسی هم حس شود (نه فقط متن روی صفحه)
    expect(haptics.count('success'), 1);
    expect(haptics.count('warning'), 0);
  });

  testWidgets('empty reps sends nothing', (tester) async {
    final captured = <Map<String, dynamic>>[];
    final haptics = RecordingHaptics();
    await pumpSheet(tester, captured: captured, haptics: haptics);
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(captured, isEmpty);
    expect(find.textContaining('چرا این تغییر؟'), findsNothing);
    // بدون ارسال، پالس هم نباید برود — وگرنه «ثبت شد» لمسی دروغ می‌شود
    expect(haptics.events, isEmpty);
  });

  testWidgets('M48-c1: shows that the suggestion was actually applied', (
    tester,
  ) async {
    await pumpSheet(tester);
    await tester.enterText(find.byType(TextField).at(1), '12');
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pumpAndSettle();
    expect(find.textContaining('اعمال شد'), findsOneWidget);
    expect(find.textContaining('2 هفته'), findsOneWidget);
  });

  testWidgets('M98/UX-G3: ارسال ناموفق پالس هشدار می‌دهد، نه پالس موفق', (
    tester,
  ) async {
    final haptics = RecordingHaptics();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          hapticsProvider.overrideWith((ref) => haptics),
          submitSetFeedbackProvider.overrideWithValue((entries) async {
            throw Exception('شبکه قطع است');
          }),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: SetFeedbackSheet(movementName: 'شنای سوئدی سطح ۱'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(1), '9');
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pumpAndSettle();

    expect(haptics.count('warning'), 1);
    expect(haptics.count('success'), 0);
    expect(find.textContaining('چرا این تغییر؟'), findsNothing);
  });

  testWidgets('M48-c1: sends the real weight, not hardcoded zero', (
    tester,
  ) async {
    final captured = <Map<String, dynamic>>[];
    await pumpSheet(tester, captured: captured);
    await tester.enterText(find.byType(TextField).at(0), '62.5');
    await tester.enterText(find.byType(TextField).at(1), '8');
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pumpAndSettle();
    expect(captured.first['weight'], 62.5);
  });
}
