/// پیشرفت واقعی — ارزیابی‌های ثبت‌شدهٔ عضو (فقط مشاهده — قانون M18).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

final myAssessmentsProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) return [];
  try {
    final r = await api.get('/assessments/member/$memberId');
    if (r is List) return r;
    return [];
  } catch (_) {
    return [];
  }
});

class ProgressPage extends ConsumerWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assessments = ref.watch(myAssessmentsProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassCard(
            child: Row(
              children: [
                const Icon(
                  Icons.trending_up,
                  color: MpColors.primary,
                  size: 36,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'روند پیشرفت شما',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'ارزیابی‌های مربی — داده‌های شما فقط توسط ادمین ثبت می‌شود',
                        style: TextStyle(
                          fontSize: 12,
                          color: MpColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          assessments.when(
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (e, _) =>
                GlassCard(child: Text('خطا: $e', textAlign: TextAlign.center)),
            data: (list) {
              if (list.isEmpty) {
                return GlassCard(
                  child: Column(
                    children: [
                      const Icon(
                        Icons.insights,
                        size: 40,
                        color: MpColors.info,
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'هنوز ارزیابی ثبت نشده است',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'پس از ارزیابی توسط مربی، روند شما اینجا دیده می‌شود',
                        style: TextStyle(color: MpColors.textSecondary),
                      ),
                    ],
                  ),
                );
              }
              return Column(
                children: [
                  for (final a in list)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: GlassCard(
                        child: Text(
                          'ارزیابی شمارهٔ ${(a as Map<String, dynamic>)['id']}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
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
