/// تست ویجت خانهٔ گریدی (M19) — ۸ بخش + جست‌وجو + بنر.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/home/home_page.dart';

void main() {
  Widget wrap() => MaterialApp(theme: mpTheme(), home: const Scaffold(body: HomePage()));

  testWidgets('گرید ۸ بخش نمایش داده می‌شود', (tester) async {
    await tester.pumpWidget(wrap());
    for (final label in ['برنامهٔ اختصاصی من', 'پیکرسنجی', 'تغذیه', 'چک‌این', 'کیف پول', 'پیشرفت', 'کلاس‌ها', 'فروشگاه']) {
      expect(find.text(label), findsOneWidget, reason: 'بخش $label باید باشد');
    }
  });

  testWidgets('جست‌وجو و بنر موجودند', (tester) async {
    await tester.pumpWidget(wrap());
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('تولدت مبارک! 🎂'), findsOneWidget);
  });

  testWidgets('چک‌این سریع در خانه', (tester) async {
    await tester.pumpWidget(wrap());
    expect(find.text('چک‌این سریع'), findsOneWidget);
  });
}
