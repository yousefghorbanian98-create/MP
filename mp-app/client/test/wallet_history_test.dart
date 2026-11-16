/// تست تاریخچهٔ پرداخت در صفحهٔ کیف پول (G1 از ممیزی رقابتی).
///
/// چرا: پرسش روزمرهٔ عضو «پول من کجا رفت؟» بود و اپ هیچ پاسخی نداشت، در حالی
/// که `GET /payments` از قبل وجود داشت. تست زیر سه چیز را قفل می‌کند:
///   ۱) فهرست از API می‌آید (نه آرایهٔ ثابت)
///   ۲) مبلغ و وضعیت هر ردیف از پاسخ سرور خوانده می‌شود
///   ۳) فهرست خالی ← پیام روشن، نه صفحهٔ سفید
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/wallet/wallet_page.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient(this.routes);

  final Map<String, dynamic> routes;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    final payload = routes[path] ?? <String, dynamic>{};
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

/// بدون memberId، `walletProvider` اصلاً API را صدا نمی‌زند و موجودی ۰
/// نمایش می‌دهد؛ پس authProvider هم override می‌شود تا مسیر واقعی سنجیده شود.
Widget _wrap(http.Client client) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) => AuthController.test(AuthState(accessToken: 't', memberId: 1)),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: WalletPage()),
        ),
      ),
    );

void main() {
  testWidgets('تاریخچهٔ پرداخت از API می‌آید و مبلغ/وضعیت را نشان می‌دهد', (tester) async {
    final fake = _FakeClient({
      '/payments/wallet/1': {'balance_rial': 450000},
      '/payments': [
        {
          'id': 9,
          'member_id': 1,
          'amount_rial': 2900000,
          'method': 'wallet',
          'status': 'paid',
          'reference_id': 'ref-1',
          'description': 'سفارش پروتئین وی',
          'paid_at': '2026-11-15T10:00:00',
        },
        {
          'id': 8,
          'member_id': 1,
          'amount_rial': 4000000,
          'method': 'gateway',
          'status': 'failed',
          'reference_id': '',
          'description': 'تمدید عضویت',
          'paid_at': null,
        },
      ],
    });

    await tester.pumpWidget(_wrap(fake));
    await tester.pumpAndSettle();

    expect(fake.calls, contains('GET /payments'));
    expect(find.text('تاریخچهٔ پرداخت'), findsOneWidget);
    expect(find.text('سفارش پروتئین وی'), findsOneWidget);
    // مبلغ از سرور — با جداکنندهٔ هزارگان
    expect(find.textContaining('2,900,000'), findsOneWidget);
    // وضعیت‌ها به فارسی، نه کد خام
    expect(find.textContaining('پرداخت‌شده'), findsOneWidget);
    expect(find.textContaining('ناموفق'), findsOneWidget);
    // کد خام status نباید به کاربر نشان داده شود
    expect(find.textContaining('paid ·'), findsNothing);
  });

  testWidgets('بدون پرداخت ← پیام روشن، نه فهرست خالی', (tester) async {
    final fake = _FakeClient({
      '/payments/wallet/1': {'balance_rial': 0},
      '/payments': <dynamic>[],
    });

    await tester.pumpWidget(_wrap(fake));
    await tester.pumpAndSettle();

    expect(find.text('هنوز پرداختی ثبت نشده است.'), findsOneWidget);
  });
}
