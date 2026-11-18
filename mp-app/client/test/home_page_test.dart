/// تست ویجت خانهٔ گریدی (M19) — ۸ بخش + جست‌وجو + بنر + اعلان.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/home/home_page.dart';

class _HomeClient extends http.BaseClient {
  _HomeClient({this.unread = 0});

  final int unread;
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    final payload = switch (path) {
      '/members/3/memberships' => <dynamic>[],
      '/notifications/member/3' => [
          for (var id = 1; id <= unread; id++)
            {
              'id': id,
              'title': 'اعلان $id',
              'body': '',
              'read_at': null,
              'created_at': '2026-11-16T12:00:00Z',
            },
        ],
      _ => <String, dynamic>{},
    };
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Widget wrap({int unread = 0}) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(_HomeClient(unread: unread)),
        authProvider.overrideWith(
          (ref) => AuthController.test(
            AuthState(
                accessToken: 'test-token', memberId: 3, userName: 'عضو تست'),
          ),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: HomePage()),
        ),
      ),
    );

void main() {
  testWidgets('گرید بخش‌های خانه نمایش داده می‌شود', (tester) async {
    await tester.pumpWidget(wrap());
    await tester.pumpAndSettle();
    for (final label in [
      'برنامهٔ اختصاصی من',
      'پیکرسنجی',
      'تغذیه',
      'چک‌این',
      'کیف پول',
      'پیشرفت',
      'کلاس‌ها',
      'فروشگاه',
    ]) {
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

  testWidgets('نشان اعلان خانه unread count واقعی API را نمایش می‌دهد', (
    tester,
  ) async {
    await tester.pumpWidget(wrap(unread: 3));
    await tester.pumpAndSettle();
    expect(find.text('۳'), findsOneWidget);
    expect(find.byIcon(Icons.notifications_outlined), findsOneWidget);
  });
}
