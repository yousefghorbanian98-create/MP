/// M80 — تاریخچهٔ حضور فقط از مسیر self-scoped عضو خوانده می‌شود.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/checkin/checkin_page.dart';
import 'package:mp_client/features/checkin/member_checkin_history.dart';

class _HistoryClient extends http.BaseClient {
  _HistoryClient({
    this.failNext = false,
    this.hasMore = false,
    List<Map<String, dynamic>>? items,
    List<Map<String, dynamic>>? nextPage,
  })  : items = items ?? _defaultItems,
        nextPage = nextPage ?? const [];

  bool failNext;
  final bool hasMore;
  final List<Map<String, dynamic>> items;
  final List<Map<String, dynamic>> nextPage;
  final List<String> calls = [];
  final List<int> offsets = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    var status = 200;
    dynamic payload;
    if (request.method == 'GET' && path == '/members/me/checkins') {
      final offset = int.parse(request.url.queryParameters['offset'] ?? '0');
      offsets.add(offset);
      if (failNext) {
        failNext = false;
        status = 503;
        payload = {'detail': 'پاسخ آزمایشی ناموفق'};
      } else {
        payload = {
          'items': offset == 0 ? items : nextPage,
          'has_more': offset == 0 && hasMore,
          'limit': 30,
          'offset': offset,
          'rule_version': 'member-checkin-history-1.0',
          'generated_at': '2026-11-16T12:00:00Z',
        };
      }
    } else if (request.method == 'GET' && path == '/face/qr-token') {
      payload = {'payload': 'signed-test-payload', 'member_id': 3};
    } else if (request.method == 'GET' && path == '/members/me/face-consent') {
      payload = {'consent': true};
    } else {
      status = 404;
      payload = {'detail': 'not found'};
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

final _defaultItems = [
  {
    'checkin_id': 41,
    'method': 'qr',
    'result': 'ok',
    'denial_reason': '',
    'checked_in_at': '2026-11-16T08:15:00Z',
    'checked_out_at': null,
    'is_open': true,
  },
  {
    'checkin_id': 40,
    'method': 'face',
    'result': 'denied',
    'denial_reason': 'membership_expired',
    'checked_in_at': '2026-11-15T09:00:00Z',
    'checked_out_at': null,
    'is_open': false,
  },
];

Widget _wrap(
  http.Client client, {
  Widget child = const MemberCheckInHistoryPage(),
}) =>
    ProviderScope(
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
          child: Scaffold(body: child),
        ),
      ),
    );

void main() {
  testWidgets('سوابق واقعی و ورود ردشده را فقط از مسیر عضو جاری نشان می‌دهد',
      (tester) async {
    final client = _HistoryClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('ورود ثبت شد'), findsOneWidget);
    expect(find.text('ورود ثبت نشد'), findsOneWidget);
    expect(find.text('اشتراک فعال نیست یا منقضی شده است'), findsOneWidget);
    expect(client.calls, contains('GET /members/me/checkins'));
    expect(client.calls.any((call) => call.contains('/admin/checkins')), isFalse);
    expect(client.calls.every((call) => !call.contains('member_id=')), isTrue,
        reason: 'شناسهٔ عضو نباید از کلاینت قابل انتخاب باشد');
  });

  testWidgets('تاریخچهٔ خالی را به‌جای دادهٔ ساختگی نشان می‌دهد', (tester) async {
    final client = _HistoryClient(items: []);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('هنوز سابقهٔ حضوری ثبت نشده است.'), findsOneWidget);
    expect(find.text('ورود ثبت شد'), findsNothing);
  });

  testWidgets('خطای API را خالی جا نمی‌زند و امکان تلاش دوباره دارد', (tester) async {
    final client = _HistoryClient(failNext: true);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('دریافت سوابق حضور ناموفق بود'), findsOneWidget);
    expect(find.text('هنوز سابقهٔ حضوری ثبت نشده است.'), findsNothing);

    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();

    expect(client.calls.where((call) => call == 'GET /members/me/checkins').length, 2);
    expect(find.text('ورود ثبت شد'), findsOneWidget);
  });

  testWidgets('سوابق قدیمی‌تر با offset صفحهٔ بعد بارگیری می‌شود', (tester) async {
    final firstPage = List<Map<String, dynamic>>.generate(
      30,
      (index) => <String, dynamic>{
        'checkin_id': 100 + index,
        'method': 'qr',
        'result': 'ok',
        'denial_reason': '',
        'checked_in_at': '2026-11-16T08:15:00Z',
        'checked_out_at': null,
        'is_open': true,
      },
    );
    final client = _HistoryClient(
      items: firstPage,
      hasMore: true,
      nextPage: [
        <String, dynamic>{
          'checkin_id': 99,
          'method': 'manual',
          'result': 'ok',
          'denial_reason': '',
          'checked_in_at': '2026-11-14T08:15:00Z',
          'checked_out_at': '2026-11-14T10:00:00Z',
          'is_open': false,
        },
      ],
    );
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(client.offsets, [0]);
    await tester.ensureVisible(find.text('سوابق قدیمی‌تر'));
    await tester.tap(find.text('سوابق قدیمی‌تر'));
    await tester.pumpAndSettle();

    expect(client.offsets, [0, 30]);
    expect(find.text('ثبت پذیرش'), findsOneWidget);
  });

  testWidgets('سوابق از تب چک‌این عضو هم در دسترس است', (tester) async {
    final client = _HistoryClient();
    await tester.pumpWidget(_wrap(client, child: const CheckInPage()));
    await tester.pumpAndSettle();

    expect(find.text('سوابق'), findsOneWidget);
    await tester.tap(find.text('سوابق'));
    await tester.pumpAndSettle();

    expect(find.text('سوابق حضور'), findsOneWidget);
    expect(find.text('ورود ثبت شد'), findsOneWidget);
    expect(client.calls, contains('GET /members/me/checkins'));
  });
}
