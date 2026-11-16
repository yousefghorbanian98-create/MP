/// فروشگاه باشگاه — مکمل/تجهیزات با دادهٔ **واقعی** از API (M59).
///
/// تاریخچه: تا پیش از M59 این صفحه چهار محصول hardcode داشت و هیچ اتصالی به
/// بک‌اند نداشت؛ یعنی «فروشگاه» در دمو فقط یک تصویر بود. حالا:
/// کاتالوگ ← `GET /shop/products`، سبد ← `GET/POST /shop/cart`،
/// تسویه ← `POST /shop/checkout` (کیف‌پول)، سفارش‌ها ← `GET /shop/orders`.
///
/// قاعدهٔ امنیتی که کلاینت رعایت می‌کند: **هیچ قیمتی از این صفحه به سرور
/// فرستاده نمی‌شود.** فقط `product_id` و `qty`؛ مبلغ را سرور از DB می‌سازد.
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

/// ارقام فارسی — قرارداد کل پروژه (کاربر فارسی‌زبان). یک‌جا تعریف می‌شود تا
/// هر صفحه ارقام لاتین نشان ندهد؛ پیش‌تر `fa()` در استودیو بود و Dart نداشت.
String faDigits(Object value) {
  const latin = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
  const persian = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  var out = value.toString();
  for (var i = 0; i < 10; i++) {
    out = out.replaceAll(latin[i], persian[i]);
  }
  return out;
}

/// مبلغ با جداکنندهٔ هزارگان فارسی: 2500000 ← ۲٬۵۰۰٬۰۰۰ ریال
String _rial(num n) {
  final grouped =
      n.toString().replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]}٬');
  return '${faDigits(grouped)} ریال';
}

class ShopPage extends ConsumerWidget {
  const ShopPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final products = ref.watch(shopProductsProvider);
    final cart = ref.watch(cartProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('فروشگاه'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
        actions: [
          cart.maybeWhen(
            data: (c) {
              final count = (c['count'] as num?)?.toInt() ?? 0;
              return Padding(
                padding: const EdgeInsets.only(left: 12),
                child: TextButton.icon(
                  onPressed: count == 0 ? null : () => _openCart(context, ref),
                  icon: Badge(
                    isLabelVisible: count > 0,
                    label: Text('$count'),
                    child: const Icon(Icons.shopping_cart_outlined),
                  ),
                  label: const Text('سبد'),
                ),
              );
            },
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
      body: products.when(
        loading: () => const _ShopSkeleton(),
        error: (e, _) => Padding(
          padding: const EdgeInsets.all(24),
          child: GlassCard(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.wifi_off, color: MpColors.danger, size: 40),
                const SizedBox(height: 8),
                Text('دریافت محصولات ناموفق بود\n$e', textAlign: TextAlign.center),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () {
                    ref.invalidate(shopProductsProvider);
                    ref.invalidate(cartProvider);
                  },
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'هنوز محصولی ثبت نشده است.\nمدیر باشگاه می‌تواند از پنل استودیو محصول اضافه کند.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(shopProductsProvider);
              ref.invalidate(cartProvider);
            },
            child: GridView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 0.72,
              ),
              itemCount: items.length,
              itemBuilder: (context, i) => _ProductCard(
                product: items[i],
                onAdd: () => _add(context, ref, items[i]),
              )
                  .animate()
                  .fadeIn(duration: 220.ms, delay: (30 * i).ms)
                  .slideY(begin: 0.08, end: 0, curve: Curves.easeOutCubic),
            ),
          );
        },
      ),
    );
  }

  Future<void> _add(BuildContext context, WidgetRef ref, Map<String, dynamic> product) async {
    final api = ref.read(apiClientProvider);
    try {
      await api.post('/shop/cart', {'product_id': product['id'], 'qty': 1});
      ref.invalidate(cartProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('«${product['title']}» به سبد اضافه شد')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _openCart(BuildContext context, WidgetRef ref) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _CartSheet(onDone: () => ref.invalidate(cartProvider)),
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({required this.product, required this.onAdd});

  final Map<String, dynamic> product;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final stock = (product['stock_qty'] as num?)?.toInt() ?? 0;
    final price = (product['price_rial'] as num?) ?? 0;
    final compare = (product['compare_at_rial'] as num?);
    final image = (product['image_url'] as String?) ?? '';
    final soldOut = stock == 0;

    return GlassCard(
      padding: const EdgeInsets.all(10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: image.isEmpty
                  ? Container(
                      width: double.infinity,
                      color: MpColors.primary.withOpacity(0.10),
                      child: const Icon(Icons.inventory_2_outlined, size: 40, color: MpColors.primaryLight),
                    )
                  : Image.network(
                      image,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                        color: MpColors.primary.withOpacity(0.10),
                        child: const Icon(Icons.image_not_supported_outlined, color: MpColors.primaryLight),
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            (product['title'] as String?) ?? '',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: MpColors.textPrimary),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: Text(
                  _rial(price),
                  style: const TextStyle(fontSize: 11.5, color: MpColors.accentSoft, fontWeight: FontWeight.w800),
                ),
              ),
              if (compare != null && compare > price)
                Text(
                  _rial(compare),
                  style: const TextStyle(
                    fontSize: 10,
                    color: MpColors.textSecondary,
                    decoration: TextDecoration.lineThrough,
                  ),
                ),
            ],
          ),
          const SizedBox(height: 6),
          SizedBox(
            width: double.infinity,
            height: 32,
            child: FilledButton(
              onPressed: soldOut ? null : onAdd,
              style: FilledButton.styleFrom(padding: EdgeInsets.zero),
              child: Text(soldOut ? 'ناموجود' : 'افزودن به سبد', style: const TextStyle(fontSize: 11.5)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ShopSkeleton extends StatelessWidget {
  const _ShopSkeleton();

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 0.72,
      ),
      itemCount: 4,
      // بدون انیمیشن تکرارشونده: `repeat()` باعث می‌شود `pumpAndSettle` در
      // تست هرگز «آرام» نشود و تست بارگذاری به تایم‌اوت بخورد. شیمر یک‌باره
      // همان حس «در حال آمدن» را می‌دهد.
      itemBuilder: (_, __) => GlassCard(
        padding: const EdgeInsets.all(10),
        child: Column(
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white10,
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Container(height: 12, color: Colors.white10),
            const SizedBox(height: 6),
            Container(height: 12, width: 80, color: Colors.white10),
          ],
        ),
      ).animate().fadeIn(duration: 260.ms),
    );
  }
}

/// شیت سبد + تسویه از کیف‌پول. مبلغ نمایشی از سرور است.
class _CartSheet extends ConsumerStatefulWidget {
  const _CartSheet({required this.onDone});

  final VoidCallback onDone;

  @override
  ConsumerState<_CartSheet> createState() => _CartSheetState();
}

class _CartSheetState extends ConsumerState<_CartSheet> {
  bool _busy = false;

  Future<void> _checkout() async {
    final api = ref.read(apiClientProvider);
    setState(() => _busy = true);
    try {
      final res = await api.post('/shop/checkout', {'method': 'wallet'});
      // M60/R16 — `res` بدنهٔ خام API است و نوعش dynamic؛ cast مستقیم به Map
      // همان الگویی است که در M59 سه صفحه را بی‌صدا شکست. `Map.from` هم
      // نوع را صریح می‌کند و هم اگر بدنه List باشد پیام روشن می‌دهد.
      final orderId = Map<String, dynamic>.from(res as Map)['order_id'];
      ref.invalidate(cartProvider);
      ref.invalidate(walletProvider);
      ref.invalidate(shopOrdersProvider);
      widget.onDone();
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('سفارش #$orderId ثبت شد و از کیف‌پول پرداخت شد')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider);
    final gateways = ref.watch(gatewaysProvider);
    return Container(
      decoration: const BoxDecoration(
        color: MpColors.background,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: cart.when(
        loading: () => const SizedBox(height: 160, child: Center(child: CircularProgressIndicator())),
        error: (e, _) => SizedBox(height: 120, child: Center(child: Text('$e'))),
        data: (c) {
          final items = ((c['items'] as List?) ?? const []).cast<Map<String, dynamic>>();
          final total = (c['total_rial'] as num?) ?? 0;
          if (items.isEmpty) {
            return const SizedBox(height: 140, child: Center(child: Text('سبد خالی است')));
          }
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('سبد خرید', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              ...items.map(
                (line) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    '${line['title']}${(line['variant_label'] as String?)?.isNotEmpty == true ? ' — ${line['variant_label']}' : ''}',
                    style: const TextStyle(fontSize: 13),
                  ),
                  subtitle: Text(_rial((line['line_total_rial'] as num?) ?? 0)),
                  trailing: Text('×${line['qty']}'),
                ),
              ),
              const Divider(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('قابل پرداخت'),
                  Text(_rial(total), style: const TextStyle(fontWeight: FontWeight.w800, color: MpColors.accentSoft)),
                ],
              ),
              const SizedBox(height: 4),
              gateways.maybeWhen(
                data: (gs) {
                  final enabled = gs.where((g) => g['is_enabled'] == true).toList();
                  if (enabled.isEmpty) return const SizedBox.shrink();
                  return Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Wrap(
                      spacing: 6,
                      children: enabled
                          .map((g) => Chip(
                                label: Text(
                                  '${g['title']}${(g['card_number_masked'] as String?)?.isNotEmpty == true ? ' · ${g['card_number_masked']}' : ''}',
                                  style: const TextStyle(fontSize: 10.5),
                                ),
                              ))
                          .toList(),
                    ),
                  );
                },
                orElse: () => const SizedBox.shrink(),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 46,
                child: FilledButton(
                  onPressed: _busy ? null : _checkout,
                  child: _busy
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('پرداخت از کیف‌پول'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
