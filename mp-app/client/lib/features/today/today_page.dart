/// «امروز» واقعی — تمرین‌های برنامهٔ موتور، چک‌خوردن زنده، حلقهٔ پیشرفت.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/app_state.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'today_controller.dart';

class TodayPage extends ConsumerWidget {
  const TodayPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final programAsync = ref.watch(myProgramsProvider);
    final exercises = ref.watch(todayWorkoutProvider);
    final todayState = ref.watch(todayControllerProvider);

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () async => ref.invalidate(myProgramsProvider),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            // سرسلامت + پیشرفت
            GlassCard(
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('سلام، ${auth.userName ?? 'ورزشکار'} 👋',
                            style: const TextStyle(
                                fontSize: 18, fontWeight: FontWeight.w900)),
                        const SizedBox(height: 4),
                        Text(
                          exercises.isEmpty
                              ? 'برنامه‌ای برای امروز نیست'
                              : '${exercises.length} حرکت امروز — ${(todayState.progress(exercises.length) * 100).round()}٪ انجام شد',
                          style: TextStyle(color: MpColors.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: 64,
                    height: 64,
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        CircularProgressIndicator(
                          value: exercises.isEmpty
                              ? 0
                              : todayState.progress(exercises.length),
                          strokeWidth: 6,
                          backgroundColor: MpColors.surface,
                          color: MpColors.primary,
                        ),
                        Center(
                          child: Text(
                            '${(todayState.progress(exercises.length) * 100).round()}٪',
                            style: const TextStyle(
                                fontSize: 13, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 400.ms).slideY(begin: -0.15),

            const SizedBox(height: 14),
            programAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(40),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => GlassCard(
                child: Column(
                  children: [
                    const Icon(Icons.wifi_off, color: MpColors.danger, size: 40),
                    const SizedBox(height: 8),
                    Text('خطا در دریافت برنامه: $e',
                        textAlign: TextAlign.center),
                    const SizedBox(height: 10),
                    OutlinedButton(
                      onPressed: () => ref.invalidate(myProgramsProvider),
                      child: const Text('تلاش دوباره'),
                    ),
                  ],
                ),
              ),
              data: (_) {
                if (exercises.isEmpty) {
                  return GlassCard(
                    child: Column(
                      children: [
                        const Icon(Icons.fitness_center,
                            size: 44, color: MpColors.primary),
                        const SizedBox(height: 10),
                        const Text('هنوز برنامه‌ای ندارید',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 6),
                        Text('با چند پرسش ساده، برنامهٔ اختصاصی شما ساخته می‌شود',
                            style: TextStyle(color: MpColors.textSecondary)),
                        const SizedBox(height: 14),
                        FilledButton.icon(
                          onPressed: () => context.push('/intake'),
                          icon: const Icon(Icons.auto_awesome),
                          label: const Text('ساخت برنامهٔ اختصاصی'),
                        ),
                      ],
                    ),
                  );
                }
                return Column(
                  children: [
                    for (var i = 0; i < exercises.length; i++)
                      _ExerciseTile(
                        index: i,
                        exercise: exercises[i],
                        done: todayState.done.contains(i),
                      )
                          .animate()
                          .fadeIn(delay: (80 * i).ms, duration: 350.ms)
                          .slideX(begin: 0.08),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ExerciseTile extends ConsumerWidget {
  const _ExerciseTile({required this.index, required this.exercise, required this.done});

  final int index;
  final Map<String, dynamic> exercise;
  final bool done;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () =>
              ref.read(todayControllerProvider.notifier).toggle(index),
          child: Row(
            children: [
              AnimatedScale(
                scale: done ? 1.12 : 1.0,
                duration: const Duration(milliseconds: 220),
                curve: Curves.easeOutBack,
                child: Icon(
                  done ? Icons.check_circle : Icons.circle_outlined,
                  size: 30,
                  color: done ? MpColors.primary : MpColors.textSecondary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      (exercise['exercise_name'] as String?) ??
                          'حرکت ${exercise['exercise_id'] ?? ''}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        decoration: done ? TextDecoration.lineThrough : null,
                        color: done ? MpColors.textSecondary : MpColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${exercise['sets']} ست × ${exercise['reps']} — استراحت ${exercise['rest_seconds']} ثانیه',
                      style: TextStyle(
                          fontSize: 12, color: MpColors.textSecondary),
                    ),
                  ],
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: MpColors.primary.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text('${exercise['load_pct']}٪ بار',
                    style: const TextStyle(
                        fontSize: 11, color: MpColors.primaryLight)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
