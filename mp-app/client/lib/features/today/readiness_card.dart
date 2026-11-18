/// خلاصهٔ آمادگی/خستگی از گزارش واقعی موتور MP؛ تخمینی است، نه تشخیص پزشکی.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ReadinessCard extends ConsumerWidget {
  const ReadinessCard({super.key});

  static const _bands = <String, String>{
    'ready': 'آماده',
    'monitor': 'نیازمند مراقبت',
    'fatigued': 'خستگی بالا',
    'insufficient': 'دادهٔ ناکافی',
  };
  static const _recommendations = <String, String>{
    'keep': 'حفظ حجم',
    'deload': 'پیشنهاد کاهش حجم',
    'increase': 'پیشنهاد افزایش حجم',
    'insufficient': 'توصیه‌ای ساخته نشد',
  };
  static const _signals = <String, String>{
    'rep_drop': 'افت تکرار',
    'rir_mismatch': 'اختلاف RIR',
    'soreness': 'درد عضلانی',
    'volume_spike': 'تغییر حجم هفتگی',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final report = ref.watch(readinessProvider);
    return report.when(
      loading: () => const GlassCard(
        child: Row(
          children: [
            SizedBox.square(
              dimension: 22,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('در حال دریافت آمادگی از داده‌های تمرین…'),
          ],
        ),
      ),
      error: (error, _) => GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'آمادگی دریافت نشد',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 6),
            Text(
              '$error',
              style: const TextStyle(
                color: MpColors.textSecondary,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () => ref.invalidate(readinessProvider),
              child: const Text('تلاش دوباره'),
            ),
          ],
        ),
      ),
      data: (payload) {
        final rawReadiness = payload['readiness'];
        if (rawReadiness == null) {
          return GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'آمادگی هنوز قابل محاسبه نیست',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                Text(
                  payload['reason'] as String,
                  style: TextStyle(color: MpColors.textSecondary, height: 1.5),
                ),
                const SizedBox(height: 6),
                const Text(
                  'امتیاز یا توصیهٔ ساختگی نمایش داده نمی‌شود.',
                  style: TextStyle(fontSize: 11, color: MpColors.textSecondary),
                ),
              ],
            ),
          );
        }

        final readiness = Map<String, dynamic>.from(rawReadiness as Map);
        final score = readiness['score'] as num?;
        final band = readiness['band'] as String;
        final recommendation = readiness['recommendation'] as String;
        final signals = (readiness['signals'] as List)
            .map((item) => Map<String, dynamic>.from(item as Map))
            .toList();
        final missing = (readiness['missing_signals'] as List).cast<String>();
        final counts = payload['data_counts'] is Map
            ? Map<String, dynamic>.from(payload['data_counts'] as Map)
            : null;
        final color = switch (band) {
          'ready' => MpColors.primary,
          'monitor' => MpColors.accent,
          'fatigued' => MpColors.danger,
          _ => MpColors.textSecondary,
        };

        return GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.monitor_heart_outlined,
                    color: MpColors.primary,
                  ),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'آمادگی / خستگی',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 9,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _bands[band] ?? 'وضعیت نامعلوم',
                      style: TextStyle(color: color),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Text(
                    score == null
                        ? 'امتیاز نامعلوم'
                        : '${_fa(score.toStringAsFixed(1))} از ۱۰۰',
                    style: const TextStyle(
                      fontSize: 19,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  if (score != null) ...[
                    const SizedBox(width: 12),
                    Expanded(
                      child: LinearProgressIndicator(
                        value: (score / 100).clamp(0, 1).toDouble(),
                        color: color,
                        backgroundColor: MpColors.surface,
                        minHeight: 7,
                      ),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'توصیه: ${_recommendations[recommendation] ?? 'توصیهٔ نامعلوم'}',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                readiness['reason'] as String,
                style: TextStyle(color: MpColors.textSecondary, height: 1.5),
              ),
              const Divider(height: 22),
              for (final signal in signals)
                Padding(
                  padding: const EdgeInsets.only(bottom: 7),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        width: 95,
                        child: Text(
                          _signals[signal['name']] ?? signal['name'] as String,
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      Expanded(
                        child: Text(
                          '${signal['score'] == null ? 'نامعلوم' : '${_fa(((signal['score'] as num).round()).toString())} از ۱۰۰'} · ${signal['reason']}',
                          style: TextStyle(
                            color: MpColors.textSecondary,
                            fontSize: 11,
                            height: 1.5,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              if (missing.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 2, bottom: 8),
                  child: Text(
                    'سیگنال‌های ناموجود: ${missing.map((name) => _signals[name] ?? name).join('، ')}',
                    style: const TextStyle(
                      color: MpColors.accent,
                      fontSize: 11,
                    ),
                  ),
                ),
              if (counts != null)
                Text(
                  'بر پایهٔ ${_fa('${counts['feedback_rows'] ?? 0}')} بازخورد؛ '
                  '${_fa('${counts['sets_last_7_days'] ?? 0}')} ست در ۷ روز اخیر و '
                  '${_fa('${counts['sets_prior_7_days'] ?? 0}')} ست در ۷ روز پیش از آن',
                  style: TextStyle(
                    color: MpColors.textSecondary,
                    fontSize: 10,
                    height: 1.5,
                  ),
                ),
              if (payload['note'] is String) ...[
                const SizedBox(height: 6),
                Text(
                  payload['note'] as String,
                  style: TextStyle(
                    color: MpColors.textSecondary,
                    fontSize: 10,
                    height: 1.5,
                  ),
                ),
              ],
              const SizedBox(height: 8),
              const Text(
                'این برآورد از بازخورد تمرین ثبت‌شده و قواعد MP می‌آید؛ تشخیص پزشکی نیست.',
                style: TextStyle(
                  color: MpColors.textSecondary,
                  fontSize: 10,
                  height: 1.5,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

String _fa(String value) => value.replaceAllMapped(
  RegExp(r'\d'),
  (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
);
