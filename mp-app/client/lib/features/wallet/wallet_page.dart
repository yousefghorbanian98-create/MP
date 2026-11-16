/// کیف‌پول واقعی — مانده از API (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class WalletPage extends ConsumerWidget {
  const WalletPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final wallet = ref.watch(walletProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          wallet.when(
            loading: () => const GlassCard(
                child: Center(child: Padding(
              padding: EdgeInsets.all(24),
              child: CircularProgressIndicator(),
            ))),
            error: (e, _) => GlassCard(
              child: Column(children: [
                const Icon(Icons.error_outline, color: MpColors.danger, size: 40),
                const SizedBox(height: 8),
                Text('خطا در دریافت موجودی: $e', textAlign: TextAlign.center),
                const SizedBox(height: 10),
                OutlinedButton(
                  onPressed: () => ref.invalidate(walletProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ]),
            ),
            data: (w) {
              final balance = (w['balance_rial'] as num? ?? 0).toInt();
              return GlassCard(
                child: Column(
                  children: [
                    Text('موجودی کیف پول',
                        style: TextStyle(color: MpColors.textSecondary)),
                    const SizedBox(height: 8),
                    Text(
                      '${_fmt(balance)} ریال',
                      style: const TextStyle(
                          fontSize: 32, fontWeight: FontWeight.w900),
                    ).animate().fadeIn(duration: 500.ms).scale(
                        begin: const Offset(0.95, 0.95),
                        curve: Curves.easeOutBack),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 12),
          // G1 — تاریخچهٔ پرداخت. پرسش روزمرهٔ عضو «پول من کجا رفت؟» بود و
          // هیچ پاسخی در اپ نداشت.
          _PaymentHistory(),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('شارژ کیف پول',
                    style: TextStyle(fontWeight: FontWeight.bold)),
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
          const Text('تاریخچهٔ پرداخت', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          payments.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Center(child: SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
            error: (e, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('دریافت تاریخچه ناموفق بود: $e',
                    style: const TextStyle(color: MpColors.danger, fontSize: 12)),
                const SizedBox(height: 6),
                OutlinedButton(
                  onPressed: () => ref.invalidate(myPaymentsProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
            data: (rows) {
              if (rows.isEmpty) {
                return Text('هنوز پرداختی ثبت نشده است.',
                    style: TextStyle(color: MpColors.textSecondary, fontSize: 13));
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
                                  (p['description'] as String?)?.isNotEmpty == true
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
                            '${_fmtRial((p['amount_rial'] as num?) ?? 0)} ریال',
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
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
                      child: Text('۲۰ مورد آخر از ${_fmtRial(rows.length)} پرداخت',
                          style: TextStyle(color: MpColors.textSecondary, fontSize: 11)),
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
