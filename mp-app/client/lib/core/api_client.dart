/// کلاینت API واقعی — همهٔ داده‌ها از سرور (نه mock).
/// نشانی سرور با `--dart-define=MP_API=...` قابل تغییر است.
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

/// آدرس‌های مجاز برای HTTP بدون TLS — فقط loopback و بازه‌هایِ خصوصی RFC1918.
///
/// چرا: `network_security_config` اندروید بازهٔ IP نمی‌پذیرد و آدرس سرور باشگاه
/// در build معلوم نیست؛ پس مهار در لایهٔ اپ انجام می‌شود. هر آدرس عمومی با
/// HTTP رد می‌شود (HTTPS برای هر میزبانی مجاز است).
bool isPrivateHost(String host) {
  if (host == 'localhost' || host == '127.0.0.1' || host == '::1') return true;
  final parts = host.split('.');
  if (parts.length != 4) return false;
  final octets = parts.map(int.tryParse).toList();
  if (octets.any((o) => o == null || o < 0 || o > 255)) return false;
  final a = octets[0]!, b = octets[1]!;
  if (a == 10) return true; // 10.0.0.0/8
  if (a == 172 && b >= 16 && b <= 31) return true; // 172.16.0.0/12
  if (a == 192 && b == 168) return true; // 192.168.0.0/16
  if (a == 10 && b == 0 && octets[2] == 2) return true; // 10.0.2.2 (emulator)
  return false;
}

/// خطای پیکربندی — آدرس API با سیاست شبکه سازگار نیست.
class InsecureBaseUrlError extends ArgumentError {
  InsecureBaseUrlError(String baseUrl)
      : super(
          'آدرس API با HTTP روی میزبان عمومی مجاز نیست: $baseUrl — '
          'یا از بازهٔ LAN استفاده کنید یا HTTPS بدهید.',
        );
}

class ApiClient {
  ApiClient({http.Client? httpClient, String? baseUrl})
      : _http = httpClient ?? http.Client(),
        baseUrl = _validated(
          baseUrl ??
              const String.fromEnvironment(
                'MP_API',
                defaultValue: 'http://10.0.2.2:8000/api/v1',
              ),
        );

  /// اعتبارسنجی سیاست شبکه در زمان ساخت کلاینت (نه در اولین درخواست).
  static String _validated(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null || uri.host.isEmpty) {
      throw ArgumentError('آدرس API نامعتبر است: $url');
    }
    if (uri.scheme == 'https') return url;
    if (uri.scheme != 'http' || !isPrivateHost(uri.host)) {
      throw InsecureBaseUrlError(url);
    }
    return url;
  }

  final http.Client _http;
  final String baseUrl;
  String? accessToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (accessToken != null) 'Authorization': 'Bearer $accessToken',
      };

  Future<dynamic> get(String path) async {
    final r = await _http.get(Uri.parse('$baseUrl$path'), headers: _headers);
    return _decode(r);
  }

  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    final r = await _http.post(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(r);
  }

  Future<dynamic> put(String path, Map<String, dynamic> body) async {
    final r = await _http.put(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(r);
  }

  /// PATCH و DELETE — تا M60 در این کلاینت **نبودند**.
  ///
  /// پیامد واقعی: سرور `PATCH /shop/cart/{id}` و `DELETE /shop/cart/{id}` را
  /// داشت (با محدودیت نرخ و بررسی مالکیت) ولی اپ هیچ راهی برای صدا زدنشان
  /// نداشت؛ یعنی عضو نمی‌توانست تعداد را عوض کند یا قلمی را حذف کند و سبد
  /// فقط خواندنی بود. endpointهای بی‌مصرف، همان باگ «کد مرده» هستند.
  Future<dynamic> patch(String path, Map<String, dynamic> body) async {
    final r = await _http.patch(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(r);
  }

  Future<dynamic> delete(String path) async {
    final r = await _http.delete(Uri.parse('$baseUrl$path'), headers: _headers);
    return _decode(r);
  }

  /// رمزگشایی پاسخ — **هم شیء و هم آرایه**.
  ///
  /// باگ واقعی (M59): نسخهٔ پیشین بدنه را همیشه `as Map<String, dynamic>`
  /// می‌کرد. هر مسیری که آرایه برمی‌گرداند (`/classes`، `/shop/products`،
  /// `/shop/orders`، `/axis-assessments/...`) در اپ با TypeError می‌شکست —
  /// و چون هیچ تستی این کلاینت را روی پاسخ آرایه‌ای نمی‌سنجید، سه صفحه
  /// «کار می‌کرد» ولی همیشه خطا می‌داد. تست `api_client_test` این را قفل
  /// می‌کند.
  dynamic _decode(http.Response r) {
    final dynamic decoded = r.body.isEmpty ? null : jsonDecode(r.body);
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return decoded ?? <String, dynamic>{};
    }
    // خطای ساختاریافتهٔ بک‌اند: {"error": {"code","message"}} (قالب پروژه)
    // و قالب قدیمی FastAPI: {"detail": ...}. هر دو پشتیبانی می‌شوند تا
    // پیام فارسی سرور به کاربر برسد، نه «خطای سرور (۴۰۳)».
    String msg = 'خطای سرور (${r.statusCode})';
    if (decoded is Map) {
      final err = decoded['error'];
      if (err is Map && err['message'] is String) {
        msg = err['message'] as String;
      } else if (decoded['detail'] is String) {
        msg = decoded['detail'] as String;
      } else if (decoded['detail'] is Map && decoded['detail']['message'] is String) {
        msg = decoded['detail']['message'] as String;
      }
    }
    throw ApiException(msg, statusCode: r.statusCode);
  }
}
