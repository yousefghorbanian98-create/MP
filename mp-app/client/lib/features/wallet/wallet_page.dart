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
