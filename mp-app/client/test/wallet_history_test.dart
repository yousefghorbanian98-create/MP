/// Regression coverage for the wallet ledger (M83) and payment history (G1).
/// The ledger must use persisted credit/debit rows and its server-computed balance,
/// validate member ownership, preserve newest-first order, and page via its cursor.
/// Payment status history remains a separate list; it cannot stand in for the ledger.
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
    calls.add(
      '${request.method} $path${request.url.hasQuery ? '?${request.url.query}' : ''}',
    );
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

class _PagedWalletClient extends http.BaseClient {
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    final query = request.url.queryParameters;
    calls.add('${request.method} $path${request.url.hasQuery ? '?${request.url.query}' : ''}');
    late final Object payload;
    if (path == '/payments') {
      payload = <dynamic>[];
    } else if (path == '/payments/wallet/1/transactions' && query['before_id'] == null) {
      payload = {
        'member_id': 1,
        'balance_rial': 70000,
        'transactions': [
          {
            'id': 3,
            'member_id': 1,
            'amount_rial': 50000,
            'kind': 'credit',
            'description': 'شارژ آخر',
            'created_at': '2026-11-15T10:00:00',
          },
          {
            'id': 2,
            'member_id': 1,
            'amount_rial': 20000,
            'kind': 'debit',
            'description': 'برداشت آخر',
            'created_at': '2026-11-14T10:00:00',
          },
        ],
        'next_before_id': 2,
      };
    } else if (path == '/payments/wallet/1/transactions' && query['before_id'] == '2') {
      payload = {
        'member_id': 1,
        'balance_rial': 70000,
        'transactions': [
          {
            'id': 1,
            'member_id': 1,
            'amount_rial': 40000,
            'kind': 'credit',
            'description': 'شارژ اولیه',
            'created_at': '2026-11-13T10:00:00',
          },
        ],
        'next_before_id': null,
      };
    } else {
      throw StateError('Unexpected wallet request: $path $query');
    }
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

/// authProvider با هویت عضو override می‌شود تا wallet/balance/ledger واقعی سنجیده شوند.
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
      '/payments/wallet/1/transactions': {
        'member_id': 1,
        'balance_rial': 85000,
        'transactions': [
          {
            'id': 12,
            'member_id': 1,
            'amount_rial': 125000,
            'kind': 'credit',
            'description': 'شارژ از پذیرش',
            'created_at': '2026-11-15T10:00:00',
          },
          {
            'id': 11,
            'member_id': 1,
            'amount_rial': 40000,
            'kind': 'debit',
            'description': 'خرید مکمل',
            'created_at': '2026-11-14T10:00:00',
          },
        ],
        'next_before_id': null,
      },
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
    expect(fake.calls, contains('GET /payments/wallet/1/transactions?limit=20'));
    expect(fake.calls, isNot(contains('GET /payments/wallet/1')));
    expect(find.text('دفتر گردش کیف پول'), findsOneWidget);
    expect(find.text('85,000 ریال'), findsOneWidget);
    expect(find.text('شارژ از پذیرش'), findsOneWidget);
    expect(find.text('خرید مکمل'), findsOneWidget);
    expect(find.textContaining('+125,000 ریال'), findsOneWidget);
    expect(find.textContaining('−40,000 ریال'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('سفارش پروتئین وی'), 250);
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
      '/payments/wallet/1/transactions': {
        'member_id': 1,
        'balance_rial': 0,
        'transactions': <dynamic>[],
        'next_before_id': null,
      },
      '/payments': <dynamic>[],
    });

    await tester.pumpWidget(_wrap(fake));
    await tester.pumpAndSettle();

    expect(find.text('هنوز پرداختی ثبت نشده است.'), findsOneWidget);
    expect(find.text('هنوز تراکنشی در کیف‌پول ثبت نشده است.'), findsOneWidget);
  });

  testWidgets('دفتر بزرگ‌تر با نشانگر قبل از شناسه صفحه‌بندی می‌شود', (tester) async {
    final client = _PagedWalletClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('شارژ آخر'), findsOneWidget);
    expect(find.text('برداشت آخر'), findsOneWidget);
    expect(find.text('تراکنش‌های قدیمی‌تر'), findsOneWidget);
    await tester.tap(find.text('تراکنش‌های قدیمی‌تر'));
    await tester.pumpAndSettle();

    expect(find.text('شارژ اولیه'), findsOneWidget);
    expect(client.calls.where((call) => call.contains('/transactions')).length, 2);
    expect(client.calls.last, contains('before_id=2'));
    expect(find.text('تراکنش‌های قدیمی‌تر'), findsNothing);
  });

  testWidgets('دفتر ناسازگار با عضو نشست را نشان نمی‌دهد', (tester) async {
    final fake = _FakeClient({
      '/payments/wallet/1/transactions': {
        'member_id': 2,
        'balance_rial': 100000,
        'transactions': [
          {
            'id': 8,
            'member_id': 2,
            'amount_rial': 100000,
            'kind': 'credit',
            'description': 'دادهٔ خصوصی عضو دیگر',
            'created_at': '2026-11-15T10:00:00',
          },
        ],
        'next_before_id': null,
      },
      '/payments': <dynamic>[],
    });

    await tester.pumpWidget(_wrap(fake));
    await tester.pumpAndSettle();

    expect(find.text('دادهٔ خصوصی عضو دیگر'), findsNothing);
    expect(find.textContaining('دفتر کیف‌پول متعلق به عضو نشست نیست'), findsOneWidget);
  });
}
