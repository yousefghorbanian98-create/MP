/// M75 — صندوق اعلان عضو: unread count، mark-as-read و حالت‌های خالی/خطا.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/notifications/notifications_page.dart';

class _NotificationsClient extends http.BaseClient {
  bool failList;
  _NotificationsClient({this.failList = false});

  final List<Map<String, dynamic>> rows = [
    _row(31, 'تمرین امروز', null),
    _row(32, 'یادآوری اشتراک', null),
    _row(33, 'پیام مربی', null),
  ];
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    dynamic payload;
    var status = 200;
    if (request.method == 'GET' && path == '/notifications/member/3') {
      if (failList) {
        status = 503;
        payload = {
          'error': {'message': 'پاسخ آزمایشی ناموفق'},
        };
      } else {
        payload = rows;
      }
    } else if (request.method == 'POST' && path.startsWith('/notifications/')) {
      final id = int.parse(path.split('/')[2]);
      final row = rows.firstWhere((item) => item['id'] == id);
      row['read_at'] = '2026-11-16T12:30:00Z';
      payload = row;
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

Map<String, dynamic> _row(int id, String title, String? readAt) => {
      'id': id,
      'member_id': 3,
      'channel': 'inapp',
      'title': title,
      'body': 'متن اعلان نمونه',
      'kind': 'general',
      'read_at': readAt,
      'created_at': '2026-11-16T12:00:00Z',
    };

Widget _wrap(http.Client client) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) => AuthController.test(
            AuthState(
                accessToken: 'test-token', memberId: 3, userName: 'عضو تست'),
          ),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: NotificationsPage(),
        ),
      ),
    );

void main() {
  testWidgets(
    'سه اعلان را می‌خواند، شمارش unread را نشان می‌دهد و read را ثبت می‌کند',
    (tester) async {
      final client = _NotificationsClient();
      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(find.text('۳ اعلان خوانده‌نشده'), findsOneWidget);
      for (final title in ['تمرین امروز', 'یادآوری اشتراک', 'پیام مربی']) {
        expect(find.text(title), findsOneWidget);
      }
      expect(client.calls, contains('GET /notifications/member/3'));

      await tester.tap(find.byTooltip('علامت‌گذاری به‌عنوان خوانده‌شده').first);
      await tester.pumpAndSettle();

      expect(client.calls, contains('POST /notifications/31/read'));
      expect(
        client.calls
            .where((call) => call == 'GET /notifications/member/3')
            .length,
        greaterThanOrEqualTo(2),
        reason: 'پس از write، وضعیت باید دوباره از API خوانده شود',
      );
      expect(find.text('۲ اعلان خوانده‌نشده'), findsOneWidget);
      expect(find.text('اعلان به‌عنوان خوانده‌شده ثبت شد'), findsOneWidget);
    },
  );

  testWidgets('حالت inbox خالی را صادقانه نمایش می‌دهد', (tester) async {
    final client = _NotificationsClient()..rows.clear();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('اعلانی ندارید'), findsOneWidget);
    expect(find.text('۰ اعلان خوانده‌نشده'), findsNothing);
    expect(find.byTooltip('علامت‌گذاری به‌عنوان خوانده‌شده'), findsNothing);
  });

  testWidgets('خطای API را empty جا نمی‌زند و retry دارد', (tester) async {
    final client = _NotificationsClient(failList: true);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('دریافت اعلان‌ها ناموفق بود'), findsOneWidget);
    expect(find.text('اعلانی ندارید'), findsNothing);

    client.failList = false;
    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();

    expect(
      client.calls
          .where((call) => call == 'GET /notifications/member/3')
          .length,
      greaterThanOrEqualTo(2),
    );
    expect(find.text('۳ اعلان خوانده‌نشده'), findsOneWidget);
  });
}
