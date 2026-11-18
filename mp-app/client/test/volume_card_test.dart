/// M77 — حجم عضلات از API عضو: source, landmarks, level, empty/error/retry.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/today/volume_card.dart';

class _VolumeClient extends http.BaseClient {
  bool fail = false;
  bool empty = false;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('$path?${request.url.query}');
    final payload = fail
        ? {'detail': 'گزارش حجم در دسترس نیست'}
        : _report(
            empty: empty,
            level: request.url.queryParameters['level'] ?? '',
          );
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

Map<String, dynamic> _report({bool empty = false, required String level}) => {
  'member_id': 3,
  'program_id': empty ? null : 12,
  'level': level,
  'muscles': empty
      ? <dynamic>[]
      : [
          {
            'muscle': 'پشت',
            'level': level,
            'planned_sets': 12,
            'effective_sets': 8,
            'source_of_number': 'reported_hard_sets',
            'data_state': 'reported',
            'hard_sets': 8,
            'soft_sets': 2,
            'unknown_rir_sets': 1,
            'landmarks': {
              'muscle': 'پشت',
              'level': level,
              'mv': 4,
              'mev': 8,
              'mav_min': 10,
              'mav_max': 14,
              'mrv': 20,
              'hard_set_max_rir': 3,
              'source': 'جدول نمونهٔ تمرینی',
            },
            'status': 'mev',
            'suggestion': {'delta_sets': 0, 'reason': 'حجم فعلی حفظ شود'},
          },
        ],
  'reason': empty
      ? 'هنوز برنامه‌ای برای این عضو ثبت نشده است.'
      : 'بر اساس برنامه و بازخورد ست‌های عضو.',
  'rule_version': 'volume-report-1.0',
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
      child: Scaffold(body: ListView(children: [VolumeCard()])),
    ),
  ),
);

void main() {
  testWidgets(
    'حجم و نشانگرها از endpoint عضو می‌آیند و سطح درخواست تغییر می‌کند',
    (tester) async {
      final client = _VolumeClient();
      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(
        client.calls,
        contains('/programs/member/3/volume?level=intermediate'),
      );
      expect(find.text('حجم هفتگی عضلات'), findsOneWidget);
      expect(find.text('روی MEV'), findsOneWidget);
      expect(
        find.textContaining(
          'ست مؤثر ۸ از ۱۲ برنامه‌ریزی‌شده · منبع: بازخورد عضو',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('MV ۴ · MEV ۸'), findsOneWidget);
      expect(find.textContaining('RIR نامعلوم ۱'), findsOneWidget);
      expect(find.textContaining('پیشنهاد هفتهٔ بعد'), findsOneWidget);

      await tester.tap(find.text('مبتدی'));
      await tester.pumpAndSettle();
      expect(
        client.calls,
        contains('/programs/member/3/volume?level=beginner'),
      );
      expect(client.calls.last, contains('level=beginner'));
    },
  );

  testWidgets('بدون برنامه حالت empty و علت API را نشان می‌دهد', (
    tester,
  ) async {
    final client = _VolumeClient()..empty = true;
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(
      find.text('هنوز برنامه‌ای برای این عضو ثبت نشده است.'),
      findsOneWidget,
    );
    expect(find.textContaining('ست مؤثر ۸ از ۱۲'), findsNothing);
  });

  testWidgets('خطای volume جدا از empty است و retry دوباره از API می‌خواند', (
    tester,
  ) async {
    final client = _VolumeClient()..fail = true;
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('دریافت حجم هفتگی ناموفق بود'), findsOneWidget);
    expect(find.textContaining('هنوز برنامه‌ای'), findsNothing);

    client.fail = false;
    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();
    expect(find.text('روی MEV'), findsOneWidget);
    expect(client.calls.length, greaterThanOrEqualTo(2));
  });
}
