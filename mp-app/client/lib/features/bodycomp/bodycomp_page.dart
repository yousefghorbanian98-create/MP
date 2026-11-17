/// پیکرسنجی — از دادهٔ واقعی روند JP7، نه اعداد ساخته‌شده.
///
/// M62/D4: نسخهٔ قبلی این صفحه هیچ provider/API نداشت و «۱۲٫۴٪ چربی»،
/// «۷۸٫۵ کیلو»، نمودار ۶ ماهه و چهار ردیف سوابق را **هاردکد** نشان می‌داد.
/// یعنی عضو اعدادی می‌دید که مال خودش نبود و هیچ‌جا «نمونه» برچسب نداشتند —
/// نقض قاعدهٔ «هیچ عددی در UI بدون منبع داده».
///
/// اکنون تنها منبع، `GET /assessments/jp7/member/{id}/trend` است، که خودش
/// سه حالت صادقانه دارد و هر سه را همین‌جا نمایش می‌دهیم:
///   • داده کم (< ۲ اندازه‌گیری) → «یک نقطه، روند نیست»
///   • روند واقعی → مجموع چین + تفسیر + سطح اطمینان
///   • `body_fat_pct` قفل است (D-012) → عددی برایش ساخته نمی‌شود
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

/// روند JP7 عضو — تنها منبع این صفحه.
final jp7TrendProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) {
    return {'data_state': 'no_member', 'measurements': <dynamic>[]};
  }
  final r = await api.get('/assessments/jp7/member/$memberId/trend');
  return Map<String, dynamic>.from(r as Map);
});

/// برچسب فارسیِ سطح اطمینان — از سرور می‌آید، ترجمه فقط برای نمایش است.
const _confidenceLabels = {
  'insufficient': 'داده کافی نیست',
  'medium': 'اطمینان متوسط',
  'high': 'اطمینان بالا',
};

class BodyCompPage extends ConsumerWidget {
  const BodyCompPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trend = ref.watch(jp7TrendProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('پیکرسنجی'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: trend.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('دریافت روند پیکرسنجی ناموفق بود: $e',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: MpColors.danger)),
                const SizedBox(height: 10),
                OutlinedButton(
                  onPressed: () => ref.invalidate(jp7TrendProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
          ),
        ),
        data: (data) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            _HeadlineCard(data: data).animate().fadeIn(duration: 380.ms).slideY(begin: 0.06),
            const SizedBox(height: 12),
            _Jp7TrendChartCard(data: data),
            const SizedBox(height: 12),
            _MeasurementsCard(data: data)
                .animate()
                .fadeIn(delay: 90.ms, duration: 380.ms),
            const SizedBox(height: 12),
            _LockedNote(data: data),
            const SizedBox(height: 12),
            const _StaffOnlyNote(),
          ],
        ),
      ),
    );
  }
}

/// کارت اصلی — تفسیر سرور، یا صادقانه «داده کافی نیست».
class _HeadlineCard extends StatelessWidget {
  const _HeadlineCard({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final interp = (data['interpretation'] as Map?) ?? const {};
    final headline = interp['headline'] as String? ?? 'وضعیت نامعلوم';
    final detail = interp['detail'] as String? ?? '';
    final confidence = interp['confidence'] as String? ?? 'insufficient';
    final trend = data['trend'] as Map?;

    // «نامعلوم» با رنگ هشدار، نه با عدد سبز جعلی.
    final isInsufficient = confidence == 'insufficient';
    final accent = isInsufficient ? MpColors.textSecondary : MpColors.primary;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isInsufficient ? Icons.info_outline : Icons.show_chart,
                color: accent,
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  headline,
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: accent),
                ),
              ),
            ],
          ),
          if (detail.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(detail,
                style: const TextStyle(fontSize: 12, height: 1.8, color: MpColors.textSecondary)),
          ],
          if (trend != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                _Stat('تغییر مجموع چین', '${trend['delta_mm'] ?? '—'} میلی‌متر'),
                const SizedBox(width: 12),
                _Stat('بازه', '${trend['days'] ?? '—'} روز'),
              ],
            ),
          ],
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: accent.withOpacity(0.10),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              _confidenceLabels[confidence] ?? confidence,
              style: TextStyle(fontSize: 11, color: accent, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
          const SizedBox(height: 2),
          Text(value,
              style: const TextStyle(
                  fontSize: 14, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
        ],
      ),
    );
  }
}

/// M79: رسم روند عضو از همان measurements API؛ زیر دو نقطه هیچ خطی نمی‌سازیم.
class _Jp7TrendChartCard extends StatelessWidget {
  const _Jp7TrendChartCard({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final points = _jp7ChartPoints(data);
    if (points.length < 2) return const SizedBox.shrink();

    final values = points.map((point) => point.sumMm).toList(growable: false);
    final first = points.first;
    final last = points.last;
    final firstValue = _faDigits(first.sumMm.toString());
    final lastValue = _faDigits(last.sumMm.toString());
    final semanticLabel =
        'نمودار مجموع چین‌ها در ${_faDigits(points.length.toString())} اندازه‌گیری، '
        'از ${_dateFa(first.measuredAt)} تا ${_dateFa(last.measuredAt)}؛ '
        'از $firstValue تا $lastValue میلی‌متر';

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('روند مجموع چین‌های پوستی',
              style: TextStyle(
                  fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 4),
          const Text('بر اساس اندازه‌گیری‌های ثبت‌شده در سرور',
              style: TextStyle(fontSize: 11, color: MpColors.textSecondary)),
          const SizedBox(height: 12),
          Semantics(
            container: true,
            image: true,
            label: semanticLabel,
            child: SizedBox(
              height: 150,
              width: double.infinity,
              child: CustomPaint(
                key: const ValueKey('jp7-trend-chart'),
                painter: _Jp7TrendChartPainter(
                  values: values,
                  color: MpColors.primaryLight,
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text('از ${_dateFa(first.measuredAt)} تا ${_dateFa(last.measuredAt)}',
              style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
          const SizedBox(height: 2),
          Text('ابتدا: $firstValue میلی‌متر  ·  آخر: $lastValue میلی‌متر',
              style: const TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
        ],
      ),
    );
  }
}

class _Jp7ChartPoint {
  const _Jp7ChartPoint({required this.sumMm, required this.measuredAt});

  final double sumMm;
  final String? measuredAt;
}

List<_Jp7ChartPoint> _jp7ChartPoints(Map<String, dynamic> data) {
  final rows = data['measurements'];
  if (rows is! List) return const [];
  return [
    for (final row in rows)
      if (row is Map && row['sum_mm'] is num)
        _Jp7ChartPoint(
          sumMm: (row['sum_mm'] as num).toDouble(),
          measuredAt: row['measured_at'] is String ? row['measured_at'] as String : null,
        ),
  ];
}

class _Jp7TrendChartPainter extends CustomPainter {
  const _Jp7TrendChartPainter({required this.values, required this.color});

  final List<double> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2 || size.width <= 24 || size.height <= 24) return;

    const inset = 12.0;
    final plot = Rect.fromLTRB(
      inset,
      inset,
      size.width - inset,
      size.height - inset,
    );
    final minValue = values.reduce((a, b) => a < b ? a : b);
    final maxValue = values.reduce((a, b) => a > b ? a : b);
    final span = maxValue - minValue;
    final points = <Offset>[
      for (var i = 0; i < values.length; i++)
        Offset(
          plot.left + (i / (values.length - 1)) * plot.width,
          plot.bottom -
              (span == 0 ? 0.5 : (values[i] - minValue) / span) * plot.height,
        ),
    ];

    final gridPaint = Paint()
      ..color = MpColors.primary.withOpacity(0.12)
      ..strokeWidth = 1;
    for (var row = 0; row < 3; row++) {
      final y = plot.top + (row / 2) * plot.height;
      canvas.drawLine(Offset(plot.left, y), Offset(plot.right, y), gridPaint);
    }

    final linePaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final path = Path()..moveTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      path.lineTo(point.dx, point.dy);
    }
    canvas.drawPath(path, linePaint);

    final dotPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;
    for (final point in points) {
      canvas.drawCircle(point, 3.5, dotPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _Jp7TrendChartPainter oldDelegate) =>
      oldDelegate.values != values || oldDelegate.color != color;
}

/// سوابق اندازه‌گیری — فقط نقاطی که در سرور هستند.
class _MeasurementsCard extends StatelessWidget {
  const _MeasurementsCard({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final rows = (data['measurements'] as List?) ?? const [];
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('سوابق اندازه‌گیری',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 12),
          if (rows.isEmpty)
            Text('هنوز اندازه‌گیری‌ای ثبت نشده است.',
                style: TextStyle(fontSize: 13, color: MpColors.textSecondary))
          else
            for (final r in rows.cast<Map>()) ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 9),
                child: Row(
                  children: [
                    const Icon(Icons.event_note, size: 18, color: MpColors.textSecondary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _dateFa(r['measured_at'] as String?),
                        style: const TextStyle(fontSize: 13, color: MpColors.textPrimary),
                      ),
                    ),
                    Text(
                      '${r['sum_mm'] ?? '—'} میلی‌متر',
                      style: const TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w700, color: MpColors.primaryLight),
                    ),
                  ],
                ),
              ),
              if (r != rows.last) Divider(color: MpColors.primary.withOpacity(0.10), height: 1),
            ],
        ],
      ),
    );
  }
}

/// تاریخ ISO سرور → سال/ماه/روز میلادی با ارقام فارسی.
/// بدون `intl` انجام می‌شود تا وابستگی تازه اضافه نشود.
String _dateFa(String? iso) {
  if (iso == null) return 'تاریخ نامعلوم';
  final d = DateTime.tryParse(iso);
  if (d == null) return 'تاریخ نامعلوم';
  final g = '${d.year}/${d.month.toString().padLeft(2, '0')}/${d.day.toString().padLeft(2, '0')}';
  return _faDigits(g);
}

String _faDigits(String value) {
  const fa = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return value.split('').map((character) {
    final digit = int.tryParse(character);
    return digit == null ? character : fa[digit];
  }).join();
}

/// یادداشت قفل درصد چربی — صریح، چون عدد ندارد.
class _LockedNote extends StatelessWidget {
  const _LockedNote({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final note = data['body_fat_note'] as String?;
    if (note == null || note.isEmpty) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      decoration: BoxDecoration(
        color: MpColors.primary.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MpColors.primary.withOpacity(0.20)),
      ),
      child: Row(
        children: [
          const Icon(Icons.lock_outline, size: 17, color: MpColors.primaryLight),
          const SizedBox(width: 9),
          Expanded(
            child: Text(note,
                style: const TextStyle(fontSize: 11.5, height: 1.7, color: MpColors.primaryLight)),
          ),
        ],
      ),
    );
  }
}

class _StaffOnlyNote extends StatelessWidget {
  const _StaffOnlyNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: MpColors.accent.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MpColors.accent.withOpacity(0.25)),
      ),
      child: Row(
        children: const [
          Icon(Icons.info_outline, size: 18, color: MpColors.accentSoft),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'ثبت اندازه‌گیری جدید فقط توسط مربی/پذیرش باشگاه انجام می‌شود',
              style: TextStyle(fontSize: 12, color: MpColors.accentSoft, height: 1.6),
            ),
          ),
        ],
      ),
    );
  }
}
