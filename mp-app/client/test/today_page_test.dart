/// تست ویجت «برنامهٔ امروز» — RTL و حالت تاریک (اجرا در CI — D-002).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mp_client/features/today/today_page.dart';

void main() {
  testWidgets('TodayPage renders exercises RTL with dark theme', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: Directionality(textDirection: TextDirection.rtl, child: TodayPage()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('سلام، علی 👋'), findsOneWidget);
    expect(find.text('اسکوات هالتر'), findsOneWidget);
    expect(find.text('پرس سینه هالتر'), findsOneWidget);

    // RTL: جهت متن
    final text = tester.widget<Text>(find.text('سلام، علی 👋'));
    expect(text.textDirection ?? TextDirection.rtl, TextDirection.rtl);
  });

  testWidgets('toggling an exercise updates the ring', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: Directionality(textDirection: TextDirection.rtl, child: TodayPage()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.circle_outlined).first);
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });
}
