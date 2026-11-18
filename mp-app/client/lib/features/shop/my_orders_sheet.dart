/// «سفارش‌های من» برای عضو — تاریخچه از API با ورودی رسید (M90).
///
/// پیش از این `shopOrdersProvider` فقط بعد از checkout صدایی invalidate می‌شد و
/// هیچ صفحه‌ای فهرست سفارش را نشان نمی‌داد؛ یعنی عضو اگر SnackBar را از دست
/// می‌داد، راهی برای دیدن وضعیت تحویل یا گرفتن رسید نداشت.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/membership.dart';
import '../../core/persian_format.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'order_receipt_sheet.dart';

/// باز کردن شیت «سفارش‌های من»؛ از دسترس ShopPage و هر جای دیگر.
Future<void> showMyOrders(BuildContext context, WidgetRef ref) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => const MyOrdersSheet(),
  );
}

class MyOrdersSheet extends ConsumerWidget {
  const MyOrdersSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orders = ref.watch(shopOrdersProvider);
    return Container(
      decoration: const BoxDecoration(
        color: MpColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SizedBox(
        height: MediaQuery.of(context).size.height * 0.72,
        child: Column(
          children: [
            Row(
              children: [
                const Icon(
                  Icons.receipt_long_outlined,
                  color: MpColors.primaryLight,
                  size: 22,
                ),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'سفارش‌های من',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                  ),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('بستن'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: orders.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (e, _) => GlassCard(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'دریافت سفارش‌ها ناموفق بود\n$e',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: () => ref.invalidate(shopOrdersProvider),
                        child: const Text('تلاش دوباره'),
                      ),
                    ],
                  ),
                ),
                data: (list) {
                  if (list.isEmpty) {
                    return const GlassCard(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: Text(
                          'هنوز سفارشی ثبت نشده است\n'
                          'هر خریدی که از کیف‌پول انجام شود این‌جا دیده می‌شود.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    );
                  }
                  return RefreshIndicator(
                    onRefresh: () async => ref.invalidate(shopOrdersProvider),
                    child: ListView(
                      padding: const EdgeInsets.only(bottom: 12),
                      children: [
                        for (final order in list) _OrderRow(order: order),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OrderRow extends ConsumerWidget {
  const _OrderRow({required this.order});

  final Map<String, dynamic> order;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = (order['id'] as num?)?.toInt();
    final status = (order['status'] as String?) ?? '';
    final total = (order['total_rial'] as num?) ?? 0;
    final items =
        ((order['items'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final itemCount = items.fold<int>(
      0,
      (sum, line) => sum + ((line['qty'] as num?)?.toInt() ?? 0),
    );
    final createdAt = _date(order['created_at']);
    final note = (order['note'] as String?)?.trim() ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'سفارش #${faDigits(id ?? 0)}',
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 14,
                    ),
                  ),
                ),
                Text(
                  orderStatusLabel(status),
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: switch (status) {
                      'paid' || 'delivered' => MpColors.primary,
                      'cancelled' || 'failed' => MpColors.danger,
                      _ => MpColors.accent,
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              [
                if (createdAt != null) formatJalaliDate(createdAt),
                '${faDigits(itemCount)} قلم',
                if (note.isNotEmpty) 'یادداشت: $note',
              ].join(' · '),
              style: const TextStyle(
                fontSize: 12,
                color: MpColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(
                    rial(total),
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      color: MpColors.accentSoft,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: id == null
                      ? null
                      : () => showOrderReceipt(context, ref, id),
                  icon: const Icon(Icons.receipt_long_outlined, size: 18),
                  label: const Text('رسید'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

DateTime? _date(Object? raw) {
  if (raw is! String || raw.isEmpty) return null;
  return DateTime.tryParse(raw)?.toLocal();
}
