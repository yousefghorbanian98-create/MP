/// M61 / D5 — بنر خانه نباید وعدهٔ تجاری‌ای بدهد که سرور آن را ندارد.
///
/// باگ اثبات‌شده: بنر ثابت «تولدت مبارک! ۲۰٪ تخفیف تمدید اشتراک» بود در حالی
/// که `grep -i coupon` در کل مخزن صفر نتیجه دارد و هیچ منطق تولدی هم نیست.
/// یعنی صفحهٔ اول اپ یک تخفیف ناموجود اعلام می‌کرد. این تست سه چیز را قفل می‌کند:
///   ۱) هیچ متنی از «تخفیف/تولدت مبارک» در بنر نمانده باشد
///   ۲) محتوای بنر از دادهٔ واقعی بیاید (وضعیت اشتراکی که به کاربر نشان می‌دهیم)
///   ۳) وقتی داده‌ای نیست، بنر ادعایی نمی‌کند
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
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

    expect(find.textContaining('تخفیف'), findsNothing,
        reason: 'کوپن وجود ندارد؛ اعلام تخفیف یعنی وعدهٔ دروغ');
    expect(find.textContaining('تولدت مبارک'), findsNothing);
  });

  testWidgets('بنر با اشتراک فعال، تاریخ واقعی انقضا را نشان می‌دهد', (tester) async {
    final client = _FakeClient({
      '/members/3/memberships': [
        {
          'id': 5,
          'member_id': 3,
          'status': 'active',
          'plan_name': 'پلن ماهانه آقایان',
          'expires_at': '2026-12-10T00:00:00',
          'days_remaining': 24,
        }
      ],
    });
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(client.calls.any((c) => c.contains('/members/3/memberships')), isTrue,
        reason: 'بنر باید از دادهٔ واقعی اشتراک بسازد، نه متن ثابت');
    expect(find.textContaining('روز باقی‌مانده'), findsOneWidget,
        reason: 'روزهای باقی‌مانده باید از سرور بیاید');
  });

  testWidgets('بدون اشتراک، بنر حالت صادقانه نشان می‌دهد', (tester) async {
    final client = _FakeClient({'/members/3/memberships': []});
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('اشتراک فعالی ندارید'), findsOneWidget);
  });
}
