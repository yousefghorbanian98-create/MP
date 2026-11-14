/// کیف پول کلاینت — موجودی + تراکنش‌ها + پرداخت از کیف پول (M19؛ خروجی‌های زنده در M22-c4).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class WalletPage extends StatefulWidget {
  const WalletPage({super.key});

  @override
  State<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends State<WalletPage> {
  int _balance = 1250000; // ریال — دادهٔ ساختگی محلی (اتصال API در M27)
  final List<_TxData> _txs = [
    _TxData('پرداخت اشتراک ماهانه', -500000, '۱۲ آبان'),
    _TxData('شارژ کیف پول', 1000000, '۸ آبان'),
    _TxData('خرید مکمل (فروشگاه)', -250000, '۵ آبان'),
  ];

  static String _fa(int value) {
    final digits = value.toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (m) => '٬',
    );
    const fa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return digits.split('').map((c) => int.tryParse(c) == null ? c : fa[int.parse(c)]).join();
  }

  void _snack(String msg, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? MpColors.danger : MpColors.primary,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _chargeSheet() async {
    final amount = await showModalBottomSheet<int>(
      context: context,
      backgroundColor: MpColors.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => _AmountSheet(
        title: 'افزایش موجودی',
        confirmLabel: 'افزایش',
        options: const [100000, 200000, 500000, 1000000],
      ),
    );
    if (amount == null || !mounted) return;
    setState(() {
      _balance += amount;
      _txs.insert(0, _TxData('شارژ کیف پول', amount, 'امروز'));
    });
    _snack('موجودی ${_fa(amount)} ریال افزایش یافت');
  }

  Future<void> _paySheet() async {
    final amount = await showModalBottomSheet<int>(
      context: context,
      backgroundColor: MpColors.surface,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => _AmountSheet(
        title: 'پرداخت با کیف پول',
        confirmLabel: 'پرداخت',
        options: const [50000, 100000, 250000, 500000],
      ),
    );
    if (amount == null || !mounted) return;
    if (amount > _balance) {
      _snack('موجودی کافی نیست', error: true);
      return;
    }
    setState(() {
      _balance -= amount;
      _txs.insert(0, _TxData('پرداخت با کیف پول', -amount, 'امروز'));
    });
    _snack('پرداخت ${_fa(amount)} ریال انجام شد');
  }

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
                Text(
                  '${_fa(_balance)} ریال',
                  style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w900, color: MpColors.textPrimary),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: _WalletButton(
                        label: 'افزایش موجودی',
                        icon: Icons.add_circle_outline,
                        filled: true,
                        onTap: _chargeSheet,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _WalletButton(
                        label: 'پرداخت با کیف پول',
                        icon: Icons.payment,
                        filled: false,
                        onTap: _paySheet,
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
                for (var i = 0; i < _txs.length; i++) ...[
                  if (i > 0) Divider(color: MpColors.primary.withOpacity(0.10)),
                  _TxRow(title: _txs[i].title, amount: _txs[i].signed, date: _txs[i].date, isCredit: _txs[i].amount > 0),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TxData {
  _TxData(this.title, this.amount, this.date);

  final String title;
  final int amount;
  final String date;

  String get signed {
    final abs = amount.abs().toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (m) => '٬',
    );
    const fa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    final faAbs = abs.split('').map((c) => int.tryParse(c) == null ? c : fa[int.parse(c)]).join();
    return amount > 0 ? '+$faAbs' : '−$faAbs';
  }
}

/// شیت انتخاب مبلغ — خروجی: مبلغ انتخاب‌شده یا null.
class _AmountSheet extends StatelessWidget {
  const _AmountSheet({required this.title, required this.confirmLabel, required this.options});

  final String title;
  final String confirmLabel;
  final List<int> options;

  static String _fa(int value) {
    final digits = value.toString().replaceAllMapped(
      RegExp(r'\B(?=(\d{3})+(?!\d))'),
      (m) => '٬',
    );
    const fa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return digits.split('').map((c) => int.tryParse(c) == null ? c : fa[int.parse(c)]).join();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (final v in options)
                ActionChip(
                  label: Text('${_fa(v)} ریال'),
                  backgroundColor: MpColors.primary.withOpacity(0.12),
                  labelStyle: const TextStyle(color: MpColors.primaryLight, fontWeight: FontWeight.w700),
                  onPressed: () => Navigator.pop(context, v),
                ),
            ],
          ),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('انصراف', style: TextStyle(color: MpColors.textSecondary)),
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
                Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
                const SizedBox(height: 3),
                Text(date, style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
              ],
            ),
          ),
          Text(
            '$amount ریال',
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
