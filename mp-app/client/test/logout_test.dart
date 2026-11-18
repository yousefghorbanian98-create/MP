/// M61 / D3 — خروج از حساب، که اصلاً وجود نداشت.
///
/// اثبات باگ: `grep -rniE "logout|signout|خروج از حساب" client/lib studio/src`
/// صفر نتیجه داشت، و هیچ‌جای اپ توکن را پاک نمی‌کرد. توکن دسترسی ۳۰ دقیقه
/// اعتبار دارد و refresh ۱۴ روز؛ روی گوشی مشترک باشگاه، «خروج» تنها راه
/// قطع دسترسی است. بدون آن، کاربر فقط با پاک‌کردن اپ می‌توانست خارج شود.
///
/// این تست قفل می‌کند که خروج:
///   ۱) توکن و refresh را از حافظهٔ دستگاه حذف می‌کند
///   ۲) مسیر سرور (`POST /auth/logout`) را با refresh token صدا می‌زند تا
///      نشست سمت سرور هم باطل شود (نه فقط پاک‌کردن محلی)
///   ۳) وضعیت احراز را خالی می‌کند
///   ۴) اگر سرور خطا داد، **خروج محلی همچنان انجام می‌شود** — کاربر نباید
///      وقتی سرور در دسترس نیست در حساب خودش زندانی شود
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/api_client.dart';
import 'package:mp_client/core/session.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeClient extends http.BaseClient {
  _FakeClient({this.failLogout = false});

  final bool failLogout;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    if (path == '/auth/logout' && failLogout) {
      return http.StreamedResponse(
        Stream.value(utf8.encode('{"error":{"message":"x"}}')),
        500,
        headers: {'content-type': 'application/json'},
        request: request,
      );
    }
    final bytes = jsonEncode({'ok': true}).codeUnits;
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({
      'mp_token': 'access-1',
      'mp_refresh': 'refresh-1',
    });
  });

  test('خروج، توکن‌ها را پاک می‌کند و نشست سرور را می‌بندد', () async {
    final http_ = _FakeClient();
    final api = ApiClient(httpClient: http_)..accessToken = 'access-1';
    final auth = AuthController(api, refreshToken: 'refresh-1');
    // وضعیت «وارد شده» را از مسیر واقعی می‌سازیم
    await auth.restore();
    expect(auth.state.loggedIn, isTrue);

    await auth.logout();

    expect(auth.state.loggedIn, isFalse);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('mp_token'), isNull);
    expect(prefs.getString('mp_refresh'), isNull);
    expect(
      http_.calls.contains('POST /auth/logout'),
      isTrue,
      reason: 'پاک‌کردن محلی کافی نیست؛ نشست سمت سرور هم باید باطل شود',
    );
  });

  test('اگر سرور در دسترس نباشد، خروج محلی انجام می‌شود', () async {
    final http_ = _FakeClient(failLogout: true);
    final api = ApiClient(httpClient: http_)..accessToken = 'access-1';
    final auth = AuthController(api, refreshToken: 'refresh-1');
    await auth.restore();

    await auth.logout();

    expect(
      auth.state.loggedIn,
      isFalse,
      reason: 'کاربر نباید با خطای سرور در حساب خودش زندانی شود',
    );
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('mp_token'), isNull);
  });
}
