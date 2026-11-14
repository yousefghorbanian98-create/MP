/// نشست کاربر — توکن + پروفایل واقعی (Riverpod).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class AuthState {
  const AuthState({this.accessToken, this.userId, this.userName, this.memberId});
  final String? accessToken;
  final int? userId;
  final String? userName;
  final int? memberId;
  bool get loggedIn => accessToken != null;
  AuthState copyWith({String? accessToken, int? userId, String? userName, int? memberId}) =>
      AuthState(
        accessToken: accessToken ?? this.accessToken,
        userId: userId ?? this.userId,
        userName: userName ?? this.userName,
        memberId: memberId ?? this.memberId,
      );
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._api) : super(const AuthState());
  final ApiClient _api;

  /// ورود با کد پیامکی — توکن ذخیره و پروفایل بارگیری می‌شود.
  Future<void> loginWithOtp(String phone, String code) async {
    final r = await _api.post('/auth/otp/verify', {'phone': phone, 'code': code});
    final token = r['access_token'] as String?;
    if (token == null) throw ApiException('توکن دریافت نشد');
    _api.accessToken = token;
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
    final me = await _api.get('/members/me');
    state = state.copyWith(memberId: me['id'] as int?, userName: me['full_name'] as String?);
  }

  Future<void> _persist(String token, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('mp_token', token);
    await prefs.setString('mp_refresh', refresh);
  }

  /// بازیابی نشست قبلی در شروع برنامه.
  Future<bool> restore() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('mp_token');
    final refresh = prefs.getString('mp_refresh');
    if (token == null || token.isEmpty) return false;
    _api.accessToken = token;
    state = AuthState(accessToken: token);
    try {
      final r = await _api.post('/auth/refresh', {'refresh_token': refresh ?? token});
      final t = r['access_token'] as String? ?? token;
      _api.accessToken = t;
      state = state.copyWith(accessToken: t);
      await _persist(t, r['refresh_token'] as String? ?? (refresh ?? token));
    } catch (_) {
      // refresh نامعتبر ← همان توکن قبلی امتحان می‌شود
    }
    try {
      await refreshMe();
      return true;
    } catch (_) {
      _api.accessToken = null;
      state = const AuthState();
      return false;
    }
  }
}

final authProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) => AuthController(ref.watch(apiClientProvider)),
);
