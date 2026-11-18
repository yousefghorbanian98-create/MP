/// تاریخچهٔ حضور عضو — همیشه از هویت نشست جاری خوانده می‌شود (M80).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

const _historyPageSize = 30;

final memberCheckInHistoryProvider =
    FutureProvider.family<Map<String, dynamic>, int>((ref, offset) async {
      final api = ref.watch(apiClientProvider);
      final raw = await api.get(
        '/members/me/checkins?limit=$_historyPageSize&offset=$offset',
      );
      if (raw is! Map) throw ApiException('ساختار پاسخ سوابق حضور معتبر نیست');

      final payload = Map<String, dynamic>.from(raw);
      final rows = payload['items'];
      if (rows is! List || payload['has_more'] is! bool) {
        throw ApiException('ساختار پاسخ سوابق حضور ناقص است');
      }
      final items = <Map<String, dynamic>>[];
      for (final row in rows) {
        if (row is! Map) throw ApiException('رکورد حضور معتبر نیست');
        final item = Map<String, dynamic>.from(row);
        if (item['checkin_id'] is! int ||
            item['method'] is! String ||
            item['result'] is! String ||
            item['denial_reason'] is! String ||
            item['is_open'] is! bool ||
            (item['checked_in_at'] != null &&
                item['checked_in_at'] is! String) ||
            (item['checked_out_at'] != null &&
                item['checked_out_at'] is! String)) {
          throw ApiException('رکورد حضور معتبر نیست');
        }
        items.add(item);
      }
      return {...payload, 'items': items};
    });

class MemberCheckInHistoryPage extends ConsumerStatefulWidget {
  const MemberCheckInHistoryPage({super.key});

  @override
  ConsumerState<MemberCheckInHistoryPage> createState() =>
      _MemberCheckInHistoryPageState();
}

class _MemberCheckInHistoryPageState
    extends ConsumerState<MemberCheckInHistoryPage> {
  final List<Map<String, dynamic>> _olderItems = [];
  bool _loadingMore = false;
  bool? _hasMoreOverride;
  String? _loadMoreError;

  Future<void> _loadMore(int offset, {bool retry = false}) async {
    if (_loadingMore) return;
    if (retry) ref.invalidate(memberCheckInHistoryProvider(offset));
    setState(() {
      _loadingMore = true;
      _loadMoreError = null;
    });
    try {
      final page = await ref.read(memberCheckInHistoryProvider(offset).future);
      if (!mounted) return;
      setState(() {
        _olderItems.addAll(
          (page['items'] as List).cast<Map<String, dynamic>>(),
        );
        _hasMoreOverride = page['has_more'] as bool;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _loadMoreError = '$error');
    } finally {
      if (mounted) setState(() => _loadingMore = false);
    }
  }

  void _retryFirstPage() {
    setState(() {
      _olderItems.clear();
      _hasMoreOverride = null;
      _loadMoreError = null;
    });
    ref.invalidate(memberCheckInHistoryProvider(0));
  }

  @override
  Widget build(BuildContext context) {
    final history = ref.watch(memberCheckInHistoryProvider(0));
    return history.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'دریافت سوابق حضور ناموفق بود: $error',
                textAlign: TextAlign.center,
                style: const TextStyle(color: MpColors.danger),
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: _retryFirstPage,
                child: const Text('تلاش دوباره'),
              ),
            ],
          ),
        ),
      ),
      data: (payload) {
        final firstPage = (payload['items'] as List)
            .cast<Map<String, dynamic>>();
        final items = [...firstPage, ..._olderItems];
        final hasMore = _hasMoreOverride ?? (payload['has_more'] as bool);
        return ListView(
          key: const ValueKey('member-checkin-history-list'),
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'سوابق حضور',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: MpColors.textPrimary,
                    ),
                  ),
                ),
                IconButton(
                  tooltip: 'تازه‌سازی سوابق',
                  onPressed: _retryFirstPage,
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (items.isEmpty)
              const GlassCard(
                child: Text(
                  'هنوز سابقهٔ حضوری ثبت نشده است.',
                  style: TextStyle(color: MpColors.textSecondary),
                ),
              )
            else
              for (final item in items) ...[
                _CheckInHistoryItem(item: item),
                const SizedBox(height: 10),
              ],
            if (_loadMoreError != null) ...[
              Text(
                'دریافت سوابق قدیمی‌تر ناموفق بود: $_loadMoreError',
                style: const TextStyle(color: MpColors.danger),
              ),
              TextButton(
                onPressed: _loadingMore
                    ? null
                    : () => _loadMore(items.length, retry: true),
                child: const Text('تلاش دوباره'),
              ),
            ],
            if (hasMore && _loadMoreError == null)
              OutlinedButton.icon(
                onPressed: _loadingMore ? null : () => _loadMore(items.length),
                icon: _loadingMore
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.expand_more),
                label: Text(_loadingMore ? 'در حال دریافت…' : 'سوابق قدیمی‌تر'),
              ),
          ],
        );
      },
    );
  }
}

class _CheckInHistoryItem extends StatelessWidget {
  const _CheckInHistoryItem({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final successful = item['result'] == 'ok';
    final method = switch (item['method']) {
      'qr' => 'QR',
      'face' => 'ثبت از صفحهٔ چهره',
      'manual' => 'ثبت پذیرش',
      _ => 'روش نامشخص',
    };
    final reason = item['denial_reason'] as String;
    final checkedOutAt = item['checked_out_at'] as String?;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                successful ? Icons.check_circle_outline : Icons.error_outline,
                color: successful ? MpColors.primaryLight : MpColors.danger,
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  successful ? 'ورود ثبت شد' : 'ورود ثبت نشد',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: successful ? MpColors.primaryLight : MpColors.danger,
                  ),
                ),
              ),
              Text(
                method,
                style: const TextStyle(
                  fontSize: 12,
                  color: MpColors.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'ورود: ${_formatMemberDateTime(item['checked_in_at'] as String?)}',
            style: const TextStyle(fontSize: 12, color: MpColors.textPrimary),
          ),
          if (checkedOutAt != null)
            Text(
              'خروج: ${_formatMemberDateTime(checkedOutAt)}',
              style: const TextStyle(fontSize: 12, color: MpColors.textPrimary),
            )
          else if (item['is_open'] == true)
            const Text(
              'زمان خروج ثبت نشده است',
              style: TextStyle(fontSize: 11, color: MpColors.textSecondary),
            ),
          if (!successful && reason.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Text(
                'دلیل: ${_denialReasonFa(reason)}',
                style: const TextStyle(
                  fontSize: 11,
                  color: MpColors.textSecondary,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

String _denialReasonFa(String reason) => switch (reason) {
  'membership_expired' => 'اشتراک فعال نیست یا منقضی شده است',
  _ => reason,
};

String _formatMemberDateTime(String? value) {
  if (value == null) return 'زمان نامعلوم';
  final parsed = DateTime.tryParse(value);
  if (parsed == null) return 'زمان نامعلوم';
  final local = parsed.toLocal();
  final date =
      '${local.year}/${local.month.toString().padLeft(2, '0')}/${local.day.toString().padLeft(2, '0')}';
  final time =
      '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  return '${_toPersianDigits(date)} · ${_toPersianDigits(time)}';
}

String _toPersianDigits(String value) {
  const digits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return value.split('').map((character) {
    final digit = int.tryParse(character);
    return digit == null ? character : digits[digit];
  }).join();
}
