/// کلاس‌های گروهی — جدول زمانی (M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ClassesPage extends StatelessWidget {
  const ClassesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final classes = <({String name, String time, String coach, int capacity})>[
      (name: 'یوگا', time: 'شنبه ۱۸:۰۰', coach: 'مربی احمدی', capacity: 6),
      (name: 'اینتروال (HIIT)', time: 'یکشنبه ۲۰:۰۰', coach: 'مربی کریمی', capacity: 3),
      (name: 'پیلاتس', time: 'سه‌شنبه ۱۷:۰۰', coach: 'مربی موسوی', capacity: 10),
      (name: 'اسپینینگ', time: 'پنجشنبه ۱۹:۰۰', coach: 'مربی احمدی', capacity: 0),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('کلاس‌ها'), backgroundColor: MpColors.background, surfaceTintColor: Colors.transparent),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          for (final c in classes)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                child: Row(
                  children: [
                    Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(
                        color: MpColors.primary.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.groups, color: MpColors.primaryLight),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(c.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
                          const SizedBox(height: 3),
                          Text('${c.time} — ${c.coach}', style: const TextStyle(fontSize: 11.5, color: MpColors.textSecondary)),
                        ],
                      ),
                    ),
                    c.capacity > 0
                        ? Text('${c.capacity} ظرفیت', style: const TextStyle(fontSize: 11.5, color: MpColors.primaryLight, fontWeight: FontWeight.w700))
                        : const Text('تکمیل', style: TextStyle(fontSize: 11.5, color: MpColors.danger, fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
