/// کیف پول کلاینت — موجودی + تراکنش‌ها + پرداخت از کیف پول (M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class WalletPage extends StatelessWidget {
  const WalletPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('کیف پول'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          GlassCard(
            child: Column(
              children: [
                const Text('موجودی فعلی', style: TextStyle(fontSize: 13, color: MpColors.textSecondary)),
                const SizedBox(height: 8),
                const Text(
                  '۱٬۲۵۰٬۰۰۰ ریال',
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w900, color: MpColors.textPrimary),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _WalletButton(
                        label: 'افزایش موجودی',
                        icon: Icons.add_circle_outline,
                        filled: true,
                        onTap: () {},
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _WalletButton(
                        label: 'پرداخت با کیف پول',
                        icon: Icons.payment,
                        filled: false,
                        onTap: () {},
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          const Text('تراکنش‌های اخیر', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              children: [
                _TxRow(title: 'پرداخت اشتراک ماهانه', amount: '−۵۰۰٬۰۰۰', date: '۱۲ آبان', isCredit: false),
                Divider(color: MpColors.primary.withOpacity(0.10)),
                _TxRow(title: 'شارژ کیف پول', amount: '+۱٬۰۰۰٬۰۰۰', date: '۸ آبان', isCredit: true),
                Divider(color: MpColors.primary.withOpacity(0.10)),
                _TxRow(title: 'خرید مکمل (فروشگاه)', amount: '−۲۵۰٬۰۰۰', date: '۵ آبان', isCredit: false),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _WalletButton extends StatelessWidget {
  const _WalletButton({required this.label, required this.icon, required this.filled, required this.onTap});

  final String label;
  final IconData icon;
  final bool filled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: filled ? MpColors.primary : Colors.transparent,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: filled ? null : Border.all(color: MpColors.primary.withOpacity(0.4)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 18, color: filled ? Colors.white : MpColors.primary),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: filled ? Colors.white : MpColors.primary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TxRow extends StatelessWidget {
  const _TxRow({required this.title, required this.amount, required this.date, required this.isCredit});

  final String title;
  final String amount;
  final String date;
  final bool isCredit;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: (isCredit ? MpColors.primary : MpColors.danger).withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              isCredit ? Icons.arrow_downward : Icons.arrow_upward,
              size: 18,
              color: isCredit ? MpColors.primaryLight : MpColors.danger,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 13, color: MpColors.textPrimary, fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text(date, style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
              ],
            ),
          ),
          Text(
            amount,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: isCredit ? MpColors.primaryLight : MpColors.danger,
            ),
          ),
        ],
      ),
    );
  }
}
