/// M61/D5 + M72 — بنر خانه فقط وضعیت/تاریخ واقعی اشتراک را نمایش می‌دهد.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/membership.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/home/home_page.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient(this.routes);

  final Map<String, dynamic> routes;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    final payload = routes[path];
    final bytes = utf8.encode(jsonEncode(payload ?? {}));
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Widget _wrap(http.Client client) => ProviderScope(
  overrides: [
    httpClientProvider.overrideWithValue(client),
    authProvider.overrideWith(
      (ref) => AuthController.test(
        AuthState(accessToken: 't', memberId: 3, userName: 'عضو تست'),
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
  testWidgets('بنر هیچ تخفیف/تولدی ادعا نمی‌کند', (tester) async {
    final client = _FakeClient({
      '/members/3/memberships': [],
      '/members/me': {'id': 3, 'full_name': 'عضو تست'},
    });
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('تخفیف'),
      findsNothing,
      reason: 'کوپن وجود ندارد؛ اعلام تخفیف یعنی وعدهٔ دروغ',
    );
    expect(find.textContaining('تولدت مبارک'), findsNothing);
  });

  testWidgets('اشتراک فعال تاریخ پایان و روزهای باقی‌مانده را از API می‌گیرد', (
    tester,
  ) async {
    final expiresAt = DateTime.now()
        .toUtc()
        .add(const Duration(days: 24))
        .toIso8601String();
    final client = _FakeClient({
      '/members/3/memberships': [
        {
          'id': 5,
          'member_id': 3,
          'status': 'active',
          'plan_name': 'پلن ماهانهٔ آقایان',
          'expires_at': expiresAt,
        },
      ],
    });
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(
      client.calls.any((c) => c == 'GET /members/3/memberships'),
      isTrue,
      reason: 'بنر باید از endpoint مالک‌محور اشتراک عضو استفاده کند',
    );
    expect(find.text('اشتراک فعال'), findsOneWidget);
    expect(
      find.textContaining(
        'تاریخ پایان: ${formatJalaliDate(DateTime.parse(expiresAt).toLocal())}',
      ),
      findsOneWidget,
    );
    expect(find.textContaining('روز باقی‌مانده'), findsOneWidget);
  });

  testWidgets(
    'اشتراک منقضی از اشتراک نداشته تفکیک می‌شود و پایان را نشان می‌دهد',
    (tester) async {
      final expiresAt = DateTime.now()
          .toUtc()
          .subtract(const Duration(days: 1))
          .toIso8601String();
      final client = _FakeClient({
        '/members/3/memberships': [
          {
            'id': 6,
            'member_id': 3,
            'status': 'expired',
            'plan_name': 'پلن قبلی',
            'expires_at': expiresAt,
          },
        ],
      });
      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(find.text('اشتراک منقضی شده'), findsOneWidget);
      expect(
        find.textContaining(
          'تاریخ پایان: ${formatJalaliDate(DateTime.parse(expiresAt).toLocal())}',
        ),
        findsOneWidget,
      );
      expect(find.text('اشتراک فعالی ندارید'), findsNothing);
    },
  );

  testWidgets('بدون اشتراک، بنر حالت صادقانه نشان می‌دهد', (tester) async {
    final client = _FakeClient({'/members/3/memberships': []});
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('اشتراک فعالی ندارید'), findsOneWidget);
    expect(find.textContaining('تاریخ پایان'), findsNothing);
    expect(find.textContaining('روز باقی‌مانده'), findsNothing);
  });

  testWidgets('پاسخ نامعتبر API به‌جای ادعای نبود اشتراک، بنر را مخفی می‌کند', (
    tester,
  ) async {
    final client = _FakeClient({
      '/members/3/memberships': {'items': []},
    });
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('اشتراک فعالی ندارید'), findsNothing);
    expect(find.textContaining('وضعیت اشتراک نامعلوم'), findsNothing);
  });
}
