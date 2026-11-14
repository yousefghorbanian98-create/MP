/// فروشگاه باشگاه — مکمل/لوازم (M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ShopPage extends StatelessWidget {
  const ShopPage({super.key});

  @override
  Widget build(BuildContext context) {
    final products = <({String name, String price, IconData icon})>[
      (name: 'پروتئین وی ۱ کیلویی', price: '۲٬۹۰۰٬۰۰۰ ریال', icon: Icons.sports_bar),
      (name: 'کراتین مونوهیدرات', price: '۱٬۴۵۰٬۰۰۰ ریال', icon: Icons.science),
      (name: 'شیکر باشگاه MP', price: '۳۵۰٬۰۰۰ ریال', icon: Icons.local_drink),
      (name: 'دستکش تمرین', price: '۵۸۰٬۰۰۰ ریال', icon: Icons.fitness_center),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('فروشگاه'), backgroundColor: MpColors.background, surfaceTintColor: Colors.transparent),
      body: GridView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 0.82,
        ),
        itemCount: products.length,
        itemBuilder: (context, i) {
          final p = products[i];
          return GlassCard(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: MpColors.primary.withOpacity(0.10),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(p.icon, size: 40, color: MpColors.primaryLight),
                  ),
                ),
                const SizedBox(height: 10),
                Text(p.name, maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
                const SizedBox(height: 4),
                Text(p.price, style: const TextStyle(fontSize: 11.5, color: MpColors.accentSoft, fontWeight: FontWeight.w800)),
              ],
            ),
          );
        },
      ),
    );
  }
}
