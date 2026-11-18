/// رسید سفارش عضو — خواندن از endpoint مالک‌محور، بدون ارسال هیچ مبلغی (M90).
///
/// چرا این فایل هست: `GET /shop/orders/{id}/receipt` از M60/R5 در backend بود
/// (برای چاپ/تحویل در انبار و Studio)، ولی اپ عضو هیچ‌جا مصرفش نمی‌کرد؛ عضو بعد
/// از پرداخت فقط SnackBar «سفارش #۱۲ ثبت شد» را می‌دید و بعد از آن هیچ راهی برای
/// دیدن اقلام، وضعیت تحویل یا مرجع پرداخت نداشت.
///
/// دو قرارداد که این صفحه نگه می‌دارد:
/// ۱) **فقط خواندن.** هیچ `POST`/`PATCH` با مبلغ از این صفحه نمی‌رود؛ جمع‌ها همان
///    است که سرور ساخته (`items_total_rial` و `total_rial`).
/// ۲) **مالکیت در کلاینت هم تأیید می‌شود.** اگر پاسخ `order_id` یا `member_id`
///    نامطابق باشد، رسید نمایش داده نمی‌شود (fail closed) — همان الگوی دفتر
///    کیف‌پول (M83)؛ نمایش دادهٔ سفارش دیگر یعنی نشتی، حتی اگر سرور اشتباه کند.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/membership.dart';
import '../../core/persian_format.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

/// باز کردن شیت رسید از هر جای فروشگاه.
Future<void> showOrderReceipt(BuildContext context, WidgetRef ref, int orderId) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => OrderReceiptSheet(orderId: orderId),
  );
}

/// برچسب فارسی وضعیت. وضعیت ناشناخته دست‌کاری نمی‌شود: همان مقدار خام نمایش
/// داده می‌شود تا اگر سرور status تازه‌ای اضافه کرد، UI دروغ «تأیید شد» نگویید.
String orderStatusLabel(String? status) {
  return switch (status) {
    'pending' => 'در انتظار پرداخت',
    'paid' => 'پرداخت‌شده',
    'failed' => 'ناموفق',
    'cancelled' => 'لغوشده',
    'delivered' => 'تحویل‌شده',
    'refunded' => 'بازگشت داده‌شده',
    null || '' => 'نامشخص',
    // `status` این‌جا non-null است؛ `!` فقط warning analyzer می‌گرفت (CI M90).
    _ => status,
  };
}

/// رسید قابل‌چاپ/قابل‌ارائه در تحویل.
class OrderReceiptSheet extends ConsumerWidget {
  const OrderReceiptSheet({super.key, required this.orderId});

  final int orderId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final receipt = ref.watch(orderReceiptProvider(orderId));
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
      child: receipt.when(
        loading: () => const SizedBox(
          height: 160,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            GlassCard(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.receipt_long_outlined,
                      color: MpColors.danger, size: 34),
                  const SizedBox(height: 8),
                  Text('رسید سفارش #$orderId خوانده نشد\n$e',
                      textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () => ref.invalidate(orderReceiptProvider(orderId)),
                    child: const Text('تلاش دوباره'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('بستن'),
            ),
          ],
        ),
        data: (data) => _ReceiptBody(data: data),
      ),
    );
  }
}

class _ReceiptBody extends StatelessWidget {
  const _ReceiptBody({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final lines = ((data['lines'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final itemsTotal = (data['items_total_rial'] as num?) ?? 0;
    final total = (data['total_rial'] as num?) ?? 0;
    final payment = data['payment'] is Map
        ? Map<String, dynamic>.from(data['payment'] as Map)
        : null;
    final createdAt = _date(data['created_at']);
    final issuedAt = _date(data['issued_at']);
    final receiptNo = (data['receipt_no'] as String?) ?? '';
    final memberName = (data['member_name'] as String?) ?? '';
    final note = (data['note'] as String?)?.trim() ?? '';
    final status = (data['status'] as String?) ?? '';

    // اگر سرور جمع اقلام را با مبلغ کل یکسان نگیرد، هیچ‌کدام «تصحیح» نمی‌شود؛
    // هر دو نمایش داده می‌شوند تا اختلاف در همان نگاه پیدا باشد.
    final totalsDisagree = itemsTotal != total;

    return SizedBox(
      height: MediaQuery.of(context).size.height * 0.78,
      child: Column(
        children: [
          Row(
            children: [
              const Icon(Icons.receipt_long_outlined,
                  color: MpColors.primaryLight, size: 22),
              const SizedBox(width: 8),
              Expanded(
                child: Text('رسید سفارش',
                    style: const TextStyle(
                        fontWeight: FontWeight.w800, fontSize: 16)),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('بستن'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Expanded(
            child: SelectionArea(
              child: ListView(
                padding: const EdgeInsets.only(bottom: 12),
                children: [
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                receiptNo.isEmpty
                                    ? 'شناسهٔ رسید از سرور نیامد'
                                    : receiptNo,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w800, fontSize: 14),
                              ),
                            ),
                            _StatusChip(status: status),
                          ],
                        ),
                        const SizedBox(height: 6),
                        if (memberName.isNotEmpty) ...[
                          Text('تحویل به: $memberName',
                              style: const TextStyle(fontSize: 12.5)),
                          const SizedBox(height: 2),
                        ],
                        Text(
                          [
                            if (createdAt != null)
                              'تاریخ سفارش: ${formatJalaliDate(createdAt)}',
                            if (issuedAt != null)
                              'صدور رسید: ${formatJalaliDate(issuedAt)}',
                          ].join(' · '),
                          style: const TextStyle(
                              fontSize: 12, color: MpColors.textSecondary),
                        ),
                        if (note.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text('یادداشت: $note',
                              style: const TextStyle(fontSize: 12.5)),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  if (lines.isEmpty)
                    const GlassCard(
                      child: Text('هیچ قلمی در این سفارش ثبت نشده است',
                          textAlign: TextAlign.center),
                    )
                  else
                    for (final line in lines) _ReceiptLine(line: line),
                  const SizedBox(height: 10),
                  GlassCard(
                    child: Column(
                      children: [
                        _AmountRow(
                            label: 'جمع اقلام',
                            amountRial: itemsTotal,
                            emphasized: false),
                        const Divider(height: 18),
                        _AmountRow(
                            label: 'قابل پرداخت', amountRial: total, emphasized: true),
                        if (totalsDisagree)
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              'مبلغ کل همان است که سرور ثبت کرده؛ با جمع اقلام یکسان نیست.',
                              style: const TextStyle(
                                  fontSize: 11.5, color: MpColors.accentSoft),
                            ),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 10),
                  GlassCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('پرداخت',
                            style: TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 4),
                        Text(
                          payment == null
                              ? 'رکورد پرداختی برای این سفارش ثبت نشده است'
                              : [
                                  'روش: ${payment['method'] ?? '—'}',
                                  'وضعیت: ${orderStatusLabel(payment['status'] as String?)}',
                                  if ((payment['reference_id'] as String?)
                                          ?.isNotEmpty ??
                                      false)
                                    'مرجع: ${payment['reference_id']}',
                                  if (_date(payment['paid_at']) != null)
                                    'زمان پرداخت: ${formatJalaliDate(_date(payment['paid_at'])!)}',
                                ].join(' · '),
                          style: const TextStyle(
                              fontSize: 12.5, color: MpColors.textSecondary),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'این رسید فقط خواندنی است؛ مبلغ و اقلام را سرور تعیین می‌کند.',
                    style: TextStyle(
                        fontSize: 11, color: MpColors.textSecondary.withOpacity(0.85)),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'paid' || 'delivered' => MpColors.primary,
      'cancelled' || 'failed' => MpColors.danger,
      _ => MpColors.accent,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        orderStatusLabel(status),
        style: TextStyle(fontSize: 11.5, color: color, fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _ReceiptLine extends StatelessWidget {
  const _ReceiptLine({required this.line});

  final Map<String, dynamic> line;

  @override
  Widget build(BuildContext context) {
    final title = (line['title'] as String?) ?? 'قلم';
    final variant = (line['variant'] as String?)?.trim() ?? '';
    final qty = (line['qty'] as num?)?.toInt() ?? 0;
    final unitPrice = (line['unit_price_rial'] as num?) ?? 0;
    final lineTotal = (line['line_total_rial'] as num?) ?? 0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    variant.isEmpty ? title : '$title — $variant',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${rial(unitPrice)} × ${faDigits(qty)}',
                    style: const TextStyle(
                        fontSize: 11.5, color: MpColors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Semantics(
              label: 'مبلغ این قلم',
              child: Text(rial(lineTotal),
                  style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w800,
                      color: MpColors.accentSoft)),
            ),
          ],
        ),
      ),
    );
  }
}

class _AmountRow extends StatelessWidget {
  const _AmountRow({
    required this.label,
    required this.amountRial,
    required this.emphasized,
  });

  final String label;
  final num amountRial;
  final bool emphasized;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 12.5)),
        Text(
          rial(amountRial),
          style: TextStyle(
            fontSize: 13.5,
            fontWeight: FontWeight.w800,
            color: emphasized ? MpColors.accentSoft : MpColors.textPrimary,
          ),
        ),
      ],
    );
  }
}

DateTime? _date(Object? raw) {
  if (raw is! String || raw.isEmpty) return null;
  return DateTime.tryParse(raw)?.toLocal();
}
