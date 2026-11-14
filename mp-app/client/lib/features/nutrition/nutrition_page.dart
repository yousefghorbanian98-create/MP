/// تغذیه — برنامهٔ غذایی عضو (M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class NutritionPage extends StatelessWidget {
  const NutritionPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('تغذیه'), backgroundColor: MpColors.background, surfaceTintColor: Colors.transparent),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('برنامهٔ امروز', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
                const SizedBox(height: 12),
                Row(
                  children: const [
                    _Macro('کالری', '۲٬۲۰۰', MpColors.primary),
                    _Macro('پروتئین', '۱۶۵g', MpColors.info),
                    _Macro('کربوهیدرات', '۲۲۰g', MpColors.accent),
                    _Macro('چربی', '۷۳g', MpColors.primaryLight),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text('وعده‌ها', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
                SizedBox(height: 10),
                _Meal('صبحانه', 'بلغور جو + تخم‌مرغ + گردو', '۵۲۰ کیلوکالری'),
                _Meal('ناهار', 'سینهٔ مرغ + برنج قهوه‌ای + سالاد', '۷۵۰ کیلوکالری'),
                _Meal('میان‌وعده', 'ماست یونانی + موز', '۲۸۰ کیلوکالری'),
                _Meal('شام', 'ماهی + سبزیجات بخارپز', '۶۵۰ کیلوکالری'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Macro extends StatelessWidget {
  const _Macro(this.label, this.value, this.color);

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(value, style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: color)),
          const SizedBox(height: 3),
          Text(label, style: const TextStyle(fontSize: 10.5, color: MpColors.textSecondary)),
        ],
      ),
    );
  }
}

class _Meal extends StatelessWidget {
  const _Meal(this.title, this.items, this.kcal);

  final String title;
  final String items;
  final String kcal;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Row(
        children: [
          const Icon(Icons.restaurant_menu, size: 18, color: MpColors.primaryLight),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
                const SizedBox(height: 2),
                Text(items, style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
              ],
            ),
          ),
          Text(kcal, style: const TextStyle(fontSize: 11, color: MpColors.accentSoft, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}
