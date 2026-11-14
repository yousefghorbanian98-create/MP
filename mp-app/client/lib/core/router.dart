/// مسیریابی go_router — RTL، حالت تاریک پیش‌فرض.
library;

import 'package:go_router/go_router.dart';

import '../features/checkin/checkin_page.dart';
import '../features/today/today_page.dart';

final GoRouter mpRouter = GoRouter(
  initialLocation: '/today',
  routes: [
    GoRoute(
      path: '/today',
      pageBuilder: (context, state) => const NoTransitionPage(child: TodayPage()),
    ),
    GoRoute(
      path: '/checkin',
      pageBuilder: (context, state) => const NoTransitionPage(child: CheckInPage()),
    ),
  ],
);
