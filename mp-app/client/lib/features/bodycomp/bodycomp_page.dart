/// نتایج/سوابق/پیشرفت پیکرسنجی — فقط خواندنی برای کلاینت (M18/M19).
library;

import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class BodyCompPage extends StatelessWidget {
  const BodyCompPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('پیکرسنجی'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: const [
          _SummaryCard(),
          SizedBox(height: 16),
          _TrendCard(),
          SizedBox(height: 16),
          _HistoryCard(),
          SizedBox(height: 12),
          _StaffOnlyNote(),
        ],
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Row(
        children: [
          // عدد بزرگ درصد چربی
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('درصد چربی بدن', style: TextStyle(fontSize: 13, color: MpColors.textSecondary)),
              const SizedBox(height: 6),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: const [
                  Text(
                    '۱۲٫۴',
                    style: TextStyle(fontSize: 40, fontWeight: FontWeight.w900, color: MpColors.primary, height: 1),
                  ),
                  SizedBox(width: 4),
                  Padding(
                    padding: EdgeInsets.only(bottom: 6),
                    child: Text('٪', style: TextStyle(fontSize: 16, color: MpColors.primaryLight)),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                children: const [
                  Icon(Icons.trending_down, color: MpColors.primaryLight, size: 18),
                  SizedBox(width: 4),
                  Text('۱٫۲٪ کاهش از ماه قبل', style: TextStyle(fontSize: 12, color: MpColors.primaryLight)),
                ],
              ),
            ],
          ),
          const Spacer(),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: const [
              _MiniStat('وزن', '۷۸٫۵ کیلو'),
              SizedBox(height: 10),
              _MiniStat('عضله', '۳۴٫۱ کیلو'),
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: MpColors.textSecondary)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: MpColors.textPrimary)),
      ],
    );
  }
}

class _TrendCard extends StatelessWidget {
  const _TrendCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('روند ۶ ماه اخیر', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: CustomPaint(
              size: const Size(double.infinity, 120),
              painter: _TrendPainter(),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('اردیبهشت', style: TextStyle(fontSize: 10, color: MpColors.textSecondary)),
              Text('تیر', style: TextStyle(fontSize: 10, color: MpColors.textSecondary)),
              Text('شهریور', style: TextStyle(fontSize: 10, color: MpColors.textSecondary)),
              Text('آبان', style: TextStyle(fontSize: 10, color: MpColors.textSecondary)),
            ],
          ),
        ],
      ),
    );
  }
}

class _TrendPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final line = Paint()
      ..color = MpColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    final fill = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [MpColors.primary.withOpacity(0.30), MpColors.primary.withOpacity(0.0)],
      ).createShader(Offset.zero & size);

    // داده‌های نمونه — در اتصال API از /assessments/member پر می‌شود
    final points = <Offset>[
      Offset(0, size.height * 0.35),
      Offset(size.width * 0.2, size.height * 0.45),
      Offset(size.width * 0.4, size.height * 0.40),
      Offset(size.width * 0.6, size.height * 0.60),
      Offset(size.width * 0.8, size.height * 0.72),
      Offset(size.width, size.height * 0.80),
    ];
    final path = Path()..moveTo(points.first.dx, points.first.dy);
    for (final p in points.skip(1)) {
      path.lineTo(p.dx, p.dy);
    }
    canvas.drawPath(path, line);
    final fillPath = Path.from(path)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(fillPath, fill);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard();

  @override
  Widget build(BuildContext context) {
    final rows = <({String date, String fat, String weight})>[
      (date: '۱۴ آبان ۱۴۰۵', fat: '۱۲٫۴٪', weight: '۷۸٫۵'),
      (date: '۱۴ مهر ۱۴۰۵', fat: '۱۳٫۶٪', weight: '۸۰٫۱'),
      (date: '۱۵ شهریور ۱۴۰۵', fat: '۱۴٫۲٪', weight: '۸۱٫۰'),
      (date: '۱۵ مرداد ۱۴۰۵', fat: '۱۵٫۰٪', weight: '۸۲٫۳'),
    ];
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('سوابق اندازه‌گیری', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: MpColors.textPrimary)),
          const SizedBox(height: 12),
          for (final r in rows) ...[
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Row(
                children: [
                  const Icon(Icons.event_note, size: 18, color: MpColors.textSecondary),
                  const SizedBox(width: 10),
                  Expanded(child: Text(r.date, style: const TextStyle(fontSize: 13, color: MpColors.textPrimary))),
                  Text(r.fat, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: MpColors.primaryLight)),
                  const SizedBox(width: 16),
                  Text('${r.weight} کیلو', style: const TextStyle(fontSize: 13, color: MpColors.textSecondary)),
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
