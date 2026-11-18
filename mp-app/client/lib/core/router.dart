/// مسیریابی go_router — شل ۴ تبی + مسیرهای بخش‌ها (M19).
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'theme.dart';

import '../features/bodycomp/bodycomp_page.dart';
import '../features/checkin/checkin_page.dart';
import '../features/classes/classes_page.dart';
import '../features/chat/member_chat_page.dart';
import '../features/nutrition/nutrition_page.dart';
import '../features/profile/profile_page.dart';
import '../features/progress/progress_page.dart';
import '../features/auth/otp_page.dart';
import '../features/intake/intake_page.dart';
import '../features/notifications/notifications_page.dart';
import '../features/shell/app_shell.dart';
import '../features/shop/shop_page.dart';
import '../features/today/today_page.dart';
import '../features/wallet/wallet_page.dart';

/// پوشش صفحاتِ بدون Scaffold هنگام push مستقیم (خروجی + دکمهٔ بازگشت).
class _PushedSection extends StatelessWidget {
  const _PushedSection({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: child,
    );
  }
}

GoRouter createMpRouter({String initialLocation = '/home'}) => GoRouter(
  initialLocation: initialLocation,
  routes: [
    // شل تبی — خانه/برنامه/پیشرفت/پروفایل درون AppShell
    GoRoute(
      path: '/otp',
      pageBuilder: (context, state) => const NoTransitionPage(child: OtpPage()),
    ),
    GoRoute(
      path: '/intake',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: IntakePage()),
    ),
    GoRoute(
      path: '/home',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: AppShell()),
    ),
    // مسیرهای بخش‌ها (push از گرید خانه)
    GoRoute(
      path: '/bodycomp',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: BodyCompPage()),
    ),
    GoRoute(
      path: '/nutrition',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: NutritionPage()),
    ),
    GoRoute(
      path: '/checkin',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: CheckInPage()),
    ),
    GoRoute(
      path: '/wallet',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: WalletPage()),
    ),
    GoRoute(
      path: '/classes',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: ClassesPage()),
    ),
    GoRoute(
      path: '/chat',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: MemberChatPage()),
    ),
    GoRoute(
      path: '/shop',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: ShopPage()),
    ),
    GoRoute(
      path: '/notifications',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: NotificationsPage()),
    ),
    // M22-c4: مسیرهای گرید خانه که قبلاً route نداشتند (دکمه‌های شکسته)
    GoRoute(
      path: '/today',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: TodayPage()),
    ),
    GoRoute(
      path: '/progress',
      pageBuilder: (context, state) => const NoTransitionPage(
        child: _PushedSection(title: 'پیشرفت', child: ProgressPage()),
      ),
    ),
    GoRoute(
      path: '/profile',
      pageBuilder: (context, state) => const NoTransitionPage(
        child: _PushedSection(title: 'پروفایل', child: ProfilePage()),
      ),
    ),
  ],
);
