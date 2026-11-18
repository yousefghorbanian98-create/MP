/// فرم بازخورد هر ست (M39-c1) + نمای «چرا این تغییر؟» (M39-c2).
///
/// زنجیرهٔ نمایش‌داده‌شده: داده (ست شما) ← قاعده (autoreg/درد) ← تصمیم + دلیل.
/// عدد پیشنهادی از backend می‌آید — هیچ عددی در کلاینت ساخته نمی‌شود (E04).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/haptics.dart';
import '../../core/theme.dart';
import 'feedback_providers.dart';

class SetFeedbackSheet extends ConsumerStatefulWidget {
  const SetFeedbackSheet({super.key, required this.movementName, this.programId});

  final String movementName;
  final int? programId;

  @override
  ConsumerState<SetFeedbackSheet> createState() => _SetFeedbackSheetState();
}

class _SetFeedbackSheetState extends ConsumerState<SetFeedbackSheet> {
  final _repsController = TextEditingController();
  final _weightController = TextEditingController();
  double _rir = 2;
  double _soreness = 2;
  bool _submitting = false;
  Map<String, dynamic>? _result;
  String? _queueMessage;
  String? _errorMessage;

  @override
  void dispose() {
    _repsController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final reps = int.tryParse(_repsController.text.trim());
    if (reps == null) return;
    // UX-G3/M98 — «ثبت شد» باید بدون نگاه کردن به صفحه هم حس شود. خطای پلتفرم
    // در MpHaptics بلعیده می‌شود، پس این خط هیچ‌وقت ثبت را نمی‌شکند.
    final haptics = ref.read(hapticsProvider);
    final entry = <String, dynamic>{
      'movement_id': widget.movementName,
      // M48-c1 — پیش‌تر همیشه 0 بود، پس autoreg هرگز فعال نمی‌شد و
      // همهٔ حرکات «وزن بدن» تلقی می‌شدند.
      'weight': double.tryParse(_weightController.text.trim()) ?? 0,
      'target_reps': reps,
      'reps_done': reps,
      'rir': _rir,
      'soreness': _soreness.round(),
    };
    setState(() {
      _submitting = true;
      _result = null;
      _queueMessage = null;
      _errorMessage = null;
    });
    try {
      var hasNetwork = true;
      try {
        hasNetwork = await ref.read(offlineFeedbackNetworkAvailableProvider)();
      } catch (_) {
        // Fail closed for offline persistence: if the platform cannot establish
        // that the request is offline, do not risk queuing a possibly committed write.
        hasNetwork = true;
      }
      if (!hasNetwork) {
        try {
          await ref.read(enqueueOfflineFeedbackProvider)(
            programId: widget.programId,
            entries: [entry],
          );
          ref.invalidate(offlineFeedbackQueueProvider);
          // صف آفلاین = موفق نیست، فقط از دست نرفته → پالس هشدار، نه تأیید.
          haptics.warning();
          if (mounted) {
            setState(() => _queueMessage =
                'بازخورد ساختاریافته در دستگاه ذخیره شد و هنوز به سرور نرسیده است. درد عضلانی/یادداشت و پیشنهاد خودکار آفلاین ذخیره نمی‌شوند.');
          }
        } catch (_) {
          haptics.warning();
          if (mounted) {
            setState(() => _errorMessage =
                'شبکه در دسترس نیست و صف آفلاین Android هم آماده نیست؛ بازخورد ذخیره نشد.');
          }
        }
        return;
      }

      final result = await ref.read(submitSetFeedbackProvider)([entry]);
      if (result == null) throw const FormatException('Invalid feedback response');
      if (!mounted) return;
      haptics.success();
      ref.invalidate(readinessProvider);
      setState(() => _result = result);
    } catch (_) {
      haptics.warning();
      if (mounted) {
        setState(() => _errorMessage =
            'ارسال بازخورد ناموفق بود. نتیجهٔ درخواست ممکن است نامشخص باشد؛ برای جلوگیری از ثبت تکراری آن را خودکار در صف نگذاشتیم. اتصال را بررسی کنید و سپس وضعیت سرور را بسنجید.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // M48-c1 → M59 — سه قطر سرریز و درسِ هرکدام:
    //   ۱) Column سرریز می‌کرد ← SingleChildScrollView.
    //   ۲) با کارت «چرا این تغییر؟» چند پیکسل کم آمد ← کارت با Wrap فشرده شد.
    //   ۳) تلاش کردم `Expanded` بدهم؛ خودِ فریم‌ورک گفت «Expanded inside
    //      Padding» خطاست و راست می‌گفت — Expanded فقط داخل Flex معنا دارد.
    // رفع درست: `ConstrainedBox(maxHeight)` + اسکرول. محتوای بلند اسکرول
    // می‌شود، محتوای کوتاه ارتفاع طبیعی خودش را می‌گیرد. نه فیلدی حذف شد،
    // نه فونت کوچک شد.
    final maxHeight = MediaQuery.of(context).size.height * 0.86;
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: ConstrainedBox(
        constraints: BoxConstraints(maxHeight: maxHeight),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('بازخورد ست — ${widget.movementName}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 4),
              const Text(
                  'RIR یعنی چند تکرار در تانک داشتید؛ درد عضلانی فردا را ۰ تا ۱۰ بسنجید',
                  style: TextStyle(fontSize: 11, color: MpColors.textSecondary)),
              const SizedBox(height: 14),
              TextField(
                controller: _weightController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'وزنه (کیلوگرم) — برای وزن بدن خالی بگذارید',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _repsController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'تکرار انجام‌شده',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 14),
              Text('تکرار ذخیره (RIR): ${_rir.round()}'),
              Slider(
                value: _rir,
                min: 0,
                max: 5,
                divisions: 5,
                // tick روی هر گام — همان بازخوردی که اسلایدر بصری می‌دهد، لمسی.
                onChanged: (v) {
                  setState(() => _rir = v);
                  ref.read(hapticsProvider).select();
                },
              ),
              Text('درد عضلانی: ${_soreness.round()}'),
              Slider(
                value: _soreness,
                min: 0,
                max: 10,
                divisions: 10,
                onChanged: (v) {
                  setState(() => _soreness = v);
                  ref.read(hapticsProvider).select();
                },
              ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: Text(_submitting ? 'در حال پردازش…' : 'ثبت بازخورد'),
                ),
              ),
              if (_queueMessage != null) ...[
                const SizedBox(height: 12),
                Text(
                  _queueMessage!,
                  style: const TextStyle(color: MpColors.textSecondary, fontSize: 12),
                ),
              ],
              if (_errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(
                  _errorMessage!,
                  style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                ),
              ],
              if (_result != null) ...[
                const SizedBox(height: 16),
                _WhyCard(result: _result!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// «چرا این تغییر؟» — داده ← قاعده ← تصمیم + دلیل (M39-c2).
class _WhyCard extends StatelessWidget {
  const _WhyCard({required this.result});

  final Map<String, dynamic> result;

  /// آیا پیشنهاد واقعاً روی برنامه اعمال شد یا فقط محاسبه شد؟
  List<Widget> _appliedLine(Map<String, dynamic> result) {
    final applied = result['applied'] as Map<String, dynamic>?;
    if (applied == null) return const [];
    final weeks = applied['weeks_updated'] as int? ?? 0;
    final rows = applied['rows_changed'] as int? ?? 0;
    final unmatched = (applied['unmatched_movements'] as List?)?.cast<String>() ?? [];
    if (weeks == 0) {
      return [
        Text(
          unmatched.isEmpty
              ? 'اعمال نشد — هیچ هفتهٔ آینده‌ای نبود'
              : 'اعمال نشد — حرکت در برنامه پیدا نشد: ${unmatched.join('، ')}',
          style: const TextStyle(fontSize: 11, color: MpColors.textSecondary),
        ),
      ];
    }
    return [
      Text(
        'اعمال شد: $rows ردیف در $weeks هفتهٔ آینده به‌روز شد',
        style: const TextStyle(fontSize: 11, color: MpColors.textSecondary),
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final suggestions = (result['suggestions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    if (suggestions.isEmpty) return const SizedBox.shrink();
    final s = suggestions.first;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: MpColors.primary.withOpacity(0.10),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MpColors.primary.withOpacity(0.30)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.help_outline, size: 18, color: MpColors.primary),
              SizedBox(width: 6),
              Text('چرا این تغییر؟', style: TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 8),
          // M59 — سه خط جدا (وزن/ست/دلیل) در ارتفاع ویجت‌تست سرریز می‌کرد؛
          // Wrap همان اطلاعات است و در عرض کم می‌شکند. هیچ داده‌ای حذف نشد.
          Wrap(
            spacing: 12,
            runSpacing: 2,
            children: [
              Text('وزن بعد: ${s['next_weight']} (${s['weight_action']})',
                  style: const TextStyle(fontSize: 13)),
              Text(
                s['next_sets'] == null
                    // M48-c1 — در حالت deload عدد مطلق نداریم؛ کاهش نسبت به
                    // خودِ برنامه اعمال می‌شود، نه نسبت به تعداد گزارش‌شده.
                    ? 'ست بعد: یک ست کمتر از برنامهٔ فعلی (${s['volume_action']})'
                    : 'ست بعد: ${s['next_sets']} (${s['volume_action']})',
                style: const TextStyle(fontSize: 13),
              ),
            ],
          ),
          const Divider(height: 16),
          ..._appliedLine(result),
          Text(
            'دلیل: ${s['reason']}',
            style: const TextStyle(fontSize: 12, color: MpColors.textSecondary),
          ),
          if (s['volume_action'] == 'deload' && s['weight_action'] == 'increase')
            const Padding(
              padding: EdgeInsets.only(top: 4),
              child: Text(
                // دو سیگنال مستقل: ست راحت بود (بار برود بالا) ولی درد زیاد است
                // (حجم بیاید پایین). این تناقض نیست — تفکیک بار از حجم است.
                'بار و حجم دو سیگنال جدا هستند: بار بالا می‌رود چون ست راحت بود، '
                'حجم پایین می‌آید چون درد زیاد است.',
                style: TextStyle(fontSize: 10, color: MpColors.textSecondary),
              ),
            ),
          Text(
            'قاعده: ${s['rule_version']} — عدد از موتور قواعد، نه هوش مصنوعی',
            style: const TextStyle(fontSize: 10, color: MpColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
