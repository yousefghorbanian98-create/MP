/// M74 — لغو رزرو عضو، حفظ member scope و refresh کردن ظرفیت/وضعیت.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/classes/classes_page.dart';

class _ClassesClient extends http.BaseClient {
  bool cancelled = false;
  Map<String, dynamic>? cancelBody;
  int listCalls = 0;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    dynamic payload;
    if (request.method == 'GET' && path == '/classes') {
      listCalls++;
      payload = [
        {
          'id': 4,
          'name': 'یوگا',
          'schedule_text': 'امروز',
          'seats_left': cancelled ? 1 : 0,
          'confirmed': cancelled ? 0 : 1,
          'waitlisted': 0,
          'member_booking_status': cancelled ? null : 'confirmed',
        }
      ];
    } else if (request.method == 'POST' && path == '/classes/cancel') {
      cancelBody = jsonDecode((request as http.Request).body) as Map<String, dynamic>;
      cancelled = true;
      payload = {'id': 20, 'status': 'cancelled'};
    } else {
      payload = <String, dynamic>{};
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
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: ClassesPage()),
        ),
      ),
    );

void main() {
  testWidgets('رزرو خود عضو را لغو و ظرفیت/وضعیت تازه را از API می‌گیرد', (tester) async {
    final client = _ClassesClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('لغو رزرو'), findsOneWidget);
    expect(find.text('رزرو شما تأیید شده'), findsOneWidget);

    await tester.tap(find.text('لغو رزرو'));
    await tester.pumpAndSettle();

    expect(client.cancelBody?['class_id'], 4);
    expect(client.cancelBody?['member_id'], 3,
        reason: 'member_id از نشست کاربر می‌آید، نه از انتخاب آزاد');
    expect(client.listCalls, greaterThanOrEqualTo(2),
        reason: 'پس از لغو باید ظرفیت و وضعیت رزرو دوباره از API خوانده شود');
    expect(find.text('✅ رزرو لغو شد'), findsOneWidget);
    expect(find.text('رزرو شما تأیید شده'), findsNothing);
    expect(find.text('رزرو'), findsOneWidget);
  });
}
