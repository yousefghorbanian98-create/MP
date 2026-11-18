/// تخمین TDEE و پیشنهاد کالری از API تطبیقی MP؛ بدون حدس محلی/توصیهٔ بالینی.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/app_state.dart';
import '../../core/membership.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

/// پذیرش وزن با ارقام فارسی/عربی؛ مقدار خارج از قرارداد API رد می‌شود.
double? parseBodyWeightKg(String raw) {
  var normalized =
      raw.trim().replaceAll(',', '').replaceAll('٬', '').replaceAll('٫', '.');
  normalized = normalized.replaceAllMapped(RegExp(r'[۰-۹٠-٩]'), (match) {
    final code = match.group(0)!.codeUnitAt(0);
    final digit = code >= 0x06F0 && code <= 0x06F9
        ? code - 0x06F0
        : code >= 0x0660 && code <= 0x0669
            ? code - 0x0660
            : null;
    return digit?.toString() ?? match.group(0)!;
  });
  final value = double.tryParse(normalized);
  if (value == null || !value.isFinite || value < 20 || value > 400)
    return null;
  return value;
}

class AdaptiveNutritionCard extends ConsumerStatefulWidget {
  const AdaptiveNutritionCard({super.key});

  @override
  ConsumerState<AdaptiveNutritionCard> createState() =>
      _AdaptiveNutritionCardState();
}

class _AdaptiveNutritionCardState extends ConsumerState<AdaptiveNutritionCard> {
  final _weightController = TextEditingController();
  bool _saving = false;
  String? _message;
  String? _error;

  @override
  void dispose() {
    _weightController.dispose();
    super.dispose();
  }

  Future<void> _saveWeight() async {
    final memberId = ref.read(authProvider).memberId;
    final weight = parseBodyWeightKg(_weightController.text);
    if (memberId == null) {
      setState(() => _error = 'شناسهٔ عضو در نشست موجود نیست');
      return;
    }
    if (weight == null) {
      setState(() => _error = 'وزن معتبر بین ۲۰ و ۴۰۰ کیلوگرم وارد کنید');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
      _message = null;
    });
    try {
      final raw = await ref.read(apiClientProvider).post(
        '/nutrition/weight-logs',
        {
          'member_id': memberId,
          'entries': [
            {'weight_kg': weight, 'logged_for_date': _todayKey(DateTime.now())},
          ],
        },
      );
      if (raw is! Map) throw const FormatException('پاسخ ثبت وزن نامعتبر است');
      final response = Map<String, dynamic>.from(raw);
      final logged = response['logged'];
      final updated = response['updated'];
      if (logged is! num || updated is! num || response['reason'] is! String) {
        throw const FormatException('نتیجهٔ ثبت وزن قابل‌تأیید نیست');
      }
      final rejected = response['rejected'];
      if (rejected is List && rejected.isNotEmpty) {
        final reasons = rejected
            .whereType<Map>()
            .map((item) => item['reason'])
            .whereType<String>()
            .join(' · ');
        if (!mounted) return;
        setState(
          () => _error = reasons.isEmpty ? 'سرور وزن را نپذیرفت' : reasons,
        );
        return;
      }
      if (logged + updated <= 0) {
        if (!mounted) return;
        setState(() => _error = response['reason'] as String);
        return;
      }
      if (!mounted) return;
      ref.invalidate(adaptiveNutritionProvider);
      setState(() {
        _message = response['reason'] as String;
        _weightController.clear();
      });
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (error) {
      if (mounted) setState(() => _error = 'ثبت وزن تأیید نشد: $error');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final report = ref.watch(adaptiveNutritionProvider);
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.insights_outlined, color: MpColors.primary),
              const SizedBox(width: 8),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'تغذیهٔ سازگار',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'TDEE و تغییر هدف از روند وزن و ثبت غذا',
                      style: TextStyle(
                        fontSize: 11,
                        color: MpColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'تازه‌سازی تخمین تغذیه',
                onPressed: () => ref.invalidate(adaptiveNutritionProvider),
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 8),
          report.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Row(
                children: [
                  SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 10),
                  Text('در حال محاسبه از داده‌های واقعی…'),
                ],
              ),
            ),
            error: (error, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'گزارش تغذیه دریافت نشد: $error',
                  style: const TextStyle(color: MpColors.danger, fontSize: 12),
                ),
                TextButton(
                  onPressed: () => ref.invalidate(adaptiveNutritionProvider),
                  child: const Text('تلاش دوباره'),
                ),
              ],
            ),
            data: _reportContent,
          ),
          const Divider(height: 24),
          Text(
            'ثبت وزن امروز · ${formatJalaliDate(DateTime.now())}',
            style: const TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            'برای تخمین روند، وزن و روزهای ثبت‌شدهٔ غذا لازم است. ثبت دوبارهٔ امروز، مقدار همان روز را به‌روزرسانی می‌کند.',
            style: TextStyle(
              color: MpColors.textSecondary,
              fontSize: 11,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          if (_message != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                _message!,
                style: const TextStyle(color: MpColors.primaryLight),
              ),
            ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                _error!,
                style: const TextStyle(color: MpColors.danger),
              ),
            ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('adaptive-weight-field'),
                  controller: _weightController,
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  textDirection: TextDirection.ltr,
                  decoration: const InputDecoration(
                    labelText: 'وزن (کیلوگرم)',
                    hintText: 'مثلاً ۷۴٫۵',
                  ),
                ),
              ),
              const SizedBox(width: 10),
              FilledButton(
                key: const Key('adaptive-weight-save'),
                onPressed: _saving ? null : _saveWeight,
                child: Text(_saving ? 'در حال ثبت…' : 'ثبت وزن'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _reportContent(Map<String, dynamic> report) {
    final estimate = Map<String, dynamic>.from(report['estimate'] as Map);
    final suggestion = Map<String, dynamic>.from(report['suggestion'] as Map);
    final trend = Map<String, dynamic>.from(estimate['trend'] as Map);
    final counts = Map<String, dynamic>.from(report['data_counts'] as Map);
    final tdee = estimate['tdee_kcal'] as num?;
    final target = report['current_target_kcal'] as num?;
    final intake = estimate['mean_intake_kcal'] as num?;
    final slope = trend['slope_kg_per_week'] as num?;
    final action = suggestion['action'] as String;

    final actionLabel = switch (action) {
      'increase' => 'افزایش هدف',
      'decrease' => 'کاهش هدف',
      'keep' => 'حفظ هدف فعلی',
      _ => 'تغییری پیشنهاد نشده',
    };
    final confidenceLabel = switch (estimate['confidence']) {
      'high' => 'اطمینان بالا',
      'medium' => 'اطمینان متوسط',
      'low' => 'اطمینان کم',
      _ => 'دادهٔ ناکافی',
    };
    final notes = trend['notes'] is List
        ? (trend['notes'] as List).whereType<String>().toList()
        : <String>[];
    final assumptions = estimate['assumptions'] is List
        ? (estimate['assumptions'] as List).whereType<String>().toList()
        : <String>[];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _Metric(
              label: 'TDEE برآوردی',
              value: tdee == null ? 'نامعلوم' : '${_faNumber(tdee)} kcal',
            ),
            _Metric(
              label: 'هدف فعلی',
              value: target == null
                  ? 'بدون برنامهٔ تأییدشده'
                  : '${_faNumber(target)} kcal',
            ),
            _Metric(
              label: 'میانگین مصرف ثبت‌شده',
              value: intake == null ? 'نامعلوم' : '${_faNumber(intake)} kcal',
            ),
            _Metric(
              label: 'روند وزن',
              value: slope == null ? 'نامعلوم' : '${_faNumber(slope)} kg/هفته',
            ),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            _Tag(confidenceLabel),
            _Tag('${_faNumber(counts['weight_entries'] as num)} ثبت وزن'),
            _Tag('${_faNumber(counts['intake_days'] as num)} روز ثبت غذا'),
            if (report['latest_weight_kg'] is num)
              _Tag(
                'آخرین وزن ${_faNumber(report['latest_weight_kg'] as num)} کیلوگرم',
              ),
          ],
        ),
        const SizedBox(height: 8),
        Text(
          estimate['reason'] as String,
          style: TextStyle(
            color: MpColors.textSecondary,
            fontSize: 11,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(11),
          decoration: BoxDecoration(
            color: MpColors.surface.withOpacity(0.7),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                action == 'none'
                    ? actionLabel
                    : 'پیشنهاد هفتهٔ بعد: $actionLabel · ${_signed(suggestion['delta_kcal'] as num)} kcal'
                        '${suggestion['suggested_target_kcal'] is num ? ' → ${_faNumber(suggestion['suggested_target_kcal'] as num)} kcal' : ''}',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                suggestion['reason'] as String,
                style: TextStyle(
                  color: MpColors.textSecondary,
                  fontSize: 11,
                  height: 1.5,
                ),
              ),
              if (suggestion['capped'] == true)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    'محدودیت تغییر هفتگی API اعمال شده است.',
                    style: TextStyle(color: MpColors.accent, fontSize: 10),
                  ),
                ),
            ],
          ),
        ),
        if (notes.isNotEmpty) ...[
          const SizedBox(height: 7),
          for (final note in notes)
            Padding(
              padding: const EdgeInsets.only(bottom: 3),
              child: Text(
                '• $note',
                style: const TextStyle(color: MpColors.accent, fontSize: 10),
              ),
            ),
        ],
        if (assumptions.isNotEmpty)
          Material(
            type: MaterialType.transparency,
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: const Text(
                'فرض‌های برآورد',
                style: TextStyle(fontSize: 11),
              ),
              children: [
                for (final assumption in assumptions)
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        '• $assumption',
                        style: TextStyle(
                          color: MpColors.textSecondary,
                          fontSize: 10,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        const SizedBox(height: 8),
        const Text(
          'این عدد یک تخمین بر پایهٔ ثبت وزن و غذاست؛ توصیهٔ درمانی یا رژیم پزشکی نیست. برای نیازهای پزشکی با متخصص مشورت کنید.',
          style: TextStyle(
            color: MpColors.textSecondary,
            fontSize: 10,
            height: 1.5,
          ),
        ),
      ],
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Container(
        constraints: const BoxConstraints(minWidth: 135),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: MpColors.surface.withOpacity(0.7),
          borderRadius: BorderRadius.circular(11),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(color: MpColors.textSecondary, fontSize: 10),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
            ),
          ],
        ),
      );
}

class _Tag extends StatelessWidget {
  const _Tag(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: MpColors.primary.withOpacity(0.10),
          borderRadius: BorderRadius.circular(99),
        ),
        child: Text(label, style: const TextStyle(fontSize: 10)),
      );
}

String _todayKey(DateTime date) =>
    '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';

String _faNumber(num value) {
  final number = value.toDouble();
  final text = number == number.roundToDouble()
      ? number.toStringAsFixed(0)
      : number.toStringAsFixed(1);
  return text.replaceAllMapped(
    RegExp(r'\d'),
    (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
  );
}

String _signed(num value) {
  final text =
      value > 0 ? '+${value.toStringAsFixed(0)}' : value.toStringAsFixed(0);
  return text.replaceAllMapped(
    RegExp(r'\d'),
    (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
  );
}
