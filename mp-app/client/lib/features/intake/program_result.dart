/// نمایش برنامهٔ واقعی تولیدشده از موتور — هفته‌ها، حرکات، بار/تکرار/استراحت.
library;

import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../shared/widgets/glass_card.dart';

class ProgramResult extends StatelessWidget {
  const ProgramResult({
    super.key,
    required this.program,
    required this.nutrition,
    required this.onStartOver,
  });

  final Map<String, dynamic> program;
  final Map<String, dynamic>? nutrition;
  final VoidCallback onStartOver;

  @override
  Widget build(BuildContext context) {
    final weeks = (program['weeks'] as List?) ?? const [];
    final explanation = program['llm_explanation'] as String? ?? '';
    final engineVersion = program['engine_version'] as String? ?? '';
    final goal = program['goal'] as String? ?? '';

    return Scaffold(
      appBar: AppBar(title: const Text('برنامهٔ اختصاصی شما')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              GlassCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.fitness_center, color: MpColors.primary),
                        const SizedBox(width: 8),
                        Text('برنامهٔ $goal — ${weeks.length} هفته',
                            style: const TextStyle(
                                fontSize: 17, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    if (engineVersion.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text('نسخهٔ موتور: $engineVersion',
                          style:
                              TextStyle(color: MpColors.textSecondary, fontSize: 12)),
                    ],
                    if (explanation.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      Text(explanation, style: const TextStyle(height: 1.8)),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 12),
              ...weeks.map(_weekCard),
              if (nutrition != null) ...[
                const SizedBox(height: 12),
                _nutritionCard(nutrition!),
              ],
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: onStartOver,
                icon: const Icon(Icons.refresh),
                label: const Text('ساخت برنامهٔ جدید'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _weekCard(dynamic w) {
    final week = w as Map<String, dynamic>;
    final exercises = (week['exercises'] as List?) ?? const [];
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('هفتهٔ ${week['week_number']} — ${week['focus'] ?? ''}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 8),
            ...exercises.map(_exerciseRow),
          ],
        ),
      ),
    );
  }

  Widget _exerciseRow(dynamic e) {
    final ex = e as Map<String, dynamic>;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Text('حرکت ${ex['exercise_id']} — روز ${ex['day']}',
                style: const TextStyle(fontSize: 13)),
          ),
          Expanded(
            flex: 3,
            child: Text('${ex['sets']} × ${ex['reps']}',
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            flex: 2,
            child: Text('${ex['load_pct']}٪',
                style: TextStyle(fontSize: 13, color: MpColors.primary)),
          ),
          Expanded(
            flex: 2,
            child: Text('${ex['rest_seconds']}s',
                style: TextStyle(fontSize: 12, color: MpColors.textSecondary)),
          ),
        ],
      ),
    );
  }

  Widget _nutritionCard(Map<String, dynamic> n) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('برنامهٔ غذایی شما',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          const SizedBox(height: 8),
          Text('کالری روزانه: ${n['target_kcal'] ?? n['daily_kcal']} کیلوکالری'),
          Text('پروتئین: ${n['protein_g']} گرم — کربوهیدرات: ${n['carbs_g']} گرم — چربی: ${n['fat_g']} گرم'),
        ],
      ),
    );
  }
}
