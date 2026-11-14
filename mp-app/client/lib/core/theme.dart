/// توکن‌های دیزاین — همگام با mp-app/shared/design-tokens.json
library;

import 'package:flutter/material.dart';

abstract final class MpColors {
  static const background = Color(0xFF0B0F14);
  static const surface = Color(0xFF111827);
  static const primary = Color(0xFF00B86A);
  static const primaryLight = Color(0xFF34D399);
  static const accent = Color(0xFFFFD700);
  static const accentSoft = Color(0xFFFDE68A);
  static const textPrimary = Color(0xFFF3F6F8);
  static const textSecondary = Color(0xFF9CA3AF);
  static const danger = Color(0xFFF87171);
}

ThemeData mpTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: const ColorScheme.dark(
      primary: MpColors.primary,
      secondary: MpColors.accent,
      surface: MpColors.surface,
      error: MpColors.danger,
    ),
    scaffoldBackgroundColor: MpColors.background,
    fontFamily: 'Vazirmatn',
  );
  return base.copyWith(
    // کارت‌ها با GlassCard سبک می‌شوند (design tokens مشترک)
    textTheme: base.textTheme.apply(
      bodyColor: MpColors.textPrimary,
      displayColor: MpColors.textPrimary,
    ),
  );
}
