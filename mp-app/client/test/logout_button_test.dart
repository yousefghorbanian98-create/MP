/// M61 / D3 — دکمهٔ خروج در صفحهٔ پروفایل.
///
/// تست سرویس (`logout_test.dart`) فقط رفتار `AuthController.logout` را قفل
/// می‌کند. اگر دکمه به آن وصل نباشد، کاربر همچنان راهی برای خروج ندارد —
/// یعنی «کد آماده ولی بی‌مصرف»، همان دسته باگی که R5/G1 هم از آن رنج می‌بردند.
/// این تست وجود دکمه، تأیید کاربر، و انجام واقعی خروج را می‌سنجد.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/profile/profile_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeClient extends http.BaseClient {
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    final payload = path == '/members/me'
        ? {'id': 3, 'full_name': 'عضو تست', 'phone': '09350000001', 'goal': 'strength'}
        : <String, dynamic>{'ok': true};
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(Stream.value(bytes), 200,
        headers: {'content-type': 'application/json'}, request: request);
  }
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({
      'mp_token': 'access-1',
      'mp_refresh': 'refresh-1',
    });
  });

  testWidgets('دکمهٔ خروج وجود دارد، تأیید می‌گیرد و توکن را پاک می‌کند', (tester) async {
    final client = _FakeClient();
    final api = ApiClient(httpClient: client)..accessToken = 'access-1';
    final auth = AuthController(api, refreshToken: 'refresh-1');
    await auth.restore();

    await tester.pumpWidget(ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith((ref) => auth),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: ProfilePage()),
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final button = find.text('خروج از حساب');
    expect(button, findsOneWidget, reason: 'بدون این دکمه، کاربر هیچ راه خروجی ندارد');

    await tester.tap(button);
    await tester.pumpAndSettle();

    // انصراف: نباید خارج شود
    expect(find.text('انصراف'), findsOneWidget);
    await tester.tap(find.text('انصراف'));
    await tester.pumpAndSettle();
    expect(await (await SharedPreferences.getInstance()).getString('mp_token'), 'access-1');

    // این بار تأیید
    await tester.tap(button);
    await tester.pumpAndSettle();
    await tester.tap(find.text('خروج'));
    await tester.pumpAndSettle();

    expect(auth.state.loggedIn, isFalse);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('mp_token'), isNull);
    expect(prefs.getString('mp_refresh'), isNull);
    expect(client.calls.contains('POST /auth/logout'), isTrue,
        reason: 'نشست سمت سرور هم باید بسته شود');
  });
}
