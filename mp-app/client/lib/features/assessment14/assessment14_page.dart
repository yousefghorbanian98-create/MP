/// «توانایی‌های من» — ثبت آزمون + ماتریس درصد ۱۴ محور (M37).
///
/// چهار وضعیت تصمیم (اسپک §8): تمرین مستقیم | پوشش در تکلیف دیگر | نگهداری | ارجاع.
/// نمرهٔ نامعلوم «—» نمایش داده می‌شود — هرگز صفر (داده ناشناخته است نه صفر).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'assessment14_providers.dart';

const Map<String, Color> decisionColors = {
  'direct': Color(0xFFE8A13A),
  'covered': Color(0xFF4A90D9),
  'maintain': Color(0xFF3DBE7A),
  'refer': Color(0xFFD9534F),
  'unknown': Color(0xFF8A8F98),
};

const Map<String, String> decisionLabelsFa = {
  'direct': 'تمرین مستقیم',
  'covered': 'پوشش در تکلیف دیگر',
  'maintain': 'نگهداری',
  'refer': 'ارجاع',
  'unknown': 'نامعلوم',
};

class Assessment14Page extends ConsumerStatefulWidget {
  const Assessment14Page({super.key});

  @override
  ConsumerState<Assessment14Page> createState() => _Assessment14PageState();
}

class _Assessment14PageState extends ConsumerState<Assessment14Page> {
  String? _selectedTest;
  final _valueController = TextEditingController();
  bool _submitting = false;
  String? _message;

  @override
  void dispose() {
    _valueController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final raw = double.tryParse(_valueController.text.trim());
    if (_selectedTest == null || raw == null) {
      setState(() => _message = 'آزمون و مقدار عددی را وارد کنید');
      return;
    }
    setState(() {
      _submitting = true;
      _message = null;
    });
    final ok = await ref.read(submitAxisTestsProvider)([
      {'test_key': _selectedTest, 'raw_value': raw},
    ]);
    setState(() {
      _submitting = false;
      _message = ok ? 'ثبت شد ✓' : 'ثبت نشد — دوباره تلاش کنید';
      if (ok) _valueController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final matrixAsync = ref.watch(axisMatrixProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.insights, color: MpColors.primary, size: 28),
                    SizedBox(width: 10),
                    Text('توانایی‌های من',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'نتیجهٔ آزمون‌های میدانی شما با نُرم‌های مرجع سنجیده می‌شود',
                  style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _selectedTest,
                  hint: const Text('انتخاب آزمون'),
                  items: testLabelsFa.entries
                      .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                      .toList(),
                  onChanged: (v) => setState(() => _selectedTest = v),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _valueController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'مقدار اندازه‌گیری‌شده',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: _submitting ? null : _submit,
                  child: Text(_submitting ? 'در حال ثبت…' : 'ثبت آزمون'),
                ),
                if (_message != null) ...[
                  const SizedBox(height: 8),
                  Text(_message!, style: const TextStyle(fontSize: 12)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('ماتریس ۱۴ توانایی',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                matrixAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (_, __) => const Text('خطا در دریافت ماتریس'),
                  data: (matrix) {
                    if (matrix == null || (matrix['axes'] as List?)?.isEmpty != false) {
                      return const Text(
                        'هنوز ارزیابی ثبت نشده است — اولین آزمون خود را ثبت کنید',
                        style: TextStyle(color: MpColors.textSecondary),
                      );
                    }
                    final axes = (matrix['axes'] as List).cast<Map<String, dynamic>>();
                    return Column(
                      children: axes.map(_AxisRow.new).toList(),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AxisRow extends StatelessWidget {
  const _AxisRow(this.axis);

  final Map<String, dynamic> axis;

  @override
  Widget build(BuildContext context) {
    final score = (axis['score'] as num?)?.toDouble();
    final state = (axis['decision_state'] as String?) ?? 'unknown';
    final color = decisionColors[state] ?? decisionColors['unknown']!;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            flex: 4,
            child: Text('${axis['axis']} ${axis['name_fa']}',
                style: const TextStyle(fontSize: 12)),
          ),
          Expanded(
            flex: 3,
            child: score == null
                ? const Text('—', textAlign: TextAlign.center)
                : Stack(
                    alignment: Alignment.center,
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: (score.clamp(0, 100)) / 100,
                          minHeight: 14,
                          backgroundColor: Colors.white12,
                          valueColor: AlwaysStoppedAnimation(color),
                        ),
                      ),
                      Text('${score.round()}',
                          style: const TextStyle(fontSize: 10)),
                    ],
                  ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: color.withOpacity(0.18),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              decisionLabelsFa[state] ?? state,
              style: TextStyle(fontSize: 10, color: color),
            ),
          ),
        ],
      ),
    );
  }
}
