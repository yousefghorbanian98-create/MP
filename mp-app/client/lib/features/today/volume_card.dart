/// حجم هفتگی عضلات و MV/MEV/MAV/MRV از گزارش واقعی عضو (G2/M77).
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class VolumeCard extends ConsumerStatefulWidget {
  const VolumeCard({super.key});

  @override
  ConsumerState<VolumeCard> createState() => _VolumeCardState();
}

class _VolumeCardState extends ConsumerState<VolumeCard> {
  String _level = 'intermediate';

  static const _levels = <({String key, String label})>[
    (key: 'beginner', label: 'مبتدی'),
    (key: 'intermediate', label: 'متوسط'),
    (key: 'advanced', label: 'پیشرفته'),
  ];

  @override
  Widget build(BuildContext context) {
    final volume = ref.watch(volumeProvider(_level));
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.bar_chart, color: MpColors.primary),
              const SizedBox(width: 8),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('حجم هفتگی عضلات', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    SizedBox(height: 3),
                    Text('ست مؤثر در برابر نشانگرهای مربی‌گری',
                        style: TextStyle(fontSize: 11, color: MpColors.textSecondary)),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'تازه‌سازی حجم',
                onPressed: () => ref.invalidate(volumeProvider(_level)),
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 7,
            children: [
              for (final level in _levels)
                ChoiceChip(
                  label: Text(level.label),
                  selected: _level == level.key,
                  onSelected: (selected) {
                    if (selected) setState(() => _level = level.key);
                  },
                ),
            ],
          ),
          const SizedBox(height: 8),
          volume.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 18),
              child: Row(
                children: [
                  SizedBox.square(dimension: 20, child: CircularProgressIndicator(strokeWidth: 2)),
                  SizedBox(width: 10),
                  Text('در حال دریافت حجم هفتگی…'),
                ],
              ),
            ),
            error: (error, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('دریافت حجم هفتگی ناموفق بود: $error',
                    style: const TextStyle(color: MpColors.danger, fontSize: 12)),
                OutlinedButton(
                  onPressed: () => ref.invalidate(volumeProvider(_level)),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
            data: (report) {
              final rows = (report['muscles'] as List)
                  .map((row) => Map<String, dynamic>.from(row as Map))
                  .toList();
              if (rows.isEmpty) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: Text(
                    report['reason'] as String,
                    textAlign: TextAlign.center,
                    style: TextStyle(color: MpColors.textSecondary, height: 1.5),
                  ),
                );
              }
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(report['reason'] as String,
                      style: TextStyle(color: MpColors.textSecondary, fontSize: 11, height: 1.5)),
                  const SizedBox(height: 14),
                  for (final row in rows) ...[
                    _MuscleVolumeRow(row: row),
                    if (row != rows.last) const Divider(height: 22),
                  ],
                  const Divider(height: 22),
                  Text(
                    'منبع جدول نشانگرها: ${(rows.first['landmarks'] as Map)['source']}',
                    style: TextStyle(color: MpColors.textSecondary, fontSize: 10, height: 1.5),
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    'این‌ها حدود راهنمای برنامه‌ریزی تمرین‌اند، نه معادله یا تشخیص پزشکی.',
                    style: TextStyle(color: MpColors.textSecondary, fontSize: 10),
                  ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

class _MuscleVolumeRow extends StatelessWidget {
  const _MuscleVolumeRow({required this.row});

  final Map<String, dynamic> row;

  static const _statusLabels = <String, String>{
    'below_mv': 'زیر MV',
    'between_mv_mev': 'بین MV و MEV',
    'mev': 'روی MEV',
    'mav': 'در بازهٔ MAV',
    'above_mav': 'بالاتر از MAV',
    'mrv_exceeded': 'بالاتر از MRV',
  };

  Color _statusColor(String status) => switch (status) {
        'below_mv' || 'mrv_exceeded' => MpColors.danger,
        'between_mv_mev' || 'above_mav' => MpColors.accent,
        'mev' || 'mav' => MpColors.primary,
        _ => MpColors.textSecondary,
      };

  @override
  Widget build(BuildContext context) {
    final landmarks = Map<String, dynamic>.from(row['landmarks'] as Map);
    final suggestion = Map<String, dynamic>.from(row['suggestion'] as Map);
    final maxSets = math.max(
      math.max((landmarks['mrv'] as num).toDouble(), (row['effective_sets'] as num).toDouble()),
      1.0,
    );
    double fraction(num value) =>
        ((value.toDouble() / maxSets).clamp(0.0, 1.0)).toDouble();
    final status = row['status'] as String;
    final color = _statusColor(status);
    final effective = row['effective_sets'] as num;
    final planned = row['planned_sets'] as num;
    final source = switch (row['source_of_number']) {
      'planned' => 'برنامه',
      'reported_hard_sets' => 'بازخورد عضو',
      _ => 'منبع نامعلوم',
    };
    final delta = (suggestion['delta_sets'] as num).toInt();
    final deltaText = delta > 0 ? '+${_fa('$delta')}' : _fa('$delta');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(row['muscle'] as String,
                  style: const TextStyle(fontWeight: FontWeight.w700)),
            ),
            Text(_statusLabels[status] ?? 'وضعیت نامعلوم',
                style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
          ],
        ),
        const SizedBox(height: 8),
        LayoutBuilder(
          builder: (context, constraints) => Container(
            height: 12,
            decoration: BoxDecoration(
              color: MpColors.surface,
              borderRadius: BorderRadius.circular(99),
            ),
            clipBehavior: Clip.antiAlias,
            child: Stack(
              children: [
                PositionedDirectional(
                  start: (constraints.maxWidth * fraction(landmarks['mav_min'] as num)).toDouble(),
                  width: (constraints.maxWidth *
                          (fraction(landmarks['mav_max'] as num) -
                              fraction(landmarks['mav_min'] as num)))
                      .clamp(0.0, constraints.maxWidth)
                      .toDouble(),

                  top: 0,
                  bottom: 0,
                  child: Container(color: MpColors.primary.withOpacity(0.20)),
                ),
                PositionedDirectional(
                  start: 0,
                  width: (constraints.maxWidth * fraction(effective)).toDouble(),
                  top: 0,
                  bottom: 0,
                  child: Container(color: color),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'ست مؤثر ${_fa(_n(effective))} از ${_fa(_n(planned))} برنامه‌ریزی‌شده · منبع: $source',
          style: TextStyle(color: MpColors.textSecondary, fontSize: 10, height: 1.5),
        ),
        Text(
          'MV ${_fa(_n(landmarks['mv'] as num))} · MEV ${_fa(_n(landmarks['mev'] as num))} · '
          'MAV ${_fa(_n(landmarks['mav_min'] as num))}–${_fa(_n(landmarks['mav_max'] as num))} · '
          'MRV ${_fa(_n(landmarks['mrv'] as num))}',
          textDirection: TextDirection.ltr,
          style: TextStyle(color: MpColors.textSecondary, fontSize: 10),
        ),
        if (row['data_state'] == 'reported')
          Text(
            'ست سخت ${_fa(_n(row['hard_sets'] as num))} · ست راحت ${_fa(_n(row['soft_sets'] as num))}'
            '${(row['unknown_rir_sets'] as num) > 0 ? ' · RIR نامعلوم ${_fa(_n(row['unknown_rir_sets'] as num))}' : ''} · '
            'ست سخت: RIR ≤ ${_fa(_n(landmarks['hard_set_max_rir'] as num))}',
            style: TextStyle(color: MpColors.textSecondary, fontSize: 10, height: 1.5),
          ),
        const SizedBox(height: 4),
        Text(
          'پیشنهاد هفتهٔ بعد: $deltaText ست — ${suggestion['reason']}',
          style: TextStyle(color: MpColors.textSecondary, fontSize: 10, height: 1.5),
        ),
      ],
    );
  }
}

String _n(num value) => value % 1 == 0 ? value.toInt().toString() : value.toStringAsFixed(1);

String _fa(String value) => value.replaceAllMapped(
      RegExp(r'\d'),
      (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
    );
