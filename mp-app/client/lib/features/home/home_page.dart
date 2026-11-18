/// خانهٔ کلاینت — گرید دسته‌بندی‌شدهٔ بخش‌ها (الگوی سوپر-اپ) + جست‌وجو + بنر.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';

import '../../core/app_state.dart';
import '../../core/membership.dart';
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
          Row(
            children: [
              Expanded(child: _SearchBar(controller: _searchCtrl)),
              const SizedBox(width: 10),
              const _NotificationsButton(),
              const SizedBox(width: 8),
              // M22-c4: ورودی پروفایل (قبلاً صفحه بدون مسیر/ورودی بود)
              Material(
                color: MpColors.surface.withOpacity(0.7),
                borderRadius: BorderRadius.circular(16),
                child: InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () => context.push('/profile'),
                  child: const Padding(
                    padding: EdgeInsets.all(11),
                    child: Icon(
                      Icons.person_outline,
                      color: MpColors.primaryLight,
                      size: 24,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const _SubscriptionBanner()
              .animate()
              .fadeIn(duration: 450.ms)
              .slideY(begin: -0.12),
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
          const _SectionsGrid().animate().fadeIn(
            delay: 120.ms,
            duration: 450.ms,
          ),
          const SizedBox(height: 20),
          _QuickCheckInCard(onTap: () => context.push('/checkin'))
              .animate()
              .fadeIn(delay: 240.ms)
              .slideY(begin: 0.15),
        ],
      ),
    );
  }
}

class _NotificationsButton extends ConsumerWidget {
  const _NotificationsButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(myUnreadNotificationsCountProvider);
    return Material(
      color: MpColors.surface.withOpacity(0.7),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push('/notifications'),
        child: SizedBox(
          width: 46,
          height: 46,
          child: Stack(
            children: [
              const Center(
                child: Icon(
                  Icons.notifications_outlined,
                  color: MpColors.primaryLight,
                  size: 24,
                ),
              ),
              if (count > 0)
                Positioned(
                  top: 3,
                  right: 3,
                  child: Container(
                    constraints: const BoxConstraints(
                      minWidth: 17,
                      minHeight: 17,
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    decoration: const BoxDecoration(
                      color: MpColors.danger,
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      count > 9 ? '۹+' : _toPersianDigits('$count'),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        height: 1,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
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
        child: Transform.translate(
          offset: Offset(0, 12 * (1 - t)),
          child: child,
        ),
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

/// بنر وضعیت اشتراک — از دادهٔ واقعی، نه متن ثابت.
///
/// M61/D5 + M72: بنر فقط از تاریخچهٔ واقعی `/members/{id}/memberships` داده می‌گیرد.
/// حالت‌ها: active (با تاریخ پایان و روز باقی‌مانده)، expired (از status یا مرز
/// expires_at)، بدون اشتراک، و unknown برای دادهٔ ناقص/نامعتبر. تا لحظهٔ پایان
/// اعتبار مثبت است؛ در لحظهٔ `expires_at` یا پس از آن active نمایش داده نمی‌شود.
/// Loading و خطا بنر را پنهان می‌کنند؛ هیچ روز، تاریخ یا پیشنهاد تجاری ساخته نمی‌شود.
class _SubscriptionBanner extends ConsumerWidget {
  const _SubscriptionBanner();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final memberships = ref.watch(myMembershipsProvider);
    return memberships.when(
      loading: () => const SizedBox(height: 84),
      error: (_, __) => const SizedBox.shrink(),
      data: (rows) {
        final summary = summarizeMemberships(rows);
        final membership = summary.membership;
        final expiryLabel = summary.expiresAt == null
            ? 'تاریخ پایان نامعلوم'
            : 'تاریخ پایان: ${formatJalaliDate(summary.expiresAt!.toLocal())}';
        final daysText = summary.daysRemaining == null
            ? 'اعتبار نامعلوم'
            : '${summary.daysRemaining} روز باقی‌مانده';
        final (title, body, color, icon) = switch (summary.status) {
          MembershipDisplayStatus.active => (
            'اشتراک فعال',
            '${membership?['plan_name'] ?? 'پلن باشگاه'} · $expiryLabel · $daysText',
            MpColors.primary,
            Icons.verified_outlined,
          ),
          MembershipDisplayStatus.expired => (
            'اشتراک منقضی شده',
            '$expiryLabel · برای تمدید، با پذیرش باشگاه در ارتباط باشید.',
            MpColors.accent,
            Icons.info_outline,
          ),
          MembershipDisplayStatus.none => (
            'اشتراک فعالی ندارید',
            'برای فعال‌سازی یا تمدید، با پذیرش باشگاه در ارتباط باشید.',
            MpColors.accent,
            Icons.info_outline,
          ),
          MembershipDisplayStatus.unknown => (
            'وضعیت اشتراک نامعلوم',
            'تاریخ پایان از دادهٔ دریافتی قابل‌تأیید نیست؛ با پذیرش باشگاه تماس بگیرید.',
            MpColors.accent,
            Icons.help_outline,
          ),
        };
        return TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: 1),
          duration: const Duration(milliseconds: 450),
          curve: Curves.easeOutCubic,
          builder: (context, t, child) => Opacity(
            opacity: t,
            child: Transform.translate(
              offset: Offset(0, 16 * (1 - t)),
              child: child,
            ),
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
                      colors: [color, color.withOpacity(0.6)],
                      begin: Alignment.topRight,
                      end: Alignment.bottomLeft,
                    ),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(icon, color: Colors.white, size: 28),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: MpColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        body,
                        style: TextStyle(
                          fontSize: 12,
                          color: MpColors.textSecondary,
                          height: 1.6,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

String _toPersianDigits(String value) => value.replaceAllMapped(
  RegExp(r'\d'),
  (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
);

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
    _SectionItem('برنامهٔ اختصاصی من', Icons.fitness_center, [
      Color(0xFF00B86A),
      Color(0xFF00995A),
    ], '/intake'),
    _SectionItem('پیکرسنجی', Icons.show_chart, [
      Color(0xFF38BDF8),
      Color(0xFF0EA5E9),
    ], '/bodycomp'),
    _SectionItem('تغذیه', Icons.restaurant, [
      Color(0xFFF59E0B),
      Color(0xFFD97706),
    ], '/nutrition'),
    _SectionItem('چک‌این', Icons.qr_code, [
      Color(0xFF34D399),
      Color(0xFF059669),
    ], '/checkin'),
    _SectionItem('کیف پول', Icons.account_balance_wallet, [
      Color(0xFF8B5CF6),
      Color(0xFF7C3AED),
    ], '/wallet'),
    _SectionItem('پیشرفت', Icons.trending_up, [
      Color(0xFFF472B6),
      Color(0xFFEC4899),
    ], '/progress'),
    _SectionItem('کلاس‌ها', Icons.groups, [
      Color(0xFFF87171),
      Color(0xFFEF4444),
    ], '/classes'),
    _SectionItem('گفتگو با مربی', Icons.forum_outlined, [
      Color(0xFF34D399),
      Color(0xFF059669),
    ], '/chat'),
    _SectionItem('فروشگاه', Icons.storefront, [
      Color(0xFFA3E635),
      Color(0xFF84CC16),
    ], '/shop'),
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
  const _GridTile({
    required this.item,
    required this.size,
    required this.index,
  });

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
        child: Transform.translate(
          offset: Offset(0, 14 * (1 - t)),
          child: child,
        ),
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
                  style: const TextStyle(
                    fontSize: 11.5,
                    color: MpColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
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
            const Icon(
              Icons.qr_code_scanner,
              color: MpColors.primary,
              size: 28,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'چک‌این سریع',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: MpColors.textPrimary,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'ورود به باشگاه با QR — بدون صف',
                    style: TextStyle(
                      fontSize: 12,
                      color: MpColors.textSecondary,
                    ),
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
