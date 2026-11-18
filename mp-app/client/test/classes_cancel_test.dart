/// M74 — لغو رزرو عضو، حفظ member scope و refresh کردن ظرفیت/وضعیت.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/haptics.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/classes/classes_page.dart';

import 'haptics_recorder.dart';

class _ClassesClient extends http.BaseClient {
  _ClassesClient({bool initiallyBooked = true}) : booked = initiallyBooked;

  bool booked;
  bool cancelled = false;
  Map<String, dynamic>? bookBody;
  Map<String, dynamic>? cancelBody;
  int listCalls = 0;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    dynamic payload;
    if (request.method == 'GET' && path == '/classes') {
      listCalls++;
      final hasBooking = booked && !cancelled;
      payload = [
        {
          'id': 4,
          'name': 'یوگا',
          'schedule_text': 'امروز',
          'seats_left': hasBooking ? 0 : 1,
          'confirmed': hasBooking ? 1 : 0,
          'waitlisted': 0,
          'member_booking_status': hasBooking ? 'confirmed' : null,
          'member_booking_name': hasBooking ? 'سارا از پایگاه داده' : null,
        },
      ];
    } else if (request.method == 'POST' && path == '/classes/book') {
      bookBody =
          jsonDecode((request as http.Request).body) as Map<String, dynamic>;
      booked = true;
      cancelled = false;
      payload = {
        'id': 19,
        'status': 'confirmed',
        'member_name': 'سارا از پایگاه داده',
      };
    } else if (request.method == 'POST' && path == '/classes/cancel') {
      cancelBody =
          jsonDecode((request as http.Request).body) as Map<String, dynamic>;
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

Widget _wrap(http.Client client, {RecordingHaptics? haptics}) => ProviderScope(
      overrides: [
        if (haptics != null) hapticsProvider.overrideWith((ref) => haptics),
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
          child: Scaffold(body: ClassesPage()),
        ),
      ),
    );

void main() {
  testWidgets('رزرو خود عضو را لغو و ظرفیت/وضعیت تازه را از API می‌گیرد', (
    tester,
  ) async {
    final client = _ClassesClient();
    final haptics = RecordingHaptics();
    await tester.pumpWidget(_wrap(client, haptics: haptics));
    await tester.pumpAndSettle();

    expect(find.text('لغو رزرو'), findsOneWidget);
    expect(
      find.textContaining('رزرو به نام سارا از پایگاه داده تأیید شده'),
      findsOneWidget,
    );

    await tester.ensureVisible(find.text('لغو رزرو'));
    await tester.tap(find.text('لغو رزرو'));
    await tester.pumpAndSettle();

    expect(client.cancelBody?['class_id'], 4);
    expect(
      client.cancelBody?['member_id'],
      3,
      reason: 'member_id از نشست کاربر می‌آید، نه از انتخاب آزاد',
    );
    expect(
      client.listCalls,
      greaterThanOrEqualTo(2),
      reason: 'پس از لغو باید ظرفیت و وضعیت رزرو دوباره از API خوانده شود',
    );
    expect(find.text('✅ رزرو لغو شد'), findsOneWidget);
    // M98/UX-G3 — لغو موفق یک پالس لمسی دارد؛ بی‌صدا «انجام شد» فقط متن است
    expect(haptics.count('success'), 1);
    expect(haptics.count('warning'), 0);
    expect(
      find.textContaining('رزرو به نام سارا از پایگاه داده تأیید شده'),
      findsNothing,
    );
    expect(find.text('رزرو'), findsOneWidget);
  });

  testWidgets('تأیید رزرو نام معتبر برگشتی از سرور را نمایش می‌دهد', (
    tester,
  ) async {
    final client = _ClassesClient(initiallyBooked: false);
    final haptics = RecordingHaptics();
    await tester.pumpWidget(_wrap(client, haptics: haptics));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('رزرو'));
    await tester.tap(find.text('رزرو'));
    await tester.pumpAndSettle();

    expect(client.bookBody?['class_id'], 4);
    expect(client.bookBody?['member_id'], 3);
    expect(
      find.text('✅ رزرو به نام سارا از پایگاه داده ثبت شد (تأییدشده)'),
      findsOneWidget,
    );
    expect(haptics.count('success'), 1);
    expect(
      find.textContaining('رزرو به نام سارا از پایگاه داده تأیید شده'),
      findsOneWidget,
    );
  });
}
