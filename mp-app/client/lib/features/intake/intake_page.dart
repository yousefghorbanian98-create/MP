/// جریان ساخت برنامه — پرسش‌نامهٔ واقعی ← گیت جمعیتی ← تولید اختصاصی از موتور.
/// هیچ داده‌ای نمونه/دکوری نیست؛ همه چیز از API می‌آید.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import 'program_result.dart';

class IntakePage extends ConsumerStatefulWidget {
  const IntakePage({super.key});

  @override
  ConsumerState<IntakePage> createState() => _IntakePageState();
}

class _IntakePageState extends ConsumerState<IntakePage> {
  // گام ۱: هدف و برنامه
  String goal = 'hypertrophy';
  String level = 'beginner';
  int days = 3;
  int weeks = 8;

  // گام ۲: سابقه و بازهٔ عملکرد
  double experienceMonths = 6;
  String activity = 'moderate';
  final weightCtrl = TextEditingController(text: '75');
  final ageCtrl = TextEditingController(text: '28');
  String? gender; // M41-c1: اجباری — باید صریح انتخاب شود (تفکیک آقایان/بانوان)

  // گام ۳: محدودیت‌ها
  final Set<String> constraints = {};
  static const allConstraints = [
    'کمردرد',
    'زانودرد',
    'شانه‌درد',
    'گردن‌درد',
    'فتق دیسک',
    'بارداری/پس از زایمان',
  ];

  int step = 0;
  bool busy = false;
  String? error;
  Map<String, dynamic>? generated;
  Map<String, dynamic>? nutrition;

  @override
  void dispose() {
    weightCtrl.dispose();
    ageCtrl.dispose();
    super.dispose();
  }

  String get _experienceLabel {
    final m = experienceMonths.round();
    if (m < 6) return 'کمتر از ۶ ماه';
    if (m < 24) return '$m ماه';
    return '${(m / 12).toStringAsFixed(1)} سال';
  }

  Future<void> _generate() async {
    if (gender == null) {
      setState(() => error = 'انتخاب جنسیت الزامی است — تفکیک آقایان/بانوان');
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final auth = ref.read(authProvider);
      if (auth.memberId == null) {
        await ref.read(authProvider.notifier).refreshMe();
      }
      final memberId = ref.read(authProvider).memberId;
      if (memberId == null) {
        throw Exception('ابتدا پروفایل خود را بسازید');
      }

      // گیت جمعیتی — برای مسیرهای متوقف، خطای صریح می‌آید (E05)
      final age = int.tryParse(ageCtrl.text) ?? 0;
      final path = (age >= 60) ? 'senior_healthy' : 'adult';
      await api.post('/population/gate-check', {'path': path});

      // ذخیرهٔ پروفایل با پاسخ‌های همین پرسش‌نامه
      await api.put('/members/me', {'goal': goal, 'gender': gender!});

      // تولید برنامه از موتور قواعد (G8) — با محدودیت‌ها و سابقه
      final prog = await api.post('/ai/program/generate', {
        'member_id': memberId,
        'goal': goal,
        'level': level,
        'days_per_week': days,
        'weeks_count': weeks,
        'constraints': constraints.toList(),
      });

      // تغذیه با بازهٔ عملکرد (وزن/قد/سن/جنس/فعالیت)
      final height = ref.read(authProvider).memberId != null
          ? (await api.get('/members/me'))['height_cm'] as int? ?? 170
          : 170;
      try {
        nutrition = await api.post('/ai/nutrition/generate', {
          'member_id': memberId,
          'goal': goal,
          'activity': activity,
          'weight_kg': double.tryParse(weightCtrl.text) ?? 75,
          'height_cm': height,
          'age': age,
          'gender': gender!,
        });
      } catch (_) {
        nutrition = null; // تغذیه اختیاری است — برنامه اصلی ساخته می‌شود
      }

      setState(() => generated = prog);
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (generated != null) {
      return ProgramResult(
        program: generated!,
        nutrition: nutrition,
        onStartOver: () => setState(() {
          generated = null;
          nutrition = null;
          step = 0;
        }),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('ساخت برنامهٔ اختصاصی')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              _stepIndicator(),
              const SizedBox(height: 16),
              if (step == 0) _stepGoal(),
              if (step == 1) _stepHistory(),
              if (step == 2) _stepConstraints(),
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(error!,
                      style: const TextStyle(color: Colors.redAccent)),
                ),
              const SizedBox(height: 20),
              Row(
                children: [
                  if (step > 0)
                    OutlinedButton(
                      onPressed: busy ? null : () => setState(() => step--),
                      child: const Text('بازگشت'),
                    ),
                  const Spacer(),
                  FilledButton(
                    onPressed: busy
                        ? null
                        : (step < 2
                            ? () => setState(() => step++)
                            : _generate),
                    child: Text(busy
                        ? 'در حال تولید…'
                        : (step < 2 ? 'ادامه' : 'ساخت برنامهٔ من')),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _stepIndicator() {
    return Row(
      children: List.generate(3, (i) {
        final active = i <= step;
        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            height: 5,
            decoration: BoxDecoration(
              color: active ? MpColors.primary : MpColors.surface,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        );
      }),
    );
  }

  Widget _stepGoal() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('هدف تمرینی شما چیست؟',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _chip('افزایش حجم عضلانی', 'hypertrophy'),
            _chip('افزایش قدرت', 'strength'),
            _chip('کاهش وزن', 'weight_loss'),
            _chip('آمادگی جسمانی', 'fitness'),
          ],
        ),
        const SizedBox(height: 20),
        const Text('سطح فعلی شما؟',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          children: [
            _chip('مبتدی', 'beginner'),
            _chip('متوسط', 'intermediate'),
            _chip('پیشرفته', 'advanced'),
          ],
        ),
        const SizedBox(height: 20),
        Text('روزهای تمرین در هفته: $days',
            style: const TextStyle(fontSize: 15)),
        Slider(
          value: days.toDouble(),
          min: 3,
          max: 6,
          divisions: 3,
          label: '$days',
          onChanged: (v) => setState(() => days = v.round()),
        ),
        Text('طول برنامه: $weeks هفته', style: const TextStyle(fontSize: 15)),
        Slider(
          value: weeks.toDouble(),
          min: 4,
          max: 16,
          divisions: 6,
          label: '$weeks',
          onChanged: (v) => setState(() => weeks = v.round()),
        ),
      ],
    );
  }

  Widget _stepHistory() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('سابقهٔ تمرینی شما',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        Text('$_experienceLabel تمرین منظم',
            style: TextStyle(color: MpColors.textSecondary)),
        Slider(
          value: experienceMonths,
          min: 0,
          max: 120,
          divisions: 24,
          onChanged: (v) => setState(() => experienceMonths = v),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: weightCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                    labelText: 'وزن (کیلوگرم)', border: OutlineInputBorder()),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: TextField(
                controller: ageCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                    labelText: 'سن', border: OutlineInputBorder()),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        // M41-c1: انتخاب اجباری جنسیت — تفکیک آقایان/بانوان
        InputDecorator(
          decoration: InputDecoration(
            labelText: 'جنسیت *',
            border: OutlineInputBorder(
              borderSide: BorderSide(
                color: gender == null ? Colors.redAccent : Colors.grey,
              ),
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: ChoiceChip(
                  label: const Text('آقا'),
                  selected: gender == 'male',
                  onSelected: (_) => setState(() => gender = 'male'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ChoiceChip(
                  label: const Text('بانو'),
                  selected: gender == 'female',
                  onSelected: (_) => setState(() => gender = 'female'),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: activity,
          decoration: const InputDecoration(
              labelText: 'سطح فعالیت روزانه', border: OutlineInputBorder()),
          items: const [
            DropdownMenuItem(value: 'sedentary', child: Text('کم‌تحرک')),
            DropdownMenuItem(value: 'light', child: Text('سبک')),
            DropdownMenuItem(value: 'moderate', child: Text('متوسط')),
            DropdownMenuItem(value: 'active', child: Text('پرتحرک')),
            DropdownMenuItem(value: 'athlete', child: Text('ورزشکار حرفه‌ای')),
          ],
          onChanged: (v) => setState(() => activity = v ?? 'moderate'),
        ),
      ],
    );
  }

  Widget _stepConstraints() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('آسیب یا محدودیت خاصی دارید؟',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text('موتور برنامه‌ریزی حرکات نامناسب را حذف می‌کند',
            style: TextStyle(color: MpColors.textSecondary)),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: allConstraints.map((c) {
            final on = constraints.contains(c);
            return FilterChip(
              label: Text(c),
              selected: on,
              onSelected: (v) => setState(() {
                v ? constraints.add(c) : constraints.remove(c);
              }),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _chip(String label, String value) {
    final selected = goal == value || level == value;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => setState(() {
        const goals = ['hypertrophy', 'strength', 'weight_loss', 'fitness'];
        if (goals.contains(value)) {
          goal = value;
        } else {
          level = value;
        }
      }),
    );
  }
}
