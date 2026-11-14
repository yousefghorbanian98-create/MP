/// MP Client — اپ عضو Muscle Paradise (Flutter).
/// RTL فارسی کامل، حالت تاریک پیش‌فرض، فونت Vazirmatn.
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router.dart';
import 'core/theme.dart';

void main() {
  runApp(const ProviderScope(child: MpClientApp()));
}

class MpClientApp extends StatelessWidget {
  const MpClientApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Muscle Paradise',
      debugShowCheckedModeBanner: false,
      theme: mpTheme(),
      darkTheme: mpTheme(),
      themeMode: ThemeMode.dark, // حالت تاریک default (برند MP)
      routerConfig: mpRouter,
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
