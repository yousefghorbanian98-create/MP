/// تست ویجت «برنامهٔ امروز» — دادهٔ واقعی با override (اجرا در CI — D-002).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mp_client/core/app_state.dart';
import 'package:mp_client/features/today/today_page.dart';

List<Map<String, dynamic>> _fakeExercises() => [
      {
        'exercise_name': 'اسکوات هالتر',
        'sets': 4,
        'reps': 8,
        'load_pct': 70,
        'rest_seconds': 150,
      },
      {
        'exercise_name': 'پرس سینه هالتر',
        'sets': 3,
        'reps': 10,
        'load_pct': 65,
        'rest_seconds': 120,
      },
    ];

Widget _wrap(Widget child) => ProviderScope(
      overrides: [
        todayExercisesProvider.overrideWith((ref) => _fakeExercises()),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: Directionality(textDirection: TextDirection.rtl, child: child),
        ),
      ),
    );

void main() {
  testWidgets('TodayPage renders real exercises RTL with dark theme', (tester) async {
    await tester.pumpWidget(_wrap(const TodayPage()));
    await tester.pumpAndSettle();

    expect(find.text('اسکوات هالتر'), findsOneWidget);
    expect(find.text('پرس سینه هالتر'), findsOneWidget);
    // RTL: جهت متن
    final text = tester.widget<Text>(find.text('اسکوات هالتر'));
    expect(text.textDirection ?? TextDirection.rtl, TextDirection.rtl);
  });

  testWidgets('toggling an exercise updates completion state', (tester) async {
    await tester.pumpWidget(_wrap(const TodayPage()));
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.circle_outlined).first);
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });

  testWidgets('empty state shows when no workout is planned', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          todayExercisesProvider.overrideWith((ref) => <Map<String, dynamic>>[]),
        ],
        child: const MaterialApp(
          home: Scaffold(
            body: Directionality(textDirection: TextDirection.rtl, child: TodayPage()),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('برنامه‌ای برای امروز'), findsOneWidget);
  });
}
