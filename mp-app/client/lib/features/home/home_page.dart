/// خانهٔ کلاینت — گرید دسته‌بندی‌شدهٔ بخش‌ها (الگوی سوپر-اپ) + جست‌وجو + بنر.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          _SearchBar(controller: _searchCtrl),
          const SizedBox(height: 16),
          const _PromoBanner(),
          const SizedBox(height: 20),
          Text(
            'بخش‌ها',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: MpColors.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
          const _SectionsGrid(),
          const SizedBox(height: 20),
          _QuickCheckInCard(onTap: () => context.push('/checkin')),
        ],
      ),
    );
  }
}

class _SearchBar extends StatelessWidget {
  const _SearchBar({required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutCubic,
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(offset: Offset(0, 12 * (1 - t)), child: child),
      ),
      child: TextField(
        controller: controller,
        textDirection: TextDirection.rtl,
        decoration: InputDecoration(
          hintText: 'جست‌وجو در بخش‌ها، حرکات، برنامه‌ها…',
          hintStyle: TextStyle(color: MpColors.textSecondary),
          prefixIcon: Icon(Icons.search, color: MpColors.textSecondary),
          filled: true,
          fillColor: MpColors.surface.withOpacity(0.7),
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide(color: MpColors.primary.withOpacity(0.15)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide(color: MpColors.primary.withOpacity(0.15)),
          ),
        ),
      ),
    );
  }
}

class _PromoBanner extends StatelessWidget {
  const _PromoBanner();

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 450),
      curve: Curves.easeOutCubic,
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(offset: Offset(0, 16 * (1 - t)), child: child),
      ),
      child: GlassCard(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [MpColors.primary, MpColors.primary.withOpacity(0.6)],
                  begin: Alignment.topRight,
                  end: Alignment.bottomLeft,
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.celebration, color: MpColors.accent, size: 28),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'تولدت مبارک! 🎂',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'هدیهٔ باشگاه: ۲۰٪ تخفیف تمدید اشتراک تا پایان هفته',
                    style: TextStyle(fontSize: 12, color: MpColors.textSecondary, height: 1.6),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_left, color: MpColors.accentSoft),
          ],
        ),
      ),
    );
  }
}

class _SectionItem {
  const _SectionItem(this.label, this.icon, this.gradient, this.route);

  final String label;
  final IconData icon;
  final List<Color> gradient;
  final String route;
}

class _SectionsGrid extends StatelessWidget {
  const _SectionsGrid();

  static const _items = <_SectionItem>[
    _SectionItem('برنامهٔ من', Icons.fitness_center, [Color(0xFF00B86A), Color(0xFF00995A)], '/today'),
    _SectionItem('پیکرسنجی', Icons.monitoring, [Color(0xFF38BDF8), Color(0xFF0EA5E9)], '/bodycomp'),
    _SectionItem('تغذیه', Icons.restaurant, [Color(0xFFF59E0B), Color(0xFFD97706)], '/nutrition'),
    _SectionItem('چک‌این', Icons.qr_code, [Color(0xFF34D399), Color(0xFF059669)], '/checkin'),
    _SectionItem('کیف پول', Icons.account_balance_wallet, [Color(0xFF8B5CF6), Color(0xFF7C3AED)], '/wallet'),
    _SectionItem('پیشرفت', Icons.trending_up, [Color(0xFFF472B6), Color(0xFFEC4899)], '/progress'),
    _SectionItem('کلاس‌ها', Icons.groups, [Color(0xFFF87171), Color(0xFFEF4444)], '/classes'),
    _SectionItem('فروشگاه', Icons.storefront, [Color(0xFFA3E635), Color(0xFF84CC16)], '/shop'),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        // ۴ ستونه در موبایل — همان حس اسنپ
        const crossCount = 4;
        final tile = (constraints.maxWidth - 3 * 12) / crossCount;
        return Wrap(
          spacing: 12,
          runSpacing: 16,
          children: [
            for (var i = 0; i < _items.length; i++)
              _GridTile(item: _items[i], size: tile, index: i),
          ],
        );
      },
    );
  }
}

class _GridTile extends StatefulWidget {
  const _GridTile({required this.item, required this.size, required this.index});

  final _SectionItem item;
  final double size;
  final int index;

  @override
  State<_GridTile> createState() => _GridTileState();
}

class _GridTileState extends State<_GridTile> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final item = widget.item;
    // ورود پلکانی آیتم‌ها (staggered)
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: 320 + widget.index * 45),
      curve: Curves.easeOutCubic,
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(offset: Offset(0, 14 * (1 - t)), child: child),
      ),
      child: GestureDetector(
        onTapDown: (_) => setState(() => _pressed = true),
        onTapCancel: () => setState(() => _pressed = false),
        onTapUp: (_) => setState(() => _pressed = false),
        onTap: () => context.push(item.route),
        child: AnimatedScale(
          scale: _pressed ? 0.92 : 1.0,
          duration: const Duration(milliseconds: 150),
          curve: Curves.easeOut,
          child: SizedBox(
            width: widget.size,
            child: Column(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: item.gradient,
                      begin: Alignment.topRight,
                      end: Alignment.bottomLeft,
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: item.gradient.first.withOpacity(0.35),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Icon(item.icon, color: Colors.white, size: 27),
                ),
                const SizedBox(height: 8),
                Text(
                  item.label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 11.5, color: MpColors.textPrimary, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _QuickCheckInCard extends StatelessWidget {
  const _QuickCheckInCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        child: Row(
          children: [
            const Icon(Icons.qr_code_scanner, color: MpColors.primary, size: 28),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'چک‌این سریع',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'ورود به باشگاه با QR — بدون صف',
                    style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_left, color: MpColors.textSecondary),
          ],
        ),
      ),
    );
  }
}
