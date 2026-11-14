/// شل اپ کلاینت — ناوبری ۴ تبی (سبک سوپر-اپ) با میکرو-ترنزیشن.
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../home/home_page.dart';
import '../profile/profile_page.dart';
import '../progress/progress_page.dart';
import '../today/today_page.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  static const _tabs = <Widget>[
    HomePage(),
    TodayPage(),
    ProgressPage(),
    ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 250),
        switchInCurve: Curves.easeOutCubic,
        transitionBuilder: (child, animation) {
          // ترنزیشن نرم: fade + slide از پایین
          return FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0, 0.04),
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          );
        },
        child: KeyedSubtree(key: ValueKey(_index), child: _tabs[_index]),
      ),
      bottomNavigationBar: _MpBottomNav(
        index: _index,
        onChanged: (i) => setState(() => _index = i),
      ),
    );
  }
}

class _MpBottomNav extends StatelessWidget {
  const _MpBottomNav({required this.index, required this.onChanged});

  final int index;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    const items = <({IconData icon, IconData active, String label})>[
      (icon: Icons.home_outlined, active: Icons.home, label: 'خانه'),
      (icon: Icons.fitness_center_outlined, active: Icons.fitness_center, label: 'برنامه'),
      (icon: Icons.trending_up_outlined, active: Icons.trending_up, label: 'پیشرفت'),
      (icon: Icons.person_outline, active: Icons.person, label: 'پروفایل'),
    ];
    return Container(
      decoration: BoxDecoration(
        color: MpColors.surface.withOpacity(0.92),
        border: Border(top: BorderSide(color: MpColors.primary.withOpacity(0.18))),
      ),
      child: SafeArea(
        child: SizedBox(
          height: 64,
          child: Row(
            children: [
              for (var i = 0; i < items.length; i++)
                Expanded(
                  child: InkWell(
                    onTap: () => onChanged(i),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // نشانگر متحرک بالای تب فعال
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          curve: Curves.easeOutCubic,
                          height: 3,
                          width: i == index ? 24 : 0,
                          margin: const EdgeInsets.only(bottom: 6),
                          decoration: BoxDecoration(
                            color: MpColors.primary,
                            borderRadius: BorderRadius.circular(999),
                            boxShadow: [
                              BoxShadow(
                                color: MpColors.primary.withOpacity(0.5),
                                blurRadius: 8,
                              ),
                            ],
                          ),
                        ),
                        AnimatedScale(
                          scale: i == index ? 1.12 : 1.0,
                          duration: const Duration(milliseconds: 200),
                          curve: Curves.easeOutBack,
                          child: Icon(
                            i == index ? items[i].active : items[i].icon,
                            color: i == index ? MpColors.primary : MpColors.textSecondary,
                            size: 24,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          items[i].label,
                          style: TextStyle(
                            fontSize: 11,
                            color: i == index ? MpColors.primary : MpColors.textSecondary,
                            fontWeight: i == index ? FontWeight.w700 : FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
