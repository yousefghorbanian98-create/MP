/// صفحهٔ «برنامهٔ امروز» — مطابق موکاپ 02-client-today-workout.png
/// انیمیشن‌ها با flutter_animate (معادل فلاتری Framer Motion).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'today_controller.dart';

class TodayPage extends ConsumerWidget {
  const TodayPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(todayControllerProvider);
    final controller = ref.read(todayControllerProvider.notifier);

    return Scaffold(
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
                child: Row(
                  children: [
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('سلام، علی 👋', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          Text('برنامهٔ امروزت آماده است', style: TextStyle(color: MpColors.textSecondary)),
                        ],
                      ),
                    ),
                    _ProgressRing(progress: state.progress),
                  ],
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.all(20),
              sliver: SliverList.separated(
                itemCount: state.exercises.length,
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemBuilder: (context, i) {
                  final ex = state.exercises[i];
                  return GlassCard(
                    child: Row(
                      children: [
                        Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(14),
                            color: MpColors.primary.withOpacity(0.12),
                          ),
                          child: const Icon(Icons.fitness_center, color: MpColors.primaryLight),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(ex.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                              const SizedBox(height: 6),
                              Wrap(
                                spacing: 8,
                                children: [
                                  _Chip(label: '${ex.sets} ست'),
                                  _Chip(label: ex.reps),
                                  _Chip(label: '${ex.loadPct}٪ ۱RM', gold: true),
                                  _Chip(label: '${ex.restSeconds} ثانیه استراحت'),
                                ],
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          onPressed: () => controller.toggle(i),
                          icon: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 250),
                            transitionBuilder: (child, anim) =>
                                ScaleTransition(scale: anim, child: child),
                            child: Icon(
                              ex.done ? Icons.check_circle : Icons.circle_outlined,
                              key: ValueKey(ex.done),
                              color: ex.done ? MpColors.primary : MpColors.textSecondary,
                              size: 30,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                      .animate()
                      .fadeIn(delay: (80 * i).ms, duration: 350.ms)
                      .slideX(begin: 0.06, end: 0, curve: Curves.easeOut);
                },
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: MpColors.surface.withOpacity(0.9),
        indicatorColor: MpColors.primary.withOpacity(0.2),
        selectedIndex: 0,
        destinations: const [
          NavigationDestination(icon: Icon(Icons.today_outlined), label: 'امروز'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), label: 'پیشرفت'),
          NavigationDestination(icon: Icon(Icons.qr_code_scanner), label: 'چک‌این'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'پروفایل'),
        ],
      ),
    );
  }
}

class _ProgressRing extends StatelessWidget {
  const _ProgressRing({required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 72,
      height: 72,
      child: Stack(
        fit: StackFit.expand,
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: 1,
            strokeWidth: 6,
            color: MpColors.primary.withOpacity(0.15),
          ),
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: progress),
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeOut,
            builder: (_, value, __) => CircularProgressIndicator(
              value: value,
              strokeWidth: 6,
              strokeCap: StrokeCap.round,
              color: MpColors.primary,
            ),
          ),
          Center(
            child: Text('${(progress * 100).round()}٪', style: const TextStyle(fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label, this.gold = false});

  final String label;
  final bool gold;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: (gold ? MpColors.accent : MpColors.primary).withOpacity(0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          color: gold ? MpColors.accentSoft : MpColors.primaryLight,
        ),
      ),
    );
  }
}
