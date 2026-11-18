/// M61 / D1+D2 — تب «چهره» در اپ عضو.
///
/// دو باگ اثبات‌شده با curl زنده:
///   D1: دکمهٔ «ثبت چهره» → `POST /face/enroll` با نقش member همیشه ۴۰۳
///       (rbac فقط DELETE داشت). حالا مسیر باز شد، ولی بدون رضایت هم ۴۰۳ است؛
///       پس UI باید **قبل از کلیک** بداند و راه رضایت را نشان دهد.
///   D2: دکمهٔ «چک‌این» بدنهٔ `{member_id, image_base64}` می‌فرستاد به مسیری
///       که اسکیمایش `{member_id, method}` است → ۴۲۲ «Field required»، یعنی
///       این تب هیچ‌وقت کار نکرده بود.
///
/// این تست شکل درخواست‌ها و گیت رضایت را قفل می‌کند، چون آن دو تنها چیزی
/// هستند که می‌شود بدون دستگاه واقعی سنجید.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/checkin/checkin_page.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient({required this.consent, this.enrolled = false});

  final bool consent;
  final bool enrolled;
  final List<String> calls = [];
  final List<Map<String, dynamic>> bodies = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    if (request is http.Request && request.body.isNotEmpty) {
      bodies.add({
        'path': path,
        ...jsonDecode(request.body) as Map<String, dynamic>,
      });
    }
    final payload = switch (path) {
      '/face/qr-token' => {'payload': 'QR-PAYLOAD', 'member_id': 3},
      '/members/me/face-consent' => {
          'member_id': 3,
          'consent': consent,
          'policy_version': consent ? 'v1' : null,
          'enrolled': enrolled,
        },
      '/face/privacy-notice' => {'text': 'متن اطلاعیه'},
      _ => {'status': 'ok', 'result': 'ok'},
    };
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
          child: Scaffold(body: CheckInPage()),
        ),
      ),
    );

Future<void> _openFaceTab(WidgetTester tester) async {
  await tester.pumpAndSettle();
  await tester.tap(find.text('چهره'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'بدون رضایت: وضعیت از سرور خوانده می‌شود و دکمهٔ چک‌این رندر نمی‌شود',
    (tester) async {
      final client = _FakeClient(consent: false);
      await tester.pumpWidget(_wrap(client));
      await _openFaceTab(tester);

      expect(
        client.calls.contains('GET /members/me/face-consent'),
        isTrue,
        reason:
            'UI باید بداند رضایت دارد یا نه، نه اینکه بعد از کلیک ۴۰۳ بخورد',
      );
      expect(find.textContaining('رضایت بیومتریک'), findsOneWidget);
      expect(find.text('رضایت می‌دهم'), findsOneWidget);
      expect(
        find.text('چک‌این'),
        findsNothing,
        reason: 'تا رضایت نباشد، چک‌این بیومتریک نباید پیشنهاد شود',
      );
    },
  );

  testWidgets('دکمهٔ «ثبت چهره» وجود ندارد — تصمیم صادقانه، نه دکمهٔ ۴۰۳', (
    tester,
  ) async {
    final client = _FakeClient(consent: true, enrolled: false);
    await tester.pumpWidget(_wrap(client));
    await _openFaceTab(tester);

    expect(
      find.text('ثبت چهره'),
      findsNothing,
      reason:
          'R3: دکمه‌ای که نقش/مسیر واقعاً نمی‌تواند انجام دهد نباید رندر شود',
    );
    expect(
      find.textContaining('توسط پذیرش'),
      findsOneWidget,
      reason: 'کاربر باید بداند ثبت چهره را از کجا بگیرد',
    );
  });

  testWidgets('چک‌این با روش face و بدون image_base64 فرستاده می‌شود (D2)', (
    tester,
  ) async {
    // consent: true → دکمهٔ چک‌این رندر می‌شود
    final client = _FakeClient(consent: true, enrolled: true);
    await tester.pumpWidget(_wrap(client));
    await _openFaceTab(tester);

    await tester.tap(find.text('چک‌این'));
    await tester.pumpAndSettle();

    final checkin =
        client.bodies.where((b) => b['path'] == '/face/checkin').toList();
    expect(checkin, isNotEmpty, reason: 'دکمه باید درخواست را واقعاً بفرستد');
    expect(
      checkin.single['method'],
      'face',
      reason: 'schema سرور: {member_id, method} — نبودِ method همان ۴۲۲ بود',
    );
    expect(
      checkin.single.containsKey('image_base64'),
      isFalse,
      reason: 'سرور این فیلد را نمی‌پذیرد؛ فرستادنش نشانهٔ باگ قدیمی است',
    );
  });
}
