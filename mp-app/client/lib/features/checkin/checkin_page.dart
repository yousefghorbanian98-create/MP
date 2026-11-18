/// چک‌این واقعی — QR امضاشده + چهره (ثبت/چک‌این از API) (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'member_checkin_history.dart';

final qrTokenProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/face/qr-token');
  return Map<String, dynamic>.from(r as Map);
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
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 3, vsync: this);
  String? _faceMessage;
  bool _busy = false;
  int _historyVersion = 0;

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  // M61/D1+D2 — دو واقعیتی که این صفحه تا امروز پنهان می‌کرد:
  //   ۱) `POST /face/enroll` ورودی‌اش `embedding_b64` است (خروجی مدل چهره)، نه
  //      تصویر خام. ساخت این embedding در کلاینت نیست، پس دکمهٔ «ثبت چهره» در
  //      اپ **نمی‌توانست** کار کند — یا ۴۰۳ می‌گرفت (rbac) یا در بهترین حالت
  //      ورودی بی‌معنا می‌فرستاد. قاعدهٔ R3: هر دکمه‌ای که کاربر واقعاً نمی‌تواند
  //      انجامش دهد باید حذف شود، نه اینکه پیام خطا نشان دهد.
  //   ۲) ثبت چهره از کیوسک/پذیرش انجام می‌شود؛ اپ فقط رضایت و چک‌این دارد.

  Future<void> _faceCheckIn() async {
    setState(() {
      _busy = true;
      _faceMessage = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final auth = ref.read(authProvider);
      final memberId = auth.memberId;
      if (memberId == null)
        throw ApiException('عضو یافت نشد — دوباره وارد شوید');
      final r = Map<String, dynamic>.from(
        await api.post('/face/checkin', {
          'member_id': memberId,
          'method': 'face',
        }) as Map,
      );
      final denied = r['result'] == 'denied';
      setState(() {
        _faceMessage = denied
            ? 'ورود ثبت نشد: ${_denialLabel(r['denial_reason'] as String?)}'
            : '✅ ورود ثبت شد';
        _historyVersion += 1;
      });
      ref.invalidate(qrTokenProvider);
      ref.invalidate(memberCheckInHistoryProvider(0));
    } catch (e) {
      setState(() => _faceMessage = '⚠ $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  static String _denialLabel(String? reason) => switch (reason) {
        'membership_expired' => 'اشتراک فعال ندارید یا منقضی شده است',
        null => 'دلیل نامعلوم',
        _ => reason,
      };

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
    final qr = ref.watch(qrTokenProvider);
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
                  child: qr.when(
                    loading: () => const CircularProgressIndicator(),
                    error: (e, _) => Text('خطا: $e'),
                    data: (t) => GlassCard(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text(
                            'برای ورود نشان دهید',
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
                          Text(
                            'عضو شمارهٔ ${t['member_id']}',
                            style: TextStyle(color: MpColors.textSecondary),
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
                          'ورود شما ثبت می‌شود. تشخیص چهره در این نسخه انجام نمی‌شود؛ '
                          'هویت شما با حساب واردشده تأیید می‌شود.',
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
                                    'برای استفاده از ورود با چهره، ابتدا باید رضایت بیومتریک بدهید.',
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
                                FilledButton.icon(
                                  onPressed: _busy ? null : _faceCheckIn,
                                  icon: const Icon(Icons.login),
                                  label: const Text('چک‌این'),
                                ),
                                const SizedBox(height: 10),
                                Text(
                                  'ثبت چهره در باشگاه و توسط پذیرش انجام می‌شود.',
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
                MemberCheckInHistoryPage(key: ValueKey(_historyVersion)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
