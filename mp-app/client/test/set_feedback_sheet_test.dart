/// تست‌های فرم بازخورد ست + «چرا این تغییر؟» (M39-c1/c2).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_app/features/feedback/feedback_providers.dart';
import 'package:mp_app/features/feedback/set_feedback_sheet.dart';

void main() {
  Future<void> pumpSheet(WidgetTester tester, {List<Map<String, dynamic>>? captured}) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          submitSetFeedbackProvider.overrideWithValue((entries) async {
            captured?.addAll(entries);
            return {
              'suggestions': [
                {
                  'movement_id': 'pushup-l1',
                  'next_weight': 0,
                  'weight_action': 'keep_bodyweight',
                  'next_sets': 2,
                  'volume_action': 'deload',
                  'reason': 'درد عضلانی ۸/۱۰ ≥ ۷ ← کاهش یک ست جلسهٔ بعد (بازیابی)',
                  'rule_version': 'set-feedback-1.0',
                }
              ],
            };
          }),
        ],
        child: const MaterialApp(
          home: Scaffold(body: SetFeedbackSheet(movementName: 'شنای سوئدی سطح ۱')),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('renders feedback form with sliders and submit', (tester) async {
    await pumpSheet(tester);
    expect(find.textContaining('بازخورد ست — شنای سوئدی سطح ۱'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.byType(Slider), findsNWidgets(2));
    expect(find.widgetWithText(FilledButton, 'ثبت بازخورد'), findsOneWidget);
  });

  testWidgets('submit shows why-card with data-rule-decision chain', (tester) async {
    final captured = <Map<String, dynamic>>[];
    await pumpSheet(tester, captured: captured);
    await tester.enterText(find.byType(TextField), '12');
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pumpAndSettle();
    expect(find.textContaining('چرا این تغییر؟'), findsOneWidget);
    expect(find.textContaining('کاهش یک ست'), findsWidgets);
    expect(find.textContaining('set-feedback-1.0'), findsOneWidget);
    expect(captured, hasLength(1));
    expect(captured.first['reps_done'], 12);
  });

  testWidgets('empty reps sends nothing', (tester) async {
    final captured = <Map<String, dynamic>>[];
    await pumpSheet(tester, captured: captured);
    await tester.tap(find.widgetWithText(FilledButton, 'ثبت بازخورد'));
    await tester.pump(const Duration(milliseconds: 300));
    expect(captured, isEmpty);
    expect(find.textContaining('چرا این تغییر؟'), findsNothing);
  });
}
