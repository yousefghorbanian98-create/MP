/// M62 / D10 — اپ عضو در طول اجرا هیچ 401→refresh نداشت.
///
/// اثبات باگ: `grep -n "401" client/lib/core/api_client.dart` صفر بود و
/// `restore()` فقط یک‌بار در `main()` صدا زده می‌شد. توکن دسترسی ۳۰ دقیقه
/// اعتبار دارد؛ عضو ۱۵ دقیقه تمرین می‌کند و وقتی برمی‌گردد به اپ، همهٔ
/// صفحه‌ها خطا می‌دهند و تنها راه، بستن و باز کردن اپ است.
///
/// این تست قفل می‌کند که با ۴۰۱:
///   ۱) یک‌بار `POST /auth/refresh` صدا زده شود
///   ۲) درخواست اصلی با توکن تازه **تکرار** شود و موفق برگردد
///   ۳) اگر refresh هم شکست بخورد، کاربر به صفحهٔ ورود برگردد (نه خطای گنگ)
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/api_client.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _ScriptedClient extends http.BaseClient {
  _ScriptedClient(this.script);

  /// مسیر → فهرست پاسخ‌های پشت‌سرهم (هر بار یکی مصرف می‌شود).
  final Map<String, List<http.Response Function()>> script;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    final queue = script[path];
    final resp = (queue == null || queue.isEmpty)
        ? http.Response('{}', 200)
        : queue.removeAt(0)();
    return http.StreamedResponse(
      Stream.value(resp.bodyBytes),
      resp.statusCode,
      headers: resp.headers,
      request: request,
    );
  }
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('۴۰۱ → refresh → تکرار همان درخواست با توکن تازه', () async {
    final client = _ScriptedClient({
      '/protected': [
        () => http.Response('{"error":{"message":"توکن منقضی"}}', 401),
        () => http.Response('{"ok":true}', 200),
      ],
      '/auth/refresh': [
        () => http.Response('{"access_token":"fresh","refresh_token":"r2"}', 200),
      ],
    });

    final api = ApiClient(httpClient: client);
    api.attachSession(refresher: () async => true);
    api.accessToken = 'expired';

    final result = await api.get('/protected');

    expect(result, {'ok': true});
    expect(client.calls, [
      'GET /protected',
      'POST /auth/refresh',
      'GET /protected',
    ]);
    expect(api.accessToken, 'fresh', reason: 'توکن تازه باید جایگزین شود');
  });

  test('اگر refresh شکست بخورد، خطای ۴۰۱ بالا می‌آید و نشست پاک می‌شود', () async {
    final client = _ScriptedClient({
      '/protected': [() => http.Response('{"error":{"message":"توکن نامعتبر"}}', 401)],
      '/auth/refresh': [() => http.Response('{"error":{"message":"refresh منقضی"}}', 401)],
    });

    var sessionCleared = false;
    final api = ApiClient(httpClient: client);
    api.attachSession(
      refresher: () async => false,
      onSessionLost: () => sessionCleared = true,
    );
    api.accessToken = 'expired';

    await expectLater(api.get('/protected'), throwsA(isA<ApiException>()));
    expect(sessionCleared, isTrue, reason: 'کاربر باید به ورود برگردد، نه دیدن خطای گنگ');
  });

  test('۴۰۱ فقط یک‌بار refresh می‌کند — حلقهٔ بی‌پایان ممنوع', () async {
    final client = _ScriptedClient({
      '/protected': [
        () => http.Response('{}', 401),
        () => http.Response('{}', 401),
        () => http.Response('{}', 401),
      ],
      '/auth/refresh': [() => http.Response('{"access_token":"fresh"}', 200)],
    });

    final api = ApiClient(httpClient: client);
    api.attachSession(refresher: () async => true);
    api.accessToken = 'expired';

    await expectLater(api.get('/protected'), throwsA(isA<ApiException>()));
    expect(client.calls.where((c) => c == 'POST /auth/refresh').length, 1,
        reason: 'refresh دوباره و دوباره = حلقهٔ بی‌پایان روی سرور');
  });

  test('refresh خودش ۴۰۱ نگیرد — وگرنه بازگشتی می‌شود', () async {
    final client = _ScriptedClient({
      '/auth/refresh': [() => http.Response('{"access_token":"fresh"}', 200)],
      '/data': [() => http.Response('{"ok":1}', 200)],
    });
    final api = ApiClient(httpClient: client);
    api.attachSession(refresher: () async => true);
    await api.get('/data');
    expect(client.calls, ['GET /data']);
  });
}
