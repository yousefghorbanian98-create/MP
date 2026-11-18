/// Visible owner-scoped status and explicit actions for the Android feedback outbox.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/offline_feedback_outbox.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'feedback_providers.dart';

class OfflineFeedbackQueueCard extends ConsumerStatefulWidget {
  const OfflineFeedbackQueueCard({super.key});

  @override
  ConsumerState<OfflineFeedbackQueueCard> createState() =>
      _OfflineFeedbackQueueCardState();
}

class _OfflineFeedbackQueueCardState
    extends ConsumerState<OfflineFeedbackQueueCard> {
  bool _busy = false;
  String? _message;

  Future<void> _sync() async {
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      final result = await ref.read(syncOfflineFeedbackQueueProvider)();
      if (!mounted) return;
      setState(() => _message = result.message);
      ref.invalidate(offlineFeedbackQueueProvider);
    } catch (_) {
      if (mounted)
        setState(() => _message = 'همگام‌سازی کامل نشد؛ داده در صف باقی ماند.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _retryFailed(int ownerMemberId) async {
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      await ref
          .read(offlineFeedbackSyncServiceProvider)
          .retryFailed(ownerMemberId);
      final result = await ref.read(syncOfflineFeedbackQueueProvider)();
      if (!mounted) return;
      setState(() => _message = result.message);
      ref.invalidate(offlineFeedbackQueueProvider);
    } catch (_) {
      if (mounted)
        setState(
          () => _message = 'تلاش مجدد انجام نشد؛ رکوردها در صف باقی ماندند.',
        );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _discard(int ownerMemberId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('حذف صف بازخورد؟'),
        content: const Text(
          'همهٔ بازخوردهای ذخیره‌شده روی این دستگاه، از جمله موارد متعارض، برای همیشه حذف می‌شوند و به سرور نمی‌رسند.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('انصراف'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('حذف قطعی'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      await ref.read(offlineFeedbackStoreProvider).discardOwner(ownerMemberId);
      ref.invalidate(offlineFeedbackQueueProvider);
      if (mounted) setState(() => _message = 'صف همین حساب حذف شد.');
    } catch (_) {
      if (mounted)
        setState(
          () => _message = 'صف حذف نشد؛ دادهٔ محلی دست‌نخورده باقی ماند.',
        );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ownerMemberId = ref.watch(authProvider).memberId;
    final store = ref.watch(offlineFeedbackStoreProvider);
    if (ownerMemberId == null || !store.isSupported)
      return const SizedBox.shrink();
    final queue = ref.watch(offlineFeedbackQueueProvider);
    return queue.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const GlassCard(
        child: Text(
          'خواندن صف آفلاین ممکن نشد؛ هیچ موردی به‌عنوان همگام‌شده نمایش داده نمی‌شود.',
          style: TextStyle(color: Colors.redAccent),
        ),
      ),
      data: (rows) {
        if (rows.isEmpty) return const SizedBox.shrink();
        final pending = rows
            .where((row) => row.status == OfflineFeedbackStatus.pending)
            .length;
        final retry = rows
            .where((row) => row.status == OfflineFeedbackStatus.retry)
            .length;
        final failed = rows
            .where((row) => row.status == OfflineFeedbackStatus.failed)
            .length;
        final conflicts = rows
            .where((row) => row.status == OfflineFeedbackStatus.conflict)
            .length;
        final synced = rows
            .where((row) => row.status == OfflineFeedbackStatus.synced)
            .length;
        final canSync = pending + retry > 0;
        return GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'صف بازخورد آفلاین',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(
                'در انتظار: $pending · زمان‌بندی retry: $retry · نیازمند تلاش دستی: $failed · تعارض: $conflicts · تأییدشده: $synced',
                style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
              ),
              const SizedBox(height: 10),
              if (canSync)
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _busy ? null : _sync,
                    icon: const Icon(Icons.sync),
                    label: Text(
                      _busy ? 'در حال همگام‌سازی…' : 'همگام‌سازی با سرور',
                    ),
                  ),
                ),
              if (failed > 0)
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _busy ? null : () => _retryFailed(ownerMemberId),
                    icon: const Icon(Icons.refresh),
                    label: Text('تلاش دستی برای $failed مورد شکست‌خورده'),
                  ),
                ),
              if (conflicts > 0)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    'مورد متعارض حذف یا دوباره‌ارسال نمی‌شود؛ تا تصمیم کاربر حفظ می‌ماند.',
                    style: TextStyle(fontSize: 11, color: Colors.orangeAccent),
                  ),
                ),
              if (_message != null) ...[
                const SizedBox(height: 8),
                Text(
                  _message!,
                  style: TextStyle(color: MpColors.textSecondary, fontSize: 12),
                ),
              ],
              Align(
                alignment: AlignmentDirectional.centerEnd,
                child: TextButton.icon(
                  onPressed: _busy ? null : () => _discard(ownerMemberId),
                  icon: const Icon(
                    Icons.delete_outline,
                    color: Colors.redAccent,
                  ),
                  label: const Text('حذف صف این حساب'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
