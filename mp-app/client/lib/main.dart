/// MP Client — اپ عضو Muscle Paradise (Flutter).
/// RTL فارسی کامل، حالت تاریک پیش‌فرض، فونت Vazirmatn.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router.dart';
import 'core/session.dart';
import 'core/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final container = ProviderContainer();
  final loggedIn = await container.read(authProvider.notifier).restore();
  runApp(
    UncontrolledProviderScope(
      container: container,
      child: MpClientApp(initialRoute: loggedIn ? '/home' : '/otp'),
    ),
  );
}

class MpClientApp extends StatelessWidget {
  const MpClientApp({super.key, this.initialRoute = '/home'});

  final String initialRoute;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Muscle Paradise',
      debugShowCheckedModeBanner: false,
      theme: mpTheme(),
      darkTheme: mpTheme(),
      themeMode: ThemeMode.dark, // حالت تاریک default (برند MP)
      routerConfig: createMpRouter(initialLocation: initialRoute),
      locale: const Locale('fa', 'IR'),
      supportedLocales: const [Locale('fa', 'IR'), Locale('en', 'US')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) => Directionality(
        textDirection: TextDirection.rtl, // RTL کامل فارسی
        child: child!,
      ),
    );
  }
}
