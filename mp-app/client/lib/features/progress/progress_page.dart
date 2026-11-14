/// پیشرفت کلاینت — نمای کلی روندها (M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ProgressPage extends StatelessWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          const Text('پیشرفت من', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: MpColors.textPrimary)),
          const SizedBox(height: 16),
          Row(
            children: const [
              Expanded(child: _ProgressTile('چربی بدن', '۱۲٫۴٪', '−۱٫۲٪', Icons.monitoring, MpColors.primary)),
              SizedBox(width: 12),
              Expanded(child: _ProgressTile('وزن', '۷۸٫۵', '−۱٫۶ کیلو', Icons.scale, MpColors.info)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: const [
              Expanded(child: _ProgressTile('حضور', '۱۸ جلسه', 'این ماه', Icons.calendar_month, MpColors.accent)),
              SizedBox(width: 12),
              Expanded(child: _ProgressTile('رکورد اسکوات', '۱۲۰ کیلو', '+۵ کیلو', Icons.fitness_center, MpColors.primaryLight)),
            ],
          ),
          const SizedBox(height: 20),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text('دستاوردهای اخیر', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
                SizedBox(height: 12),
                _Achievement('🏅', '۱۰ جلسهٔ پیوسته', 'بیش از ۱۰ جلسه بدون وقفه'),
                _Achievement('💪', 'رکورد جدید پرس سینه', '۸۰ کیلو × ۵ تکرار'),
                _Achievement('📉', 'کاهش ۲٪ چربی', 'در ۸ هفتهٔ گذشته'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProgressTile extends StatelessWidget {
  const _ProgressTile(this.label, this.value, this.delta, this.icon, this.color);

  final String label;
  final String value;
  final String delta;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: color),
              const SizedBox(width: 6),
              Text(label, style: const TextStyle(fontSize: 11.5, color: MpColors.textSecondary)),
            ],
          ),
          const SizedBox(height: 10),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: MpColors.textPrimary)),
          const SizedBox(height: 4),
          Text(delta, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }
}

class _Achievement extends StatelessWidget {
  const _Achievement(this.emoji, this.title, this.subtitle);

  final String emoji;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 22)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
                const SizedBox(height: 2),
                Text(subtitle, style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
