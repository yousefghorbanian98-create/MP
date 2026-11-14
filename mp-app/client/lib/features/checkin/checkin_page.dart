/// صفحهٔ چک‌این — برای کیوسک/موبایل (US-106).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class CheckInPage extends StatelessWidget {
  const CheckInPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 220,
                height: 260,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(color: MpColors.primary.withOpacity(0.5), width: 2),
                  color: MpColors.primary.withOpacity(0.06),
                ),
                child: const Center(
                  child: Icon(Icons.face_retouching_natural, size: 90, color: MpColors.primaryLight),
                ),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .fadeIn(duration: 1200.ms)
                  .then()
                  .shimmer(duration: 1200.ms, color: MpColors.primary.withOpacity(0.25)),
              const SizedBox(height: 28),
              const Text('برای ورود، جلوی دوربین بایستید',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('تشخیص چهره با liveness — در صورت خطا از QR استفاده کنید',
                  style: TextStyle(color: MpColors.textSecondary, fontSize: 12)),
              const SizedBox(height: 28),
              GlassCard(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.qr_code_2, color: MpColors.accent),
                    const SizedBox(width: 10),
                    Text('ورود با QR', style: TextStyle(color: MpColors.accentSoft)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
