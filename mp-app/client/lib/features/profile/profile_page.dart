/// پروفایل واقعی کاربر — داده از `/members/me` + ویرایش زنده (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/offline_feedback_outbox.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'phone_change_dialog.dart';

enum _PendingQueueExitChoice { none, cancel, keep, discard }

Future<_PendingQueueExitChoice> _confirmPendingFeedbackExit(
  BuildContext context,
  WidgetRef ref,
  int? ownerMemberId,
) async {
  final store = ref.read(offlineFeedbackStoreProvider);
  if (ownerMemberId == null || !store.isSupported)
    return _PendingQueueExitChoice.none;
  late final int count;
  try {
    count = await store.countUnresolved(ownerMemberId);
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'وضعیت صف محلی خوانده نشد؛ برای ایمنی خروج/تغییر شماره لغو شد.',
          ),
        ),
      );
    }
    return _PendingQueueExitChoice.cancel;
  }
  if (count == 0) return _PendingQueueExitChoice.none;
  if (!context.mounted) return _PendingQueueExitChoice.cancel;

  final choice = await showDialog<_PendingQueueExitChoice>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('بازخورد همگام‌نشده'),
      content: Text(
        '$count مورد هنوز روی دستگاه است. اگر صف را نگه دارید، فقط پس از ورود دوباره به همین حساب قابل ارسال است؛ حساب دیگر آن را نمی‌بیند. می‌توانید به صفحهٔ برنامه برگردید و sync کنید یا صف را صریحاً حذف کنید.',
      ),
      actions: [
        TextButton(
          onPressed: () =>
              Navigator.pop(dialogContext, _PendingQueueExitChoice.cancel),
          child: const Text('انصراف'),
        ),
        TextButton(
          onPressed: () =>
              Navigator.pop(dialogContext, _PendingQueueExitChoice.keep),
          child: const Text('خروج با نگه‌داشتن صف'),
        ),
        TextButton(
          style: TextButton.styleFrom(foregroundColor: Colors.redAccent),
          onPressed: () =>
              Navigator.pop(dialogContext, _PendingQueueExitChoice.discard),
          child: const Text('حذف صف'),
        ),
      ],
    ),
  );
  if (choice != _PendingQueueExitChoice.discard || !context.mounted) {
    return choice ?? _PendingQueueExitChoice.cancel;
  }
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('حذف قطعی صف؟'),
      content: const Text(
        'این داده‌ها برای همیشه از این دستگاه پاک می‌شوند و به سرور نمی‌رسند.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialogContext, false),
          child: const Text('بازگشت'),
        ),
        FilledButton(
          style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
          onPressed: () => Navigator.pop(dialogContext, true),
          child: const Text('حذف قطعی و ادامه'),
        ),
      ],
    ),
  );
  return confirmed == true
      ? _PendingQueueExitChoice.discard
      : _PendingQueueExitChoice.cancel;
}

final meProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/members/me');
  return Map<String, dynamic>.from(r as Map);
});

class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  final _name = TextEditingController();
  final _height = TextEditingController();
  String _goal = '';
  String _gender = 'unknown';
  bool _editing = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _height.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      await api.put('/members/me', {
        'full_name': _name.text.trim(),
        'goal': _goal,
        'gender': _gender,
        if (_height.text.trim().isNotEmpty)
          'height_cm': int.tryParse(_height.text.trim()),
      });
      ref.invalidate(meProvider);
      await ref.read(authProvider.notifier).refreshMe();
      setState(() => _editing = false);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _changePhone(String currentPhone) async {
    final queueChoice = await _confirmPendingFeedbackExit(
      context,
      ref,
      ref.read(authProvider).memberId,
    );
    if (queueChoice == _PendingQueueExitChoice.cancel || !mounted) return;
    final changed = await showDialog<bool>(
      context: context,
      builder: (_) => PhoneChangeDialog(currentPhone: currentPhone),
    );
    if (changed != true || !mounted) return;

    // The server revoked every session with the phone update. The queue choice
    // was made before the change; preserve or discard is applied only now.
    try {
      await ref
          .read(authProvider.notifier)
          .logout(
            keepPendingFeedback: queueChoice == _PendingQueueExitChoice.keep,
            discardPendingFeedback:
                queueChoice == _PendingQueueExitChoice.discard,
          );
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('خروج امن انجام نشد؛ وضعیت صف محلی بررسی شود.'),
          ),
        );
      }
      return;
    }
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'شماره عوض شد؛ برای امنیت با شمارهٔ جدید دوباره وارد شوید.',
        ),
      ),
    );
    context.go('/otp');
  }

  @override
  Widget build(BuildContext context) {
    final me = ref.watch(meProvider);
    return SafeArea(
      child: me.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'خطا در دریافت پروفایل: $e',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.redAccent),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () => ref.invalidate(meProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
          ),
        ),
        data: (m) {
          _name.text = _editing
              ? _name.text
              : (m['full_name'] as String? ?? '');
          _height.text = _editing
              ? _height.text
              : ((m['height_cm'] as int?)?.toString() ?? '');
          _goal = _editing ? _goal : (m['goal'] as String? ?? '');
          _gender = _editing ? _gender : (m['gender'] as String? ?? 'unknown');
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Center(
                    child: Column(
                      children: [
                        Container(
                          width: 96,
                          height: 96,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: LinearGradient(
                              colors: [
                                MpColors.primary,
                                MpColors.primary.withOpacity(0.5),
                              ],
                              begin: Alignment.topRight,
                              end: Alignment.bottomLeft,
                            ),
                          ),
                          child: const Icon(
                            Icons.person,
                            size: 48,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          m['full_name'] as String? ?? 'بدون نام',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          m['phone'] as String? ?? '',
                          style: TextStyle(color: MpColors.textSecondary),
                        ),
                        TextButton.icon(
                          onPressed: _busy
                              ? null
                              : () => _changePhone(m['phone'] as String? ?? ''),
                          icon: const Icon(Icons.phone_android),
                          label: const Text('تغییر شمارهٔ موبایل'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  GlassCard(child: _editing ? _editForm() : _viewForm(m)),
                  const SizedBox(height: 12),
                  if (_error != null)
                    Text(
                      _error!,
                      style: const TextStyle(color: Colors.redAccent),
                    ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: _editing
                            ? FilledButton(
                                onPressed: _busy ? null : _save,
                                child: Text(
                                  _busy ? 'در حال ذخیره…' : 'ذخیرهٔ تغییرات',
                                ),
                              )
                            : OutlinedButton.icon(
                                onPressed: () =>
                                    setState(() => _editing = true),
                                icon: const Icon(Icons.edit),
                                label: const Text('ویرایش پروفایل'),
                              ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  // M61/D3 — پیش از این هیچ راهی برای خروج نبود. توکن ۳۰ دقیقه
                  // اعتبار دارد و تا ۱۴ روز قابل تمدید است؛ روی گوشی مشترک
                  // باشگاه، نبودِ خروج یعنی نبودِ تنها راه قطع دسترسی.
                  const _LogoutButton(),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _viewForm(Map<String, dynamic> m) {
    const goals = {
      'hypertrophy': 'افزایش حجم',
      'strength': 'قدرت',
      'weight_loss': 'کاهش وزن',
      'fitness': 'آمادگی جسمانی',
    };
    return Column(
      children: [
        _row('هدف تمرینی', goals[m['goal'] as String?] ?? '—'),
        _row(
          'جنس',
          (m['gender'] as String?) == 'female'
              ? 'زن'
              : ((m['gender'] as String?) == 'male' ? 'مرد' : '—'),
        ),
        _row(
          'قد',
          m['height_cm'] != null ? '${m['height_cm']} سانتی‌متر' : '—',
        ),
        _row('محدودیت‌ها', (m['constraints'] as String?) ?? '—'),
      ],
    );
  }

  Widget _editForm() {
    return Column(
      children: [
        TextField(
          controller: _name,
          decoration: const InputDecoration(
            labelText: 'نام کامل',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _goal.isEmpty ? null : _goal,
          decoration: const InputDecoration(
            labelText: 'هدف تمرینی',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'hypertrophy', child: Text('افزایش حجم')),
            DropdownMenuItem(value: 'strength', child: Text('قدرت')),
            DropdownMenuItem(value: 'weight_loss', child: Text('کاهش وزن')),
            DropdownMenuItem(value: 'fitness', child: Text('آمادگی جسمانی')),
          ],
          onChanged: (v) => setState(() => _goal = v ?? ''),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _gender,
          decoration: const InputDecoration(
            labelText: 'جنس',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: 'male', child: Text('مرد')),
            DropdownMenuItem(value: 'female', child: Text('زن')),
          ],
          onChanged: (v) => setState(() => _gender = v ?? 'unknown'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _height,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(
            labelText: 'قد (سانتی‌متر)',
            border: OutlineInputBorder(),
          ),
        ),
      ],
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(label, style: TextStyle(color: MpColors.textSecondary)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

/// دکمهٔ خروج با تأیید صریح (کار برگشت‌ناپذیر است).
class _LogoutButton extends ConsumerStatefulWidget {
  const _LogoutButton();

  @override
  ConsumerState<_LogoutButton> createState() => _LogoutButtonState();
}

class _LogoutButtonState extends ConsumerState<_LogoutButton> {
  bool _busy = false;

  Future<void> _confirmAndLogout() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('خروج از حساب'),
        content: const Text(
          'از حساب خارج می‌شوید. برای ورود دوباره به کد پیامکی نیاز دارید.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('انصراف'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('خروج'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    final queueChoice = await _confirmPendingFeedbackExit(
      context,
      ref,
      ref.read(authProvider).memberId,
    );
    if (queueChoice == _PendingQueueExitChoice.cancel || !mounted) return;
    setState(() => _busy = true);
    try {
      final revoke = await ref
          .read(authProvider.notifier)
          .logout(
            keepPendingFeedback: queueChoice == _PendingQueueExitChoice.keep,
            discardPendingFeedback:
                queueChoice == _PendingQueueExitChoice.discard,
          );
      if (!mounted) return;
      final queueNote = queueChoice == _PendingQueueExitChoice.keep
          ? ' صف فقط برای همین حساب روی دستگاه باقی ماند.'
          : '';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            revoke
                ? 'از حساب خارج شدید و نشست سرور بسته شد.$queueNote'
                : 'از این دستگاه خارج شدید. سرور در دسترس نبود، پس نشست آن‌جا ممکن است باز بماند.$queueNote',
          ),
        ),
      );
      context.go('/otp');
    } on PendingOfflineFeedbackException {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'صف تغییر کرده است؛ همگام‌سازی یا تصمیم دربارهٔ آن را دوباره انجام دهید.',
            ),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('خروج امن انجام نشد؛ صف محلی دست‌نخورده باقی ماند.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: _busy ? null : _confirmAndLogout,
      icon: const Icon(Icons.logout, color: Colors.redAccent),
      label: Text(_busy ? 'در حال خروج…' : 'خروج از حساب'),
    );
  }
}
