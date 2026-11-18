/// کارت شیشه‌ای (glassmorphism) — همگام با Studio.
library;

import 'dart:ui';

import 'package:flutter/material.dart';

import '../../core/theme.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: MpColors.surface.withOpacity(0.55),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: MpColors.primary.withOpacity(0.15)),
          ),
          child: child,
        ),
      ),
    );
  }
}
