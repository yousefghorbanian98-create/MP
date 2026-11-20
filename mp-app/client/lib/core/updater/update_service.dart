/// سرویس آپدیت تفاضلی فلاتر (M20) — artifact: در CI با SDK واقعی اجرا می‌شود.
///
/// جریان: بررسی مانیفست ← انتخاب delta/full ← دانلود ← تأیید sha256 ← اعمال.
/// اعمال patch باینری به native وابسته است (bsdiff) — fallback: دانلود full.
library;

import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;

class UpdateManifest {
  const UpdateManifest({
    required this.updateAvailable,
    required this.latest,
    required this.current,
    required this.force,
    required this.mode,
    this.patchUrl,
    this.patchSha256,
    this.fullUrl,
  });

  final bool updateAvailable;
  final String latest;
  final String current;
  final bool force;
  final String mode; // delta | full
  final String? patchUrl;
  final String? patchSha256;
  final String? fullUrl;

  factory UpdateManifest.fromJson(Map<String, dynamic> j) {
    final patch = (j['patch'] as Map<String, dynamic>?) ?? const {};
    final full = (j['full'] as Map<String, dynamic>?) ?? const {};
    return UpdateManifest(
      updateAvailable: j['update_available'] == true,
      latest: j['latest'] as String? ?? '',
      current: j['current'] as String? ?? '',
      force: j['force'] == true,
      mode: j['mode'] as String? ?? 'full',
      patchUrl: patch['url'] as String?,
      patchSha256: patch['sha256'] as String?,
      fullUrl: full['url'] as String?,
    );
  }
}

class UpdateService {
  UpdateService({
    required this.baseUrl,
    required this.platform,
    required this.currentVersion,
  });

  final String baseUrl;
  final String platform; // android
  final String currentVersion;

  /// بررسی مانیفست — قطعی و بدون side-effect.
  Future<UpdateManifest> check() async {
    final resp = await http.get(
      Uri.parse(
        '$baseUrl/updates/manifest?platform=$platform&current=$currentVersion',
      ),
    );
    if (resp.statusCode != 200) {
      throw UpdateException('خطای بررسی نسخه: ${resp.statusCode}');
    }
    return UpdateManifest.fromJson(
      jsonDecode(resp.body) as Map<String, dynamic>,
    );
  }

  /// دانلود patch با تأیید یکپارچگی sha256 — در صورت شکست، full جایگزین می‌شود.
  ///
  /// `save` فایل را در محل مخصوص هر پلتفرم ذخیره می‌کند؛ این کلاس به `dart:io`
  /// وابسته نیست تا build وب (Flutter Web) کامپایل شود.
  /// برمی‌گرداند: نام فایلی که ذخیره شد.
  Future<String> downloadVerified(
    String url,
    String expectedSha256,
    Future<void> Function(String fileName, List<int> bytes) save,
  ) async {
    final resp = await http.get(Uri.parse('$baseUrl$url'));
    final bytes = resp.bodyBytes;
    final digest = sha256.convert(bytes).toString();
    if (digest != expectedSha256) {
      throw const FormatException('هش فایل ناسازگار — دانلود مجدد لازم است');
    }
    final fileName = url.split('/').last;
    await save(fileName, bytes);
    return fileName;
  }
}

/// خطای بررسی/دانلود بروزرسانی (جایگزین `HttpException` از dart:io).
class UpdateException implements Exception {
  const UpdateException(this.message);
  final String message;

  @override
  String toString() => message;
}

/// مقایسهٔ نسخه — همگام با backend (قطعی).
bool isVersionNewer(String candidate, String current) {
  List<int> parse(String v) {
    final parts = v
        .trim()
        .split('.')
        .map((c) => int.tryParse(c.replaceAll(RegExp(r'[^0-9]'), '')) ?? 0)
        .toList();
    while (parts.length < 3) {
      parts.add(0);
    }
    return parts.sublist(0, 3);
  }

  final a = parse(candidate);
  final b = parse(current);
  for (var i = 0; i < 3; i++) {
    if (a[i] != b[i]) return a[i] > b[i];
  }
  return false;
}
