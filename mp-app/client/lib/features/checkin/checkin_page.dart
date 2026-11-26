/// حضور عضو — QR یک‌بارمصرف امضاشده؛ چک‌این چهره تا اثبات سمت‌سرور غیرفعال است.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:local_auth/local_auth.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'member_checkin_history.dart';

final qrTokenProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/face/qr-token');
  return Map<String, dynamic>.from(r as Map);
});

/// Replaceable in widget tests; device credentials are intentionally not a fallback.
final qrBiometricProvider = Provider<Future<bool> Function()>((ref) {
  final auth = LocalAuthentication();
  return () => auth.authenticate(
        localizedReason: 'برای نمایش کد ورود احراز هویت کنید',
        options: const AuthenticationOptions(biometricOnly: true),
      );
});

/// متن اطلاعیهٔ حریم خصوصی بیومتریک — از سرور، نه متن ثابت در اپ.
///
/// M61/D6: گیت «هیچ مسیر دکوراتیو» ادعا می‌کرد «نسخهٔ متنی در اپ Dart» هست،
/// در حالی که `grep privacy-notice client/lib` صفر ارجاع داشت. طبق US-108،
/// کاربر باید متن را **قبل از** رضایت ببیند؛ اکنون همان متن سرور نمایش
/// داده می‌شود تا متن اپ و سرور هرگز از هم جدا نشوند.
final privacyNoticeProvider = FutureProvider<String>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/face/privacy-notice');
  if (r is Map && r['text'] is String) return r['text'] as String;
  if (r is String) return r;
  return 'متن اطلاعیه در دسترس نیست.';
});

/// وضعیت رضایت بیومتریک + ثبت چهرهٔ خودِ عضو.
///
/// M61/D1: دکمهٔ «ثبت چهره» بدون این پرسش، همیشه ۴۰۳ می‌گرفت و کاربر دلیلش
/// را نمی‌فهمید. سرور بدون رضایت صریح اجازهٔ ثبت نمی‌دهد (`_has_active_consent`)
/// — درست است — پس UI باید **قبل از کلیک** بگوید چه لازم است.
final faceConsentProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/members/me/face-consent');
  return Map<String, dynamic>.from(r as Map);
});

class CheckInPage extends ConsumerStatefulWidget {
  const CheckInPage({super.key});

  @override
  ConsumerState<CheckInPage> createState() => _CheckInPageState();
}

class _CheckInPageState extends ConsumerState<CheckInPage>
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  late final TabController _tabs = TabController(length: 3, vsync: this);
  String? _faceMessage;
  bool _busy = false;
  bool _qrUnlocked = false;
  bool _qrAuthenticating = false;
  String? _qrError;
  Timer? _qrTimer;
  int _qrGeneration = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  void _hideQr() {
    _qrGeneration++;
    _qrTimer?.cancel();
    if (mounted) setState(() => _qrUnlocked = false);
    ref.invalidate(qrTokenProvider);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.hidden ||
        state == AppLifecycleState.detached) {
      _hideQr();
    }
  }

  Future<void> _unlockQr() async {
    final generation = ++_qrGeneration;
    setState(() {
      _qrAuthenticating = true;
      _qrError = null;
    });
    try {
      final ok = await ref.read(qrBiometricProvider)();
      if (!mounted || generation != _qrGeneration) return;
      if (!ok) {
        setState(() => _qrError = 'احراز هویت بیومتریک تأیید نشد.');
        return;
      }
      ref.invalidate(qrTokenProvider);
      setState(() => _qrUnlocked = true);
      _qrTimer?.cancel();
      _qrTimer = Timer(const Duration(seconds: 30), _hideQr);
    } catch (_) {
      if (mounted && generation == _qrGeneration) {
        setState(() => _qrError = 'احراز هویت بیومتریک در دسترس نیست.');
      }
    } finally {
      if (mounted) setState(() => _qrAuthenticating = false);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _qrTimer?.cancel();
    _tabs.dispose();
    super.dispose();
  }

  // Face enrollment/matching has no verified server-side probe or liveness flow.
  // Do not turn an authenticated account request into a method=face check-in;
  // the signed, one-time QR flow is the supported attendance path.

  Future<void> _grantConsent() async {
    setState(() => _busy = true);
    try {
      final api = ref.read(apiClientProvider);
      final auth = ref.read(authProvider);
      await api.post('/face/consent', {'member_id': auth.memberId});
      ref.invalidate(faceConsentProvider);
      setState(() => _faceMessage = '✅ رضایت ثبت شد');
    } catch (e) {
      setState(() => _faceMessage = '⚠ $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final qr = _qrUnlocked ? ref.watch(qrTokenProvider) : null;
    final consent = ref.watch(faceConsentProvider);
    return SafeArea(
      child: Column(
        children: [
          TabBar(
            controller: _tabs,
            indicatorColor: MpColors.primary,
            labelColor: MpColors.primary,
            tabs: const [
              Tab(text: 'QR ورود'),
              Tab(text: 'چهره'),
              Tab(text: 'سوابق'),
            ],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabs,
              children: [
                // ── QR ──
                Center(
                  child: qr == null
                      ? GlassCard(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                  'برای نمایش QR احراز هویت بیومتریک لازم است'),
                              if (_qrError != null) Text(_qrError!),
                              ElevatedButton(
                                onPressed: _qrAuthenticating ? null : _unlockQr,
                                child: const Text('نمایش QR'),
                              ),
                            ],
                          ),
                        )
                      : qr.when(
                          loading: () => const CircularProgressIndicator(),
                          error: (e, _) => Text('خطا: $e'),
                          data: (t) => GlassCard(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Text(
                                  'QR یک‌بارمصرف برای پذیرش',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 14),
                                QrImageView(
                                  data: t['payload'] as String? ?? '',
                                  size: 220,
                                  backgroundColor: Colors.white,
                                )
                                    .animate()
                                    .scale(
                                      begin: const Offset(0.9, 0.9),
                                      duration: 400.ms,
                                      curve: Curves.easeOutBack,
                                    )
                                    .fadeIn(),
                                const SizedBox(height: 12),
                                const Text(
                                  'نمایش QR به‌تنهایی حضور را ثبت نمی‌کند.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(fontSize: 12, height: 1.5),
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  'عضو شمارهٔ ${t['member_id']}',
                                  style:
                                      TextStyle(color: MpColors.textSecondary),
                                ),
                              ],
                            ),
                          ),
                        ),
                ),
                // ── چهره ──
                Center(
                  child: GlassCard(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.face_retouching_natural,
                          size: 56,
                          color: MpColors.primary,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'چک‌این با چهره',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'تطبیق چهره و بررسی زنده‌بودن در سرور این نسخه پیاده نشده است؛ '
                          'چک‌این با این روش غیرفعال است. برای حضور، QR یک‌بارمصرف در تب '
                          '«QR ورود» مسیر پشتیبانی‌شدهٔ عضو است. صفحهٔ پذیرش Studio در این نسخه '
                          'رابط اسکن QR ندارد؛ از پذیرش دربارهٔ روش ثبت حضور جایگزین بپرسید.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: MpColors.textSecondary,
                            height: 1.6,
                          ),
                        ),
                        const SizedBox(height: 16),
                        consent.when(
                          loading: () => const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8),
                            child: SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          error: (e, _) => Text(
                            'وضعیت رضایت خوانده نشد: $e',
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 12),
                          ),
                          data: (c) {
                            final hasConsent = c['consent'] == true;
                            if (!hasConsent) {
                              final notice = ref.watch(privacyNoticeProvider);
                              return Column(
                                children: [
                                  Text(
                                    'رضایت برای ثبت قالب بیومتریک لازم است؛ '
                                    'این رضایت چک‌این با چهره را فعال نمی‌کند.',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      color: MpColors.accent,
                                      fontSize: 12,
                                      height: 1.6,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  // متن از سرور می‌آید (US-108: اطلاع قبل از رضایت)
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: MpColors.surface.withOpacity(0.6),
                                      borderRadius: BorderRadius.circular(10),
                                    ),
                                    child: Text(
                                      notice.valueOrNull ??
                                          'در حال دریافت متن اطلاعیه…',
                                      style: TextStyle(
                                        fontSize: 11,
                                        height: 1.7,
                                        color: MpColors.textSecondary,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(height: 10),
                                  FilledButton.icon(
                                    onPressed: _busy ? null : _grantConsent,
                                    icon: const Icon(Icons.verified_user),
                                    label: const Text('رضایت می‌دهم'),
                                  ),
                                ],
                              );
                            }
                            return Column(
                              children: [
                                Text(
                                  c['enrolled'] == true
                                      ? 'رضایت فعال است و قالب چهره ثبت شده.'
                                      : 'رضایت فعال است؛ ثبت قالب چهره در باشگاه '
                                          'و توسط پذیرش انجام می‌شود.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: MpColors.textSecondary,
                                    fontSize: 11.5,
                                    height: 1.6,
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
                        if (_busy) ...[
                          const SizedBox(height: 14),
                          const CircularProgressIndicator(),
                        ],
                        if (_faceMessage != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            _faceMessage!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 13),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const MemberCheckInHistoryPage(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
