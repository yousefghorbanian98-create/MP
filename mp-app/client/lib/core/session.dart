/// نشست کاربر — توکن + پروفایل واقعی (Riverpod).
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'offline_feedback_outbox.dart';

/// نقطهٔ تزریق HTTP — تست‌ها فقط این را override می‌کنند.
/// چرا جدا از `apiClientProvider`: سازندهٔ `ApiClient` آدرس را اعتبارسنجی
/// می‌کند و در تست باید همان مسیر تولیدی طی شود، نه یک کلاینت دست‌ساز.
final httpClientProvider = Provider<http.Client>((ref) => http.Client());

final Provider<ApiClient> apiClientProvider = Provider<ApiClient>((ref) {
  final api = ApiClient(httpClient: ref.watch(httpClientProvider));
  // M62/D10 — نشست باید وسط اجرا هم قابل تمدید باشد. تا امروز `restore()`
  // فقط یک‌بار در `main()` صدا زده می‌شد و توکن ۳۰ دقیقه‌ای وسط تمرین
  // می‌مُرد؛ یعنی هر صفحه خطا می‌داد تا کاربر اپ را ببندد و باز کند.
  api.attachSession(
    refresher: () => ref.read(authProvider.notifier).refreshAccessToken(),
    onSessionLost: () => ref.read(authProvider.notifier).markSessionLost(),
  );
  return api;
});

class AuthState {
  const AuthState({
    this.accessToken,
    this.userId,
    this.userName,
    this.memberId,
  });
  final String? accessToken;
  final int? userId;
  final String? userName;
  final int? memberId;
  bool get loggedIn => accessToken != null;
  AuthState copyWith({
    String? accessToken,
    int? userId,
    String? userName,
    int? memberId,
  }) => AuthState(
    accessToken: accessToken ?? this.accessToken,
    userId: userId ?? this.userId,
    userName: userName ?? this.userName,
    memberId: memberId ?? this.memberId,
  );
}

class PendingOfflineFeedbackException implements Exception {
  const PendingOfflineFeedbackException(this.count);
  final int count;
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(
    this._api, {
    String? refreshToken,
    OfflineFeedbackLocalStore? offlineStore,
  }) : _refreshToken = refreshToken,
       _offlineStore = offlineStore,
       super(const AuthState());

  /// refresh token در حافظه نگه داشته می‌شود تا خروج بتواند نشست **سرور** را
  /// هم ببندد (`POST /auth/logout`). نسخهٔ قبلی فقط access token را می‌شناخت.
  String? _refreshToken;

  /// سازندهٔ تست — وضعیت اولیه را مستقیم می‌دهد.
  ///
  /// چرا: بدون این، تست ویجت مجبور بود OTP واقعی را طی کند تا به وضعیت
  /// «وارد شده» برسد، یا با `overrideWith` نسخهٔ جعلی بسازد که هیچ رفتار
  /// واقعی ندارد. یک سازندهٔ صریح، تست را صادق نگه می‌دارد.
  @visibleForTesting
  AuthController.test(
    AuthState initial, {
    OfflineFeedbackLocalStore? offlineStore,
  }) : _api = null,
       _offlineStore = offlineStore,
       super(initial);
  final ApiClient? _api;
  final OfflineFeedbackLocalStore? _offlineStore;

  /// ورود با کد پیامکی — توکن ذخیره و پروفایل بارگیری می‌شود.
  Future<void> loginWithOtp(String phone, String code) async {
    final api = _api ?? (throw StateError('Authentication API is unavailable'));
    // `_decode` نوع بدنه را نگه می‌دارد (Map/List) — پس اینجا صریح تبدیل می‌کنیم
    final r = Map<String, dynamic>.from(
      await api.post('/auth/otp/verify', {'phone': phone, 'code': code}) as Map,
    );
    final token = r['access_token'] as String?;
    if (token == null) throw ApiException('توکن دریافت نشد');
    api.accessToken = token;
    final user = r['user'] as Map<String, dynamic>?;
    state = AuthState(
      accessToken: token,
      userId: user?['id'] as int?,
      userName: user?['full_name'] as String?,
    );
    await _persist(token, r['refresh_token'] as String? ?? token);
    await refreshMe();
  }

  Future<void> refreshMe() async {
    final api = _api ?? (throw StateError('Authentication API is unavailable'));
    final me = Map<String, dynamic>.from(await api.get('/members/me') as Map);
    state = state.copyWith(
      memberId: me['id'] as int?,
      userName: me['full_name'] as String?,
    );
  }

  Future<void> _persist(String token, String refresh) async {
    _refreshToken = refresh;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('mp_token', token);
    await prefs.setString('mp_refresh', refresh);
  }

  /// تمدید توکن دسترسی در میانهٔ کار — مصرف‌کنندهٔ `ApiClient.attachSession`.
  ///
  /// `true` یعنی «توکن تازه گرفتم، درخواست را دوباره بفرست». اگر refresh
  /// موجود نباشد یا سرور رد کند، `false` و نشست منقضی اعلام می‌شود.
  Future<bool> refreshAccessToken() async {
    final api = _api;
    final refresh = _refreshToken;
    if (api == null || refresh == null) return false;
    try {
      final r = Map<String, dynamic>.from(
        await api.post('/auth/refresh', {'refresh_token': refresh}) as Map,
      );
      final token = r['access_token'] as String?;
      if (token == null) return false;
      api.accessToken = token;
      state = state.copyWith(accessToken: token);
      await _persist(token, r['refresh_token'] as String? ?? refresh);
      return true;
    } catch (_) {
      return false;
    }
  }

  /// نشست از دست رفت (refresh هم رد شد) — وضعیت خالی، تا UI به ورود ببرد.
  void markSessionLost() {
    _api?.accessToken = null;
    _refreshToken = null;
    state = const AuthState();
  }

  /// خروج — نشست سرور بسته می‌شود، سپس حافظهٔ دستگاه پاک.
  ///
  /// M61/D3: این متد اصلاً وجود نداشت؛ `POST /auth/logout` صفر مصرف‌کننده بود و
  /// روی گوشی مشترک باشگاه هیچ راهی برای قطع دسترسی نبود.
  ///
  /// دو نکتهٔ عمدی:
  ///   • ترتیب: **اول** سرور، **بعد** پاک‌کردن محلی. اگر برعکس بود، refresh token
  ///     از دست می‌رفت و نشست سرور تا ۱۴ روز زنده می‌ماند.
  ///   • خطای شبکه خروج محلی را متوقف **نمی‌کند** — کاربر نباید وقتی سرور در
  ///     دسترس نیست در حساب خودش زندانی شود. ولی خطا بی‌صدا هم نمی‌ماند:
  ///     `serverRevoked` می‌گوید نشست سرور بسته شد یا نه.
  Future<bool> logout({
    bool keepPendingFeedback = false,
    bool discardPendingFeedback = false,
  }) async {
    if (keepPendingFeedback && discardPendingFeedback) {
      throw ArgumentError(
        'Choose either keep or discard for the offline feedback queue.',
      );
    }
    final ownerMemberId = state.memberId;
    final offlineStore = _offlineStore;
    if (offlineStore != null &&
        offlineStore.isSupported &&
        ownerMemberId != null) {
      final unresolved = await offlineStore.countUnresolved(ownerMemberId);
      if (unresolved > 0 && !keepPendingFeedback && !discardPendingFeedback) {
        throw PendingOfflineFeedbackException(unresolved);
      }
      if (unresolved > 0 && discardPendingFeedback) {
        await offlineStore.discardOwner(ownerMemberId);
      }
    }
    var serverRevoked = false;
    final api = _api;
    final refresh = _refreshToken;
    if (api != null && refresh != null) {
      try {
        await api.post('/auth/logout', {'refresh_token': refresh});
        serverRevoked = true;
      } catch (_) {
        // عمداً بلعیده می‌شود — پایین توضیح داده شده
      }
    }
    _api?.accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('mp_token');
    await prefs.remove('mp_refresh');
    state = const AuthState();
    return serverRevoked;
  }

  /// بازیابی نشست قبلی در شروع برنامه.
  Future<bool> restore() async {
    final api = _api ?? (throw StateError('Authentication API is unavailable'));
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('mp_token');
    final refresh = prefs.getString('mp_refresh');
    if (token == null || token.isEmpty) return false;
    api.accessToken = token;
    state = AuthState(accessToken: token);
    try {
      final r = Map<String, dynamic>.from(
        await api.post('/auth/refresh', {'refresh_token': refresh ?? token})
            as Map,
      );
      final t = r['access_token'] as String? ?? token;
      api.accessToken = t;
      state = state.copyWith(accessToken: t);
      await _persist(t, r['refresh_token'] as String? ?? (refresh ?? token));
    } catch (_) {
      // refresh نامعتبر ← همان توکن قبلی امتحان می‌شود، ولی برای خروج باید
      // همان refresh را بشناسیم تا `POST /auth/logout` بتواند نشست را ببندد.
      _refreshToken = refresh;
    }
    try {
      await refreshMe();
      return true;
    } catch (_) {
      api.accessToken = null;
      state = const AuthState();
      return false;
    }
  }
}

final authProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(
    ref.watch(apiClientProvider),
    offlineStore: ref.watch(offlineFeedbackStoreProvider),
  ),
);

/// خروج از حساب — برای دکمه‌های UI.
///
/// چرا provider جدا: تست‌های ویجت باید بتوانند مسیر واقعی `logout` را
/// بسنجند بدون اینکه به `StateNotifierProvider` دست بزنند.
final logoutProvider = Provider<Future<bool> Function()>((ref) {
  return () => ref.read(authProvider.notifier).logout();
});
