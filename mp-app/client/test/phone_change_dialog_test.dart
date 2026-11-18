/// M82 — the member profile verifies the current and proposed phone in order.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/api_client.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/features/profile/phone_change_dialog.dart';
import 'package:mp_client/features/profile/profile_page.dart';

class _PhoneChangeClient extends http.BaseClient {
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final body =
        jsonDecode((request as http.Request).body) as Map<String, dynamic>;
    final path = request.url.path;
    late final int status;
    late final Map<String, dynamic> payload;
    if (path.endsWith('/auth/phone-change/request')) {
      status = 200;
      payload = {
        'challenge_id': 'challenge-m82-test',
        'expires_in': 120,
        'dev_code': '111111',
      };
    } else if (path.endsWith('/auth/phone-change/verify-old') &&
        body['code'] == '000000') {
      status = 400;
      payload = {
        'error': {
          'code': 'invalid_otp',
          'message': 'کد شمارهٔ فعلی نادرست است',
        },
      };
    } else if (path.endsWith('/auth/phone-change/verify-old')) {
      status = 200;
      payload = {
        'challenge_id': 'challenge-m82-test',
        'expires_in': 120,
        'dev_code': '222222',
      };
    } else if (path.endsWith('/auth/phone-change/confirm')) {
      status = 200;
      payload = {'status': 'phone_changed', 'phone': '09123456789'};
    } else {
      throw StateError('Unexpected API request: $path');
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

class _ProfileClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (!request.url.path.endsWith('/members/me')) {
      throw StateError('Unexpected profile request: ${request.url.path}');
    }
    final bytes = utf8.encode(
      jsonEncode({
        'id': 3,
        'user_id': 7,
        'full_name': 'عضو آزمون',
        'phone': '09121234567',
        'goal': 'fitness',
        'gender': 'male',
        'height_cm': 175,
        'constraints': '[]',
      }),
    );
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

class _PhoneChangeHarness extends StatefulWidget {
  const _PhoneChangeHarness();

  @override
  State<_PhoneChangeHarness> createState() => _PhoneChangeHarnessState();
}

class _PhoneChangeHarnessState extends State<_PhoneChangeHarness> {
  String _result = 'pending';

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextButton(
            onPressed: () async {
              final result = await showDialog<bool>(
                context: context,
                builder: (_) =>
                    const PhoneChangeDialog(currentPhone: '09121234567'),
              );
              if (mounted) setState(() => _result = '$result');
            },
            child: const Text('باز کردن'),
          ),
          Text('نتیجه: $_result'),
        ],
      ),
    ),
  );
}

void main() {
  testWidgets('تأیید شمارهٔ فعلی سپس جدید؛ خطای کد، شماره را تغییر نمی‌دهد', (
    tester,
  ) async {
    final httpClient = _PhoneChangeClient();
    final api = ApiClient(
      httpClient: httpClient,
      baseUrl: 'https://api.example.test/api/v1',
    )..accessToken = 'session-token';

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(api)],
        child: const MaterialApp(
          home: Directionality(
            textDirection: TextDirection.rtl,
            child: _PhoneChangeHarness(),
          ),
        ),
      ),
    );

    await tester.tap(find.text('باز کردن'));
    await tester.pumpAndSettle();
    expect(find.text('تغییر شمارهٔ موبایل'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '09123456789');
    await tester.tap(find.text('ارسال کد به شمارهٔ فعلی'));
    await tester.pumpAndSettle();
    expect(find.text('کد آزمایشی: 111111'), findsOneWidget);
    expect(find.textContaining('شمارهٔ فعلی 09121234567'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '000000');
    await tester.tap(find.text('تأیید کد فعلی و ارسال کد جدید'));
    await tester.pumpAndSettle();
    expect(find.text('کد شمارهٔ فعلی نادرست است'), findsOneWidget);
    expect(find.text('تأیید شمارهٔ فعلی'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '123456');
    await tester.tap(find.text('تأیید کد فعلی و ارسال کد جدید'));
    await tester.pumpAndSettle();
    expect(find.text('تأیید شمارهٔ جدید'), findsOneWidget);
    expect(find.text('کد آزمایشی: 222222'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '222222');
    await tester.tap(find.text('تأیید و تغییر شماره'));
    await tester.pumpAndSettle();
    expect(find.text('نتیجه: true'), findsOneWidget);

    expect(httpClient.requests.map((request) => request.url.path).toList(), [
      '/api/v1/auth/phone-change/request',
      '/api/v1/auth/phone-change/verify-old',
      '/api/v1/auth/phone-change/verify-old',
      '/api/v1/auth/phone-change/confirm',
    ]);
    for (final request in httpClient.requests) {
      expect(request.headers['Authorization'], 'Bearer session-token');
    }
    final requestBody = jsonDecode(
      (httpClient.requests.first as http.Request).body,
    );
    expect(requestBody, {'new_phone': '09123456789'});
    final confirmBody = jsonDecode(
      (httpClient.requests.last as http.Request).body,
    );
    expect(confirmBody, {
      'challenge_id': 'challenge-m82-test',
      'code': '222222',
    });
  });

  testWidgets('پروفایل عضو، تغییر شماره را به دیالوگ دو مرحله‌ای وصل می‌کند', (
    tester,
  ) async {
    final api = ApiClient(
      httpClient: _ProfileClient(),
      baseUrl: 'https://api.example.test/api/v1',
    )..accessToken = 'session-token';

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(api)],
        child: const MaterialApp(home: Scaffold(body: ProfilePage())),
      ),
    );
    await tester.pumpAndSettle();

    final changeButton = find.text('تغییر شمارهٔ موبایل');
    expect(changeButton, findsOneWidget);
    await tester.tap(changeButton);
    await tester.pumpAndSettle();
    expect(find.byType(PhoneChangeDialog), findsOneWidget);
    expect(find.text('ارسال کد به شمارهٔ فعلی'), findsOneWidget);
  });
}
