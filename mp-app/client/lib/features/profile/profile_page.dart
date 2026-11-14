/// پروفایل کلاینت — فقط دادهٔ خود کاربر (M18).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          Center(
            child: Column(
              children: [
                Container(
                  width: 96,
                  height: 96,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [MpColors.primary, MpColors.primary.withOpacity(0.5)],
                      begin: Alignment.topRight,
                      end: Alignment.bottomLeft,
                    ),
                    boxShadow: [BoxShadow(color: MpColors.primary.withOpacity(0.35), blurRadius: 20)],
                  ),
                  child: const Icon(Icons.person, size: 48, color: Colors.white),
                ),
                const SizedBox(height: 12),
                const Text('علی رضایی', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: MpColors.textPrimary)),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                  decoration: BoxDecoration(
                    color: MpColors.accent.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: MpColors.accent.withOpacity(0.4)),
                  ),
                  child: const Text('عضو طلایی ✨', style: TextStyle(fontSize: 12, color: MpColors.accentSoft, fontWeight: FontWeight.w700)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          GlassCard(
            child: Column(
              children: const [
                _ProfileRow('اشتراک', 'سالانه — تا ۱۴ آبان ۱۴۰۶', Icons.workspace_premium),
                Divider(height: 1),
                _ProfileRow('تاریخ تولد', '۲۵/۰۵/۱۳۷۰', Icons.cake),
                Divider(height: 1),
                _ProfileRow('شمارهٔ تماس', '۰۹۱۲••••۳۴۵', Icons.phone),
              ],
            ),
          ),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              children: const [
                _ProfileRow('اعلان‌ها', 'فعال', Icons.notifications_outlined),
                Divider(height: 1),
                _ProfileRow('حریم خصوصی و داده‌ها', 'مدیریت رضایت بیومتریک', Icons.shield_outlined),
                Divider(height: 1),
                _ProfileRow('خروج از حساب', '', Icons.logout),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow(this.title, this.value, this.icon);

  final String title;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 13),
      child: Row(
        children: [
          Icon(icon, size: 20, color: MpColors.primaryLight),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(fontSize: 13.5, color: MpColors.textPrimary, fontWeight: FontWeight.w600))),
          Text(value, style: const TextStyle(fontSize: 12, color: MpColors.textSecondary)),
          const SizedBox(width: 4),
          const Icon(Icons.chevron_left, size: 18, color: MpColors.textSecondary),
        ],
      ),
    );
  }
}
