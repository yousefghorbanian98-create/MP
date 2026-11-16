/// تست‌های کلاینت API واقعی — پاسخ‌ها/خطاها درست تفسیر می‌شوند.
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:http/http.dart' as http;

import 'package:shared_preferences/shared_preferences.dart';

import 'package:mp_client/core/api_client.dart';
import 'package:mp_client/core/session.dart';

void main() {
  test('GET موفق JSON برمی‌گرداند + هدر Authorization', () async {
    late http.Request seen;
    final mock = MockClient((request) async {
      seen = request;
      return http.Response(jsonEncode({'id': 7, 'goal': 'strength'}), 200);
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    api.accessToken = 'tok-123';
    final r = await api.get('/members/me');
    expect((r as Map)['id'], 7);
    final authHeader = seen.headers.map((k, v) => MapEntry(k.toLowerCase(), v))['authorization'];
    expect(authHeader, 'Bearer tok-123');
    expect(seen.url.toString(), 'http://10.0.2.2:8000/api/v1/members/me');
  });

  test('خطای سرور با پیام فارسی detail بالا می‌آید', () async {
    final mock = MockClient((request) async {
      return http.Response.bytes(
        utf8.encode(jsonEncode({'detail': 'کاربر فعال نیست'})),
        401,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    try {
      await api.get('/members/me');
      fail('باید ApiException بدهد');
    } on ApiException catch (e) {
      expect(e.message, 'کاربر فعال نیست');
      expect(e.statusCode, 401);
    }
  });

  test('POST بدنهٔ JSON می‌فرستد', () async {
    late String body;
    final mock = MockClient((request) async {
      body = request.body;
      return http.Response(jsonEncode({'ok': true}), 200);
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    await api.post('/ai/program/generate', {'member_id': 3, 'goal': 'fitness'});
    expect(jsonDecode(body)['member_id'], 3);
  });

  test('AuthController ورود OTP توکن را نگه می‌دارد', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/otp/verify')) {
        return http.Response.bytes(
          utf8.encode(jsonEncode({
            'access_token': 'A1',
            'refresh_token': 'R1',
            'user': {'id': 9, 'full_name': 'کاربر تست', 'phone': '09', 'role': 'member'},
          })),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response.bytes(
        utf8.encode(jsonEncode({'id': 4, 'full_name': 'کاربر تست'})),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    final auth = AuthController(api);
    await auth.loginWithOtp('09120000000', '123456');
    expect(auth.state.loggedIn, isTrue);
    expect(auth.state.accessToken, 'A1');
    expect(auth.state.memberId, 4);
  });

  group('سیاست شبکه (REA 2026-11-15)', () {
    test('HTTP روی میزبان عمومی رد می‌شود', () {
      expect(
        () => ApiClient(httpClient: MockClient((_) async => http.Response('', 200)),
            baseUrl: 'http://api.example.com/api/v1'),
        throwsA(isA<InsecureBaseUrlError>()),
      );
    });

    test('HTTPS روی هر میزبانی مجاز است', () {
      final api = ApiClient(
        httpClient: MockClient((_) async => http.Response('{}', 200)),
        baseUrl: 'https://gym.example.com/api/v1',
      );
      expect(api.baseUrl, 'https://gym.example.com/api/v1');
    });

    test('بازه‌های RFC1918 مجازند', () {
      for (final host in ['10.1.2.3', '192.168.1.50', '172.16.0.9', '127.0.0.1', '10.0.2.2']) {
        final api = ApiClient(
          httpClient: MockClient((_) async => http.Response('{}', 200)),
          baseUrl: 'http://$host:8751/api/v1',
        );
        expect(api.baseUrl, contains(host));
      }
    });

    test('آدرس نامعتبر باعث خطای صریح می‌شود، نه شکست مبهم', () {
      expect(
        () => ApiClient(
            httpClient: MockClient((_) async => http.Response('', 200)), baseUrl: ''),
        throwsA(isA<ArgumentError>()),
      );
    });
  });

  test('پاسخ آرایه‌ای (فهرست) باید List برگردد نه TypeError — رگرسیون M59', () async {
    // باگ واقعی: `_decode` بدنه را همیشه `as Map` می‌کرد؛ پس هر مسیر
    // فهرستی (/classes، /shop/products، /shop/orders …) در اپ می‌شکست.
    final mock = MockClient((request) async {
      return http.Response(
        jsonEncode([
          {'id': 1, 'title': 'پروتئین وی'},
          {'id': 2, 'title': 'کراتین'},
        ]),
        200,
        headers: {'content-type': 'application/json'},
      );
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    final r = await api.get('/shop/products');
    expect(r, isA<List<dynamic>>());
    expect((r as List).length, 2);
    expect((r.first as Map)['title'], 'پروتئین وی');
  });

  test('خطای ساختاریافتهٔ بک‌اند ({"error":{"message"}}) پیام فارسی می‌دهد', () async {
    final mock = MockClient((request) async {
      return http.Response.bytes(
        utf8.encode(jsonEncode({
          'error': {'code': 'forbidden', 'message': 'فقط مالک سیستم اجازه دارد'}
        })),
        403,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://10.0.2.2:8000/api/v1');
    try {
      await api.get('/shop/products');
      fail('باید ApiException بدهد');
    } on ApiException catch (e) {
      expect(e.statusCode, 403);
      expect(e.message, 'فقط مالک سیستم اجازه دارد');
    }
  });
}
