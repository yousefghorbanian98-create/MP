/// M62 / D4 — صفحهٔ «پیکرسنجی» کلاینت ۱۰۰٪ دادهٔ ساختگی بود.
///
/// اثبات باگ: `bodycomp_page.dart` هیچ provider/API نداشت (`api_or_provider=0`).
/// «۱۲٫۴٪»، «۷۸٫۵ کیلو»، «۳۴٫۱ کیلو»، نمودار روند ۶ ماهه و چهار ردیف «سوابق
/// اندازه‌گیری» همه literal بودند. عضو اعدادی را می‌دید که **مال خودش نبود**
/// و هیچ‌جا هم «نمونه» برچسب نداشتند.
///
/// تست سه چیز را قفل می‌کند:
///   ۱) داده از `GET /assessments/jp7/member/{id}/trend` می‌آید (مسیر واقعی)
///   ۲) حالت «کمتر از دو اندازه‌گیری» صادقانه گفته می‌شود، نه نمودار جعلی
///   ۳) هیچ عدد فارسیِ هاردکدشده‌ای در فایل نمانده
library;

import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/bodycomp/bodycomp_page.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient(this.payload);

  final Map<String, dynamic> payload;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    calls.add(
      '${request.method} ${request.url.path.replaceFirst('/api/v1', '')}',
    );
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Widget _wrap(http.Client client) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) =>
              AuthController.test(AuthState(accessToken: 't', memberId: 3)),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: BodyCompPage(),
        ),
      ),
    );

void main() {
  test('هیچ مقدار اندازه‌گیریِ هاردکدشده‌ای در صفحه نمانده', () {
    final src =
        File('lib/features/bodycomp/bodycomp_page.dart').readAsStringSync();
    // آنچه ممنوع است «عدد اندازه‌گیری» است، نه هر رقم فارسی: ارقام فارسی
    // برای **تاریخ** و **برچسب** مجازند (تبدیل نمایشی‌اند). پس الگو را
    // دقیق می‌کنیم: عددی که با ٪ / کیلو / میلی‌متر / «کیلوگرم» آمده باشد.
    final measurement = RegExp(
      r"'[^']*[۰-۹][^']*(٪|کیلو|میلی‌متر|کیلوگرم)[^']*'",
    );
    final offending = measurement
        .allMatches(src)
        .map((m) => m.group(0))
        .where((s) => s != null && !s.contains(r'$'))
        .toList();
    expect(
      offending,
      isEmpty,
      reason:
          'هر عدد اندازه‌گیری باید از API بیاید (اسکالرهای interpolation مجازند): '
          '$offending',
    );
  });

  test('اعداد ساختگی قدیمی (۱۲٫۴ / ۷۸٫۵ / ۳۴٫۱) رفته‌اند', () {
    final src =
        File('lib/features/bodycomp/bodycomp_page.dart').readAsStringSync();
    for (final fake in ['۱۲٫۴', '۷۸٫۵', '۳۴٫۱', '۱۵٫۰', '۱۳٫۶']) {
      expect(
        src.contains(fake),
        isFalse,
        reason: 'عدد ساختگی $fake نباید برگردد',
      );
    }
  });

  testWidgets(
    'با یک اندازه‌گیری، پیام «حداقل دو اندازه‌گیری» نشان داده می‌شود',
    (tester) async {
      final client = _FakeClient({
        'member_id': 3,
        'measurements': [
          {
            'id': 1,
            'measured_at': '2026-11-01T00:00:00',
            'sum_mm': 88.0,
            'sites': {},
            'body_fat_pct': null,
          },
        ],
        'trend': null,
        'interpretation': {
          'status': 'insufficient',
          'headline': 'برای تفسیر روند حداقل دو اندازه‌گیری لازم است',
          'detail': 'فقط ۱ اندازه‌گیری ثبت شده. یک نقطه، روند نیست.',
          'confidence': 'insufficient',
        },
        'data_state': 'insufficient_measurements',
        'body_fat_note': 'درصد چربی محاسبه نشده و نمایش داده نمی‌شود',
        'rule_version': 'jp7-trend-1.0',
      });

      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(
        client.calls.any((c) => c.contains('/assessments/jp7/member/3/trend')),
        isTrue,
        reason: 'داده باید از مسیر واقعی روند JP7 بیاید',
      );
      expect(find.textContaining('حداقل دو اندازه‌گیری'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('jp7-trend-chart')),
        findsNothing,
        reason: 'با یک نقطه نباید خط روند ساخته شود',
      );
      expect(
        find.text('۲۰۲۶/۱۱/۰۱'),
        findsOneWidget,
        reason: 'تاریخ واقعی باید بدون خطای تبدیل رقم نمایش داده شود',
      );
      expect(
        find.textContaining('۱۲٫۴'),
        findsNothing,
        reason: 'عدد ساختگی قبلی نباید برگردد',
      );
    },
  );

  testWidgets(
    'با دو اندازه‌گیری، مجموع چین واقعی و تفسیر سرور نمایش داده می‌شود',
    (tester) async {
      final client = _FakeClient({
        'member_id': 3,
        'measurements': [
          {
            'id': 1,
            'measured_at': '2026-09-01T00:00:00',
            'sum_mm': 96.0,
            'sites': {},
            'body_fat_pct': null,
          },
          {
            'id': 2,
            'measured_at': '2026-11-01T00:00:00',
            'sum_mm': 88.0,
            'sites': {},
            'body_fat_pct': null,
          },
        ],
        'trend': {'delta_mm': -8.0, 'days': 61, 'per_week': -0.92},
        'interpretation': {
          'status': 'decreasing',
          'headline': 'بافت زیرجلدی کاهش یافته است',
          'detail': 'مجموع چین‌ها ۸ میلی‌متر کم شده',
          'confidence': 'high',
        },
        'data_state': 'ok',
        'body_fat_note': 'قفل تا تأیید مرجع مستقل (D-012)',
        'rule_version': 'jp7-trend-1.0',
      });

      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(find.textContaining('بافت زیرجلدی کاهش یافته'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('jp7-trend-chart')),
        findsOneWidget,
        reason: 'نمودار عضو باید از دو نقطهٔ واقعی API ساخته شود',
      );
      expect(
        find.textContaining('ابتدا: ۹۶.۰'),
        findsOneWidget,
        reason: 'نقطهٔ اول نمودار باید از measurements API بیاید',
      );
      expect(
        find.textContaining('آخر: ۸۸.۰'),
        findsOneWidget,
        reason: 'نقطهٔ آخر نمودار باید از measurements API بیاید',
      );
      expect(
        find.textContaining('۸۸'),
        findsOneWidget,
        reason: 'آخرین مجموع چین باید از پاسخ سرور بیاید',
      );
      // درصد چربی قفل است (D-012) — صفحه نباید عددی برایش بسازد
      expect(find.textContaining('٪'), findsNothing);
    },
  );
}
