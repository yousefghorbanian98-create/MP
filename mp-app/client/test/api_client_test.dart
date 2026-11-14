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
    final api = ApiClient(httpClient: mock, baseUrl: 'http://test/api/v1');
    api.accessToken = 'tok-123';
    final r = await api.get('/members/me');
    expect(r['id'], 7);
    expect(seen.headers['Authorization'], 'Bearer tok-123');
    expect(seen.url.toString(), 'http://test/api/v1/members/me');
  });

  test('خطای سرور با پیام فارسی detail بالا می‌آید', () async {
    final mock = MockClient((request) async {
      return http.Response(jsonEncode({'detail': 'کاربر فعال نیست'}), 401);
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://test/api/v1');
    expect(
      () => api.get('/members/me'),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', 'کاربر فعال نیست')),
    );
  });

  test('POST بدنهٔ JSON می‌فرستد', () async {
    late String body;
    final mock = MockClient((request) async {
      body = await request.readAsString();
      return http.Response(jsonEncode({'ok': true}), 200);
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://test/api/v1');
    await api.post('/ai/program/generate', {'member_id': 3, 'goal': 'fitness'});
    expect(jsonDecode(body)['member_id'], 3);
  });

  test('AuthController ورود OTP توکن را نگه می‌دارد', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    final mock = MockClient((request) async {
      if (request.url.path.endsWith('/otp/verify')) {
        return http.Response(
          jsonEncode({
            'access_token': 'A1',
            'refresh_token': 'R1',
            'user': {'id': 9, 'full_name': 'کاربر تست', 'phone': '09', 'role': 'member'},
          }),
          200,
        );
      }
      return http.Response(jsonEncode({'id': 4, 'full_name': 'کاربر تست'}), 200);
    });
    final api = ApiClient(httpClient: mock, baseUrl: 'http://test/api/v1');
    final auth = AuthController(api);
    await auth.loginWithOtp('09120000000', '123456');
    expect(auth.state.loggedIn, isTrue);
    expect(auth.state.accessToken, 'A1');
    expect(auth.state.memberId, 4);
  });
}
