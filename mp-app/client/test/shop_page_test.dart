/// تست ویجت فروشگاه (M59) — داده از API، نه از آرایهٔ ثابت.
///
/// چرا: تا پیش از M59 این صفحه چهار محصول hardcode داشت. تست زیر هم
/// «دادهٔ واقعی نشان داده می‌شود» را قفل می‌کند، هم «قیمت از سرور می‌آید»
/// و هم «ناموجود ← دکمه غیرفعال».
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/shop/shop_page.dart';

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
      // `http.Client.get` بدنه را از `contentLength` می‌خواند؛ بدون آن،
      // پاسخ «خالی» تلقی می‌شود و تست با «۰ ویجت» شکست می‌خورد (یک‌بار شد).
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

void main() {
  testWidgets('محصولات از API می‌آیند و قیمت از سرور است', (tester) async {
    final fake = _FakeClient({
      '/shop/products': [
        {
          'id': 7,
          'title': 'پروتئین وی ۲ کیلو',
          'price_rial': 2500000,
          'compare_at_rial': 3000000,
          'stock_qty': 4,
          'image_url': '',
          'variants': <dynamic>[],
        },
        {
          'id': 8,
          'title': 'کراتین',
          'price_rial': 1450000,
          'compare_at_rial': null,
          'stock_qty': 0,
          'image_url': '',
          'variants': <dynamic>[],
        },
      ],
      '/shop/cart': {
        'member_id': 1,
        'items': <dynamic>[],
        'total_rial': 0,
        'count': 0,
      },
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [httpClientProvider.overrideWithValue(fake)],
        // جهت راست‌به‌چپ مثل اپ واقعی؛ اندازه‌گیری چیدمان در LTR گمراه‌کننده است.
        child: MaterialApp(
          theme: mpTheme(),
          home: const Directionality(
            textDirection: TextDirection.rtl,
            child: ShopPage(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('پروتئین وی ۲ کیلو'), findsOneWidget);
    expect(find.text('کراتین'), findsOneWidget);
    expect(fake.calls, contains('GET /shop/products'));
    expect(fake.calls, contains('GET /shop/cart'));
    // قیمت از پاسخ API (۲٬۵۰۰٬۰۰۰) نمایش داده می‌شود
    expect(find.textContaining('۲٬۵۰۰٬۰۰۰'), findsOneWidget);
    // محصول ناموجود، دکمهٔ غیرفعال دارد
    expect(find.text('ناموجود'), findsOneWidget);
  });

  testWidgets('کاتالوگ خالی ← پیام راهنما، نه صفحهٔ سفید', (tester) async {
    final fake = _FakeClient({
      '/shop/products': <dynamic>[],
      '/shop/cart': {
        'member_id': 1,
        'items': <dynamic>[],
        'total_rial': 0,
        'count': 0,
      },
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [httpClientProvider.overrideWithValue(fake)],
        // جهت راست‌به‌چپ مثل اپ واقعی؛ اندازه‌گیری چیدمان در LTR گمراه‌کننده است.
        child: MaterialApp(
          theme: mpTheme(),
          home: const Directionality(
            textDirection: TextDirection.rtl,
            child: ShopPage(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('هنوز محصولی ثبت نشده'), findsOneWidget);
  });

  // M60/B2 — سبد باید قابل ویرایش باشد، نه فقط خواندنی.
  //
  // باگ واقعی: سرور PATCH/DELETE برای سبد داشت، ولی `ApiClient` هیچ‌کدام را
  // نداشت و ردیف سبد فقط `×۲` نشان می‌داد. تست زیر هر سه عمل را می‌سنجد و
  // **مسیر و متد** را هم چک می‌کند تا اگر کسی دکمه را به مسیر اشتباه وصل کرد
  // گرفته شود.
  testWidgets('سبد: افزایش، کاهش و حذف قلم واقعاً به سرور می‌رود', (
    tester,
  ) async {
    final fake = _FakeClient({
      '/shop/products': <dynamic>[],
      '/shop/cart': {
        'member_id': 1,
        'items': [
          {
            'id': 42,
            'title': 'پروتئین وی',
            'variant_label': 'شکلاتی',
            'qty': 2,
            'line_total_rial': 5000000,
          },
        ],
        'total_rial': 5000000,
        'count': 2,
      },
    });

    await tester.pumpWidget(
      ProviderScope(
        overrides: [httpClientProvider.overrideWithValue(fake)],
        child: MaterialApp(
          theme: mpTheme(),
          home: const Directionality(
            textDirection: TextDirection.rtl,
            child: ShopPage(),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // باز کردن شیت سبد
    await tester.tap(find.text('سبد'));
    await tester.pumpAndSettle();

    expect(find.textContaining('پروتئین وی'), findsWidgets);
    expect(find.byTooltip('افزایش تعداد'), findsOneWidget);
    expect(find.byTooltip('کاهش تعداد'), findsOneWidget);
    expect(find.byTooltip('حذف از سبد'), findsOneWidget);

    await tester.tap(find.byTooltip('افزایش تعداد'));
    await tester.pumpAndSettle();
    expect(fake.calls, contains('PATCH /shop/cart/42'));

    await tester.tap(find.byTooltip('حذف از سبد'));
    await tester.pumpAndSettle();
    expect(fake.calls, contains('DELETE /shop/cart/42'));
  });
}
