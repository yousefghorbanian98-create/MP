/// M76 — readiness card از API MP: estimated score، empty/loading/error.
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/today/readiness_card.dart';

class _ReadinessClient extends http.BaseClient {
  bool fail = false;
  Completer<void>? gate;
  int calls = 0;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    calls++;
    await gate?.future;
    final payload = fail ? {'detail': 'پاسخ آمادگی در دسترس نیست'} : _report();
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      fail ? 503 : 200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Map<String, dynamic> _report({bool available = true}) => {
      'member_id': 3,
      'program_id': available ? 12 : null,
      'readiness': available
          ? {
              'score': 68.4,
              'band': 'monitor',
              'recommendation': 'keep',
              'volume_delta_sets': 0,
              'reason': 'امتیاز در ناحیهٔ مراقبت است؛ حجم حفظ می‌شود.',
              'signals': [
                {
                  'name': 'soreness',
                  'value': 5,
                  'score': 50,
                  'reason': 'درد ثبت‌شده متوسط است.',
                },
                {
                  'name': 'rir_mismatch',
                  'value': null,
                  'score': null,
                  'reason': 'RIR هدف در برنامه ثبت نشده است.',
                },
              ],
              'missing_signals': ['rir_mismatch'],
            }
          : null,
      'data_counts': available
          ? {'feedback_rows': 3, 'sets_last_7_days': 2, 'sets_prior_7_days': 1}
          : null,
      'reason': available ? 'بر اساس بازخورد ثبت‌شده' : 'هیچ برنامه‌ای ثبت نشده است.',
      'note': available ? 'RIR هدف موجود نیست.' : null,
      'rule_version': 'readiness-report-1.0',
    };

Widget _wrap(http.Client client) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) => AuthController.test(
            AuthState(accessToken: 'test-token', memberId: 3, userName: 'عضو تست'),
          ),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: ListView(children: [ReadinessCard()])),
        ),
      ),
    );

void main() {
  testWidgets('بارگیری readiness را نشان می‌دهد و بعد داده/توصیهٔ API را می‌خواند',
      (tester) async {
    final client = _ReadinessClient()..gate = Completer<void>();
    await tester.pumpWidget(_wrap(client));
    await tester.pump();

    expect(find.text('در حال دریافت آمادگی از داده‌های تمرین…'), findsOneWidget);
    client.gate!.complete();
    await tester.pumpAndSettle();

    expect(find.text('۶۸.۴ از ۱۰۰'), findsOneWidget);
    expect(find.text('نیازمند مراقبت'), findsOneWidget);
    expect(find.text('توصیه: حفظ حجم'), findsOneWidget);
    expect(find.textContaining('تشخیص پزشکی نیست'), findsOneWidget);
    // The signal is also repeated in the missing-signal summary.
    expect(find.textContaining('اختلاف RIR'), findsWidgets);
    expect(find.textContaining('RIR هدف در برنامه ثبت نشده'), findsOneWidget);
    expect(client.calls, 1);
  });

  testWidgets('بدون برنامهٔ قابل سنجش امتیاز صفر یا ساختگی تولید نمی‌کند', (tester) async {
    // همان endpoint، پاسخ معتبر با readiness=null.
    final noDataClient = _NoDataClient();
    await tester.pumpWidget(_wrap(noDataClient));
    await tester.pumpAndSettle();

    expect(find.text('آمادگی هنوز قابل محاسبه نیست'), findsOneWidget);
    expect(find.text('هیچ برنامه‌ای ثبت نشده است.'), findsOneWidget);
    expect(find.textContaining('امتیاز یا توصیهٔ ساختگی'), findsOneWidget);
    expect(find.textContaining('از ۱۰۰'), findsNothing);
  });

  testWidgets('خطای API جدا از دادهٔ ناکافی است و امکان retry می‌دهد', (tester) async {
    final client = _ReadinessClient()..fail = true;
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('آمادگی دریافت نشد'), findsOneWidget);
    expect(find.text('آمادگی هنوز قابل محاسبه نیست'), findsNothing);
    client.fail = false;
    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();
    expect(find.text('۶۸.۴ از ۱۰۰'), findsOneWidget);
    expect(client.calls, greaterThanOrEqualTo(2));
  });
}

class _NoDataClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final bytes = utf8.encode(jsonEncode(_report(available: false)));
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}
