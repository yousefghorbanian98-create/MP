/// تست ویجت «توانایی‌های من» (M37) — اجرا در CI (D-002).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mp_client/features/assessment14/assessment14_page.dart';
import 'package:mp_client/features/assessment14/assessment14_providers.dart';

Map<String, dynamic> _fakeMatrix() => {
      'assessment_id': 1,
      'axes': [
        {
          'axis': 1,
          'name_fa': 'تحرک و انعطاف',
          'score': 62.0,
          'quality': 'range_estimate',
          'decision_state': 'covered',
          'decision_reason': 'دلیل تست',
        },
        {
          'axis': 7,
          'name_fa': 'پایداری مرکز',
          'score': 32.0,
          'quality': 'interpolated',
          'decision_state': 'direct',
          'decision_reason': 'دلیل تست',
        },
        {
          'axis': 12,
          'name_fa': 'بازیابی و مدیریت بار',
          'score': null,
          'quality': 'missing',
          'decision_state': 'unknown',
          'decision_reason': 'نامعلوم، نه صفر',
        },
      ],
    };

Widget _wrap(Widget child, {List<Override> overrides = const []}) => ProviderScope(
      overrides: overrides,
      child: MaterialApp(
        home: Scaffold(
          body: Directionality(textDirection: TextDirection.rtl, child: child),
        ),
      ),
    );

void main() {
  testWidgets('empty state shows prompt when no assessment exists', (tester) async {
    await tester.pumpWidget(_wrap(
      const Assessment14Page(),
      overrides: [axisMatrixProvider.overrideWith((ref) async => null)],
    ));
    await tester.pumpAndSettle();
    expect(find.text('هنوز ارزیابی ثبت نشده است — اولین آزمون خود را ثبت کنید'), findsOneWidget);
  });

  testWidgets('matrix renders axes with scores, dashes and decision chips', (tester) async {
    await tester.pumpWidget(_wrap(
      const Assessment14Page(),
      overrides: [
        axisMatrixProvider.overrideWith((ref) async => _fakeMatrix()),
      ],
    ));
    await tester.pumpAndSettle();

    expect(find.text('ماتریس ۱۴ توانایی'), findsOneWidget);
    expect(find.text('1 تحرک و انعطاف'), findsOneWidget);
    expect(find.text('7 پایداری مرکز'), findsOneWidget);
    // نمرهٔ نامعلوم = «—» نه صفر
    expect(find.text('—'), findsOneWidget);
    // چیپ‌های تصمیم
    expect(find.text('پوشش در تکلیف دیگر'), findsOneWidget);
    expect(find.text('تمرین مستقیم'), findsOneWidget);
    expect(find.text('نامعلوم'), findsOneWidget);
    // عدد درصد روی نوار
    expect(find.text('62'), findsOneWidget);
    expect(find.text('32'), findsOneWidget);
  });

  testWidgets('submitting a test posts data and confirms', (tester) async {
    List<Map<String, dynamic>>? captured;
    await tester.pumpWidget(_wrap(
      const Assessment14Page(),
      overrides: [
        axisMatrixProvider.overrideWith((ref) async => null),
        submitAxisTestsProvider.overrideWith((ref) {
          return (tests) async {
            captured = tests;
            return true;
          };
        }),
      ],
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('نشست و رسیدن (سانتی‌متر)').last);
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '30');
    await tester.tap(find.text('ثبت آزمون'));
    await tester.pumpAndSettle();

    expect(find.text('ثبت شد ✓'), findsOneWidget);
    expect(captured, isNotNull);
    expect(captured!.first['test_key'], 'sit_and_reach');
    expect(captured!.first['raw_value'], 30.0);
  });

  testWidgets('invalid submit shows validation message', (tester) async {
    await tester.pumpWidget(_wrap(
      const Assessment14Page(),
      overrides: [axisMatrixProvider.overrideWith((ref) async => null)],
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.text('ثبت آزمون'));
    await tester.pumpAndSettle();
    expect(find.text('آزمون و مقدار عددی را وارد کنید'), findsOneWidget);
  });
}
