/// M90 — «سفارش‌های من» و رسید عضو: خواندن از endpoint مالک‌محور، بدون نشت دادهٔ
/// عضو دیگر و بدون فرستادن هیچ مبلغی به سرور.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/persian_format.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/shop/order_receipt_sheet.dart';
import 'package:mp_client/features/shop/shop_page.dart';

Map<String, dynamic> _orderJson({
  int id = 12,
  String status = 'paid',
  int total = 5000000,
}) =>
    {
      'id': id,
      'member_id': 3,
      'status': status,
      'total_rial': total,
      'payment_id': 88,
      'note': 'تحویل شنبه',
      'created_at': '2026-11-10T08:30:00+00:00',
      'items': [
        {'product_id': 7, 'title': 'پروتئین وی', 'unit_price_rial': 2500000, 'qty': 2},
      ],
    };

Map<String, dynamic> _receiptJson({
  int orderId = 12,
  int member = 3,
  int itemsTotal = 5000000,
  int total = 5000000,
  List<Map<String, dynamic>>? lines,
}) =>
    {
      'receipt_no': 'O-000012',
      'order_id': orderId,
      'member_id': member,
      'member_name': 'سارا تستی',
      'status': 'paid',
      'note': 'تحویل شنبه',
      'created_at': '2026-11-10T08:30:00+00:00',
      'issued_at': '2026-11-11T10:00:00+00:00',
      'lines': lines ??
          [
            {
              'product_id': 7,
              'title': 'پروتئین وی',
              'variant': 'شکلاتی',
              'unit_price_rial': 2500000,
              'qty': 2,
              'line_total_rial': 5000000,
            }
          ],
      'items_total_rial': itemsTotal,
      'total_rial': total,
      'payment': {
        'id': 88,
        'method': 'wallet',
        'status': 'paid',
        'reference_id': 'WP-777',
        'paid_at': '2026-11-10T08:31:00+00:00',
      },
      'branch': 'Muscle Paradise',
    };

/// فیک HTTP که هم پاسخ و هم کد وضعیت مسیر رسید را کنترل می‌کند.
class _ShopFakeClient extends http.BaseClient {
  _ShopFakeClient({
    Map<String, Object>? responses,
    List<Map<String, dynamic>>? orders,
    this.receiptStatus = 200,
  })  : responses = responses ?? const {},
        orders = orders ?? const [];

  final Map<String, Object> responses;
  final List<Map<String, dynamic>> orders;
  final int receiptStatus;

  final List<String> calls = [];

  int get receiptCalls => calls.where((c) => c.contains('/receipt')).length;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');

    dynamic payload;
    var status = 200;
    if (request.method == 'GET' && path == '/shop/orders') {
      payload = orders;
    } else if (request.method == 'GET' &&
        RegExp(r'^/shop/orders/\d+/receipt$').hasMatch(path)) {
      payload = responses[path] ?? <String, dynamic>{'detail': 'not found'};
      status = receiptStatus;
    } else {
      payload = responses[path] ?? <String, dynamic>{};
    }

    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      status,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

/// شیت را با نشستِ عضو (memberId=3) و همان کلاینت فیک باز می‌کند.
Future<_ShopFakeClient> _openOrdersSheet(
  WidgetTester tester,
  _ShopFakeClient client,
) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [
      httpClientProvider.overrideWithValue(client),
      authProvider.overrideWith(
        (ref) => AuthController.test(
          AuthState(accessToken: 'test-token', memberId: 3, userName: 'سارا تستی'),
        ),
      ),
    ],
    child: MaterialApp(
      theme: mpTheme(),
      home: const Directionality(
        textDirection: TextDirection.rtl,
        child: ShopPage(),
      ),
    ),
  ));
  await tester.pumpAndSettle();
  await tester.tap(find.text('سفارش‌ها'));
  await tester.pumpAndSettle();
  return client;
}

void main() {
  test('قالب ارقام از core — همان قراردادی که رسید استفاده می‌کند', () {
    expect(rial(2500000), '۲٬۵۰۰٬۰۰۰ ریال');
    expect(rial(2500000, unit: ''), '۲٬۵۰۰٬۰۰۰');
    expect(faDigits(12), '۱۲');
  });

  test('orderStatusLabel — وضعیت خام به کاربر نمی‌چسبد، ناشناخته هم جعل نمی‌شود', () {
    expect(orderStatusLabel('paid'), 'پرداخت‌شده');
    expect(orderStatusLabel('delivered'), 'تحویل‌شده');
    expect(orderStatusLabel('cancelled'), 'لغوشده');
    expect(orderStatusLabel(null), 'نامشخص');
    // وضعیت تازه‌ای که هنوز در اپ شناخته نشده نباید «تأییدشده» خوانده شود
    expect(orderStatusLabel('left_locker'), 'left_locker');
  });

  testWidgets('سفارش‌ها از API می‌آیند و رسید فقط با GET از endpoint مالک‌محور خوانده می‌شود',
      (tester) async {
    final client = await _openOrdersSheet(
      tester,
      _ShopFakeClient(
        orders: [_orderJson()],
        responses: {'/shop/orders/12/receipt': _receiptJson()},
      ),
    );

    // فهرست سفارش
    expect(find.text('سفارش #۱۲'), findsOneWidget);
    expect(find.textContaining('پرداخت‌شده'), findsWidgets);
    expect(find.textContaining('۲ قلم'), findsOneWidget);

    await tester.tap(find.text('رسید'));
    await tester.pumpAndSettle();

    expect(client.calls, contains('GET /shop/orders'));
    expect(client.calls, contains('GET /shop/orders/12/receipt'));
    // رسید هیچ چیز می‌نویسد نه مبلغ می‌فرستد: فقط GET روی این دو مسیر
    expect(
      client.calls.where((c) => c.startsWith('POST') || c.startsWith('PATCH')),
      isEmpty,
      reason: 'رسید باید خواندنی باشد؛ مبلغ/وضعیت را سرور تعیین می‌کند',
    );

    // محتوای رسید از پاسخ سرور
    expect(find.text('O-000012'), findsOneWidget);
    expect(find.textContaining('پروتئین وی — شکلاتی'), findsOneWidget);
    // هر قلم = واحد قیمت × تعداد + مبلغ قلم؛ هیچ‌کدام در کلاینت جمع نمی‌شوند.
    expect(find.textContaining('۲٬۵۰۰٬۰۰۰ ریال × ۲'), findsOneWidget);
    expect(find.textContaining('سارا تستی'), findsWidgets);
    expect(find.textContaining('WP-777'), findsOneWidget);
    expect(find.text('قابل پرداخت'), findsOneWidget);
    // ارقام فارسی: هیچ رقم لاتینی در مبلغ‌های رسید نباید باشد
    expect(find.textContaining('5000000'), findsNothing);
  });

  testWidgets('پاسخ عضو دیگر نمایش داده نمی‌شود (fail closed)', (tester) async {
    await _openOrdersSheet(
      tester,
      _ShopFakeClient(
        orders: [_orderJson()],
        responses: {'/shop/orders/12/receipt': _receiptJson(member: 999)},
      ),
    );
    await tester.tap(find.text('رسید'));
    await tester.pumpAndSettle();

    expect(find.textContaining('رسید متعلق به عضو این نشست نیست'), findsOneWidget);
    expect(find.text('O-000012'), findsNothing);
    // عنوان قلم فقط در بدنهٔ رسید هست؛ نبودنش یعنی پاسخ عضو دیگر رندر نشده
    expect(find.textContaining('پروتئین وی'), findsNothing);
  });

  testWidgets('رسید سفارش دیگر (order_id نامطابق) رد می‌شود', (tester) async {
    await _openOrdersSheet(
      tester,
      _ShopFakeClient(
        orders: [_orderJson()],
        responses: {'/shop/orders/12/receipt': _receiptJson(orderId: 13)},
      ),
    );
    await tester.tap(find.text('رسید'));
    await tester.pumpAndSettle();

    expect(find.textContaining('رسید به سفارش دیگری تعلق دارد'), findsOneWidget);
    expect(find.textContaining('پروتئین وی'), findsNothing);
  });

  testWidgets('جمع اقلام و مبلغ کل هر دو نمایش داده می‌شوند اگر سرور یکسان نبود', (tester) async {
    // اعداد عمداً متفاوت‌اند تا هر مبلغ دقیقاً یک‌بار در صفحه بیاید و
    // `findsOneWidget` واقعی باشد (مبلغ فهرست سفارش‌ها پشت شیت هم همین‌طور).
    await _openOrdersSheet(
      tester,
      _ShopFakeClient(
        orders: [_orderJson(total: 7000000)],
        responses: {
          '/shop/orders/12/receipt': _receiptJson(
            itemsTotal: 4000000,
            total: 5000000,
            lines: [
              {
                'product_id': 7,
                'title': 'پروتئین وی',
                'variant': 'شکلاتی',
                'unit_price_rial': 1111111,
                'qty': 1,
                'line_total_rial': 2222222,
              }
            ],
          ),
        },
      ),
    );
    await tester.tap(find.text('رسید'));
    await tester.pumpAndSettle();

    // `find.text('جمع اقلام')` نه textContaining: جملهٔ اختلاف هم همین عبارت را در
    // متن دارد و finder را دوساز می‌کرد (اولین run CI همین را گرفت).
    expect(find.text('جمع اقلام'), findsOneWidget);
    expect(find.text('قابل پرداخت'), findsOneWidget);
    expect(find.textContaining('۴٬۰۰۰٬۰۰۰ ریال'), findsOneWidget);
    expect(find.textContaining('۵٬۰۰۰٬۰۰۰ ریال'), findsOneWidget);
    // قلم هم همان‌طور که سرور فرستاده نمایش داده می‌شود، حتی اگر
    // line_total_rial با unit_price × qty نخواند: کلاینت هیچ عددی را نمی‌سازد.
    expect(find.textContaining('۱٬۱۱۱٬۱۱۱ ریال × ۱'), findsOneWidget);
    expect(find.textContaining('۲٬۲۲۲٬۲۲۲ ریال'), findsOneWidget);
    expect(
      find.textContaining('با جمع اقلام یکسان نیست'),
      findsOneWidget,
      reason: 'اختلاف باید در همان نگاه پیدا باشد، نه اینکه عددی در کلاینت تصحیح شود',
    );
    // هیچ جمع‌سازی/تصحیحی در کلاینت نمی‌شود: ۱٬۱۱۱٬۱۱۱×۱ که سرور ۲٬۲۲۲٬۲۲۲ زده
    // نباید به ۱٬۱۱۱٬۱۱۱ تغییر کند.
    expect(find.textContaining('۱٬۱۱۱٬۱۱۱ ریال'), findsOneWidget);
  });

  testWidgets('خطای سرور روی رسید → تلاش دوباره همان مسیر را می‌خواند', (tester) async {
    final client = _ShopFakeClient(
      orders: [_orderJson()],
      responses: {'/shop/orders/12/receipt': <String, dynamic>{'detail': 'موقتاً در دسترس نیست'}},
      receiptStatus: 503,
    );
    await _openOrdersSheet(tester, client);
    await tester.tap(find.text('رسید'));
    await tester.pumpAndSettle();

    expect(client.receiptCalls, 1);
    expect(find.text('تلاش دوباره'), findsOneWidget);
    expect(find.text('O-000012'), findsNothing);

    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();
    expect(client.receiptCalls, 2);
  });

  testWidgets('فهرست خالی پیام راهنما می‌دهد، نه صفحهٔ سفید', (tester) async {
    await _openOrdersSheet(tester, _ShopFakeClient(orders: const []));
    expect(find.textContaining('هنوز سفارشی ثبت نشده است'), findsOneWidget);
  });
}
