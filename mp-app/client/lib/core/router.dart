/// مسیریابی go_router — شل ۴ تبی + مسیرهای بخش‌ها (M19).
library;

import 'package:go_router/go_router.dart';

import '../features/bodycomp/bodycomp_page.dart';
import '../features/checkin/checkin_page.dart';
import '../features/classes/classes_page.dart';
import '../features/nutrition/nutrition_page.dart';
import '../features/shell/app_shell.dart';
import '../features/shop/shop_page.dart';
import '../features/wallet/wallet_page.dart';

final GoRouter mpRouter = GoRouter(
  initialLocation: '/home',
  routes: [
    // شل تبی — خانه/برنامه/پیشرفت/پروفایل درون AppShell
    GoRoute(
      path: '/home',
      pageBuilder: (context, state) => const NoTransitionPage(child: AppShell()),
    ),
    // مسیرهای بخش‌ها (push از گرید خانه)
    GoRoute(
      path: '/bodycomp',
      pageBuilder: (context, state) => const NoTransitionPage(child: BodyCompPage()),
    ),
    GoRoute(
      path: '/nutrition',
      pageBuilder: (context, state) => const NoTransitionPage(child: NutritionPage()),
    ),
    GoRoute(
      path: '/checkin',
      pageBuilder: (context, state) => const NoTransitionPage(child: CheckInPage()),
    ),
    GoRoute(
      path: '/wallet',
      pageBuilder: (context, state) => const NoTransitionPage(child: WalletPage()),
    ),
    GoRoute(
      path: '/classes',
      pageBuilder: (context, state) => const NoTransitionPage(child: ClassesPage()),
    ),
    GoRoute(
      path: '/shop',
      pageBuilder: (context, state) => const NoTransitionPage(child: ShopPage()),
    ),
  ],
);
