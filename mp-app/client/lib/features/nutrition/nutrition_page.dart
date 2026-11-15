/// تغذیهٔ واقعی — برنامهٔ محاسبه‌شده از موتور (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class NutritionPage extends ConsumerWidget {
  const NutritionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plan = ref.watch(nutritionProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          plan.when(
            loading: () => const Center(
                child: Padding(
              padding: EdgeInsets.all(40),
              child: CircularProgressIndicator(),
            )),
            error: (e, _) => GlassCard(
                child: Text('خطا: $e', textAlign: TextAlign.center)),
            data: (p) {
              if (p == null) {
                return GlassCard(
                  child: Column(
                    children: [
                      const Icon(Icons.restaurant, size: 44, color: MpColors.accent),
                      const SizedBox(height: 10),
                      const Text('برنامهٔ غذایی ندارید',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 6),
                      Text('در جریان ساخت برنامه، تغذیه هم محاسبه می‌شود',
                          style: TextStyle(color: MpColors.textSecondary)),
                    ],
                  ),
                );
              }
              final kcal = p['daily_kcal'] ?? p['target_kcal'] ?? 0;
              return Column(
                children: [
                  GlassCard(
                    child: Column(
                      children: [
                        Text('کالری روزانه',
                            style: TextStyle(color: MpColors.textSecondary)),
                        const SizedBox(height: 6),
                        Text('$kcal کیلوکالری',
                            style: const TextStyle(
                                fontSize: 30, fontWeight: FontWeight.w900)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _macro('پروتئین', p['protein_g'], MpColors.primary),
                      const SizedBox(width: 8),
                      _macro('کربوهیدرات', p['carbs_g'], MpColors.info),
                      const SizedBox(width: 8),
                      _macro('چربی', p['fat_g'], MpColors.accent),
                    ],
                  ),
                  if ((p['llm_explanation'] as String? ?? '').isNotEmpty) ...[
                    const SizedBox(height: 12),
                    GlassCard(
                      child: Text(p['llm_explanation'] as String,
                          style: const TextStyle(height: 1.8)),
                    ),
                  ],
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _macro(String label, dynamic grams, Color color) {
    return Expanded(
      child: GlassCard(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Column(
          children: [
            Text('$grams گرم',
                style: TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, style: TextStyle(fontSize: 12, color: MpColors.textSecondary)),
          ],
        ),
      ),
    );
  }
}
