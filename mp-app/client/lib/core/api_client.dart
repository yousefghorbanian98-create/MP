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

class ApiClient {
  ApiClient({http.Client? httpClient, String? baseUrl})
      : _http = httpClient ?? http.Client(),
        baseUrl = baseUrl ??
            const String.fromEnvironment(
              'MP_API',
              defaultValue: 'http://10.0.2.2:8000/api/v1',
            );

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

  Future<Map<String, dynamic>> put(String path, Map<String, dynamic> body) async {
    final r = await _http.put(
      Uri.parse('$baseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(r);
  }

  Map<String, dynamic> _decode(http.Response r) {
    final Map<String, dynamic> data =
        r.body.isEmpty ? <String, dynamic>{} : jsonDecode(r.body) as Map<String, dynamic>;
    if (r.statusCode >= 200 && r.statusCode < 300) return data;
    final detail = data['detail'];
    final msg = detail is String
        ? detail
        : detail is Map
            ? (detail['message'] as String? ?? 'خطای سرور')
            : 'خطای سرور (${r.statusCode})';
    throw ApiException(msg, statusCode: r.statusCode);
  }
}
