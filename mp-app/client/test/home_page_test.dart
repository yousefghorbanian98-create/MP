/// تست ویجت خانهٔ گریدی (M19) — ۸ بخش + جست‌وجو + بنر.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/home/home_page.dart';

void main() {
  Widget wrap() => MaterialApp(theme: mpTheme(), home: const Scaffold(body: HomePage()));

  testWidgets('گرید ۸ بخش نمایش داده می‌شود', (tester) async {
    await tester.pumpWidget(wrap());
    await tester.pumpAndSettle();
    for (final label in ['برنامهٔ اختصاصی من', 'پیکرسنجی', 'تغذیه', 'چک‌این', 'کیف پول', 'پیشرفت', 'کلاس‌ها', 'فروشگاه']) {
      expect(find.text(label), findsOneWidget, reason: 'بخش $label باید باشد');
    }
  });

  testWidgets('جست‌وجو هست؛ بنر دیگر متن تخفیف ثابت ندارد', (tester) async {
    await tester.pumpWidget(wrap());
    await tester.pumpAndSettle();
    expect(find.byType(TextField), findsOneWidget);
    // M61/D5 — نسخهٔ قبلی این تست «تولدت مبارک! 🎂» را تأیید می‌کرد، یعنی
    // تستی که خودش باگ را قفل کرده بود. بنر اکنون از اشتراک واقعی ساخته
    // می‌شود؛ جزئیاتش در home_banner_test.dart سنجیده می‌شود.
    expect(find.text('تولدت مبارک! 🎂'), findsNothing);
  });

  testWidgets('چک‌این سریع در خانه', (tester) async {
    await tester.pumpWidget(wrap());
    await tester.pumpAndSettle();
    expect(find.text('چک‌این سریع'), findsOneWidget);
  });
}
