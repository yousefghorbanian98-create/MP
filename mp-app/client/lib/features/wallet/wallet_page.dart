/// کیف‌پول واقعی — مانده از API (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/membership.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'wallet_ledger.dart';

class WalletPage extends ConsumerWidget {
  const WalletPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ledger = ref.watch(walletLedgerProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassCard(
            child: Column(
              children: [
                Text(
                  'موجودی کیف پول',
                  style: TextStyle(color: MpColors.textSecondary),
                ),
                const SizedBox(height: 8),
                if (ledger.isLoading)
                  const Padding(
                    padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(),
                  )
                else if (ledger.error != null)
                  Column(
                    children: [
                      const Text(
                        'ماندهٔ کیف‌پول در دسترس نیست',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: MpColors.danger),
                      ),
                      const SizedBox(height: 8),
                      OutlinedButton(
                        onPressed: () => ref
                            .read(walletLedgerProvider.notifier)
                            .loadFirstPage(),
                        child: const Text('تلاش دوباره'),
                      ),
                    ],
                  )
                else if (ledger.balanceRial != null)
                  Text(
                    '${_fmt(ledger.balanceRial!)} ریال',
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w900,
                    ),
                  ).animate().fadeIn(duration: 500.ms).scale(
                        begin: const Offset(0.95, 0.95),
                        curve: Curves.easeOutBack,
                      ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          const _WalletLedger(),
          const SizedBox(height: 12),
          // G1 — payment history remains useful, but does not replace the ledger:
          // manual wallet credits are WalletTransaction rows, not necessarily Payments.
          _PaymentHistory(),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'شارژ کیف پول',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  'برای شارژ به پذیرش باشگاه مراجعه کنید یا از درگاه پرداخت استفاده کنید.',
                  style: TextStyle(color: MpColors.textSecondary, fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _fmt(int n) {
    final s = n.toString();
    final b = StringBuffer();
    for (var i = 0; i < s.length; i++) {
      if (i > 0 && (s.length - i) % 3 == 0) b.write(',');
      b.write(s[i]);
    }
    return b.toString();
  }
}

/// دفتر واقعی credit/debit؛ Payment history به‌تنهایی شارژهای دستی را از دست می‌دهد.
class _WalletLedger extends ConsumerWidget {
  const _WalletLedger();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ledger = ref.watch(walletLedgerProvider);
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'دفتر گردش کیف پول',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'شارژ و برداشت واقعی از دفتر سرور · جدیدترین مورد در ابتدا',
            style: TextStyle(color: MpColors.textSecondary, fontSize: 11),
          ),
          const SizedBox(height: 10),
          if (ledger.isLoading)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else if (ledger.error != null)
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'دریافت دفتر کیف‌پول ناموفق بود: ${ledger.error}',
                  style: const TextStyle(color: MpColors.danger, fontSize: 12),
                ),
                const SizedBox(height: 6),
                OutlinedButton(
                  onPressed: () =>
                      ref.read(walletLedgerProvider.notifier).loadFirstPage(),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            )
          else if (ledger.transactions.isEmpty)
            Text(
              'هنوز تراکنشی در کیف‌پول ثبت نشده است.',
              style: TextStyle(color: MpColors.textSecondary, fontSize: 13),
            )
          else ...[
            for (final row in ledger.transactions) _transactionRow(row),
            if (ledger.loadMoreError != null) ...[
              const SizedBox(height: 6),
              Text(
                'دریافت موارد قدیمی‌تر ناموفق بود: ${ledger.loadMoreError}',
                style: const TextStyle(color: MpColors.danger, fontSize: 12),
              ),
            ],
            if (ledger.nextBeforeId != null)
              Align(
                alignment: AlignmentDirectional.centerStart,
                child: OutlinedButton.icon(
                  onPressed: ledger.isLoadingMore
                      ? null
                      : () =>
                          ref.read(walletLedgerProvider.notifier).loadMore(),
                  icon: ledger.isLoadingMore
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.history),
                  label: Text(
                    ledger.isLoadingMore
                        ? 'در حال دریافت…'
                        : 'تراکنش‌های قدیمی‌تر',
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Widget _transactionRow(Map<String, dynamic> row) {
    final credit = row['kind'] == 'credit';
    final amount = (row['amount_rial'] as int).toInt();
    final createdAt = DateTime.tryParse(row['created_at'] as String)?.toLocal();
    final description = (row['description'] as String).trim();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Icon(
            credit ? Icons.add_circle_outline : Icons.remove_circle_outline,
            color: credit ? Colors.greenAccent : MpColors.textSecondary,
            size: 20,
          ),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  description.isEmpty
                      ? (credit ? 'شارژ کیف پول' : 'پرداخت از کیف پول')
                      : description,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13),
                ),
                Text(
                  '${credit ? 'شارژ' : 'برداشت'} · '
                  '${createdAt == null ? 'تاریخ نامعلوم' : formatJalaliDate(createdAt)}',
                  style: TextStyle(color: MpColors.textSecondary, fontSize: 11),
                ),
              ],
            ),
          ),
          Text(
            '${credit ? '+' : '−'}${_fmtRial(amount)} ریال',
            style: TextStyle(
              color: credit ? Colors.greenAccent : MpColors.textPrimary,
              fontSize: 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

/// تاریخچهٔ پرداخت‌های عضو — وضعیت‌ها از سرور می‌آیند، هیچ محاسبهٔ سمت کلاینت.
class _PaymentHistory extends ConsumerWidget {
  static const _labels = {
    'paid': 'پرداخت‌شده',
    'pending': 'در انتظار',
    'failed': 'ناموفق',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final payments = ref.watch(myPaymentsProvider);
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'تاریخچهٔ پرداخت',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          payments.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            ),
            error: (e, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'دریافت تاریخچه ناموفق بود: $e',
                  style: const TextStyle(color: MpColors.danger, fontSize: 12),
                ),
                const SizedBox(height: 6),
                OutlinedButton(
                  onPressed: () => ref.invalidate(myPaymentsProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
            data: (rows) {
              if (rows.isEmpty) {
                return Text(
                  'هنوز پرداختی ثبت نشده است.',
                  style: TextStyle(color: MpColors.textSecondary, fontSize: 13),
                );
              }
              return Column(
                children: [
                  for (final (i, p) in rows.take(20).indexed)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  (p['description'] as String?)?.isNotEmpty ==
                                          true
                                      ? p['description'] as String
                                      : 'پرداخت #${p['id']}',
                                  style: const TextStyle(fontSize: 13),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                Text(
                                  '${_labels[p['status']] ?? p['status']} · ${p['method'] ?? '—'}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: p['status'] == 'failed'
                                        ? MpColors.danger
                                        : MpColors.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Text(
                            '${_fmtRial(((p['amount_rial'] as num?) ?? 0).toInt())} ریال',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    )
                        .animate(delay: (i * 30).ms)
                        .fadeIn(duration: 220.ms)
                        .slideX(begin: 0.06, end: 0),
                  if (rows.length > 20)
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(
                        '۲۰ مورد آخر از ${_fmtRial(rows.length)} پرداخت',
                        style: TextStyle(
                          color: MpColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

String _fmtRial(int n) {
  final s = n.toString();
  final b = StringBuffer();
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 == 0) b.write(',');
    b.write(s[i]);
  }
  return b.toString();
}
