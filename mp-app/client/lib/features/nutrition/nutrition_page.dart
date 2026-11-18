/// تغذیهٔ واقعی — برنامه و دفتر غذای روزانه از API موجود MP.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/app_state.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';
import 'adaptive_nutrition_card.dart';

class NutritionPage extends ConsumerWidget {
  const NutritionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plan = ref.watch(nutritionProvider);
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          plan.when(
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (e, _) =>
                GlassCard(child: Text('خطا: $e', textAlign: TextAlign.center)),
            data: (p) {
              if (p == null) {
                return GlassCard(
                  child: Column(
                    children: [
                      const Icon(
                        Icons.restaurant,
                        size: 44,
                        color: MpColors.accent,
                      ),
                      const SizedBox(height: 10),
                      const Text(
                        'برنامهٔ غذایی ندارید',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'در جریان ساخت برنامه، تغذیه هم محاسبه می‌شود',
                        style: TextStyle(color: MpColors.textSecondary),
                      ),
                    ],
                  ),
                );
              }
              final kcal = p['daily_kcal'] ?? p['target_kcal'] ?? 0;
              return Column(
                children: [
                  GlassCard(
                    child: Column(
                      children: [
                        Text(
                          'کالری روزانه',
                          style: TextStyle(color: MpColors.textSecondary),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '$kcal کیلوکالری',
                          style: const TextStyle(
                            fontSize: 30,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _macro('پروتئین', p['protein_g'], MpColors.primary),
                      const SizedBox(width: 8),
                      _macro('کربوهیدرات', p['carbs_g'], MpColors.info),
                      const SizedBox(width: 8),
                      _macro('چربی', p['fat_g'], MpColors.accent),
                    ],
                  ),
                  if ((p['llm_explanation'] as String? ?? '').isNotEmpty) ...[
                    const SizedBox(height: 12),
                    GlassCard(
                      child: Text(
                        p['llm_explanation'] as String,
                        style: const TextStyle(height: 1.8),
                      ),
                    ),
                  ],
                ],
              );
            },
          ),
          const SizedBox(height: 20),
          const _DailyFoodLog(),
          const SizedBox(height: 20),
          const AdaptiveNutritionCard(),
        ],
      ),
    );
  }

  Widget _macro(String label, dynamic grams, Color color) {
    return Expanded(
      child: GlassCard(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Column(
          children: [
            Text(
              '$grams گرم',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

/// مقدار ورودی با رقم فارسی/عربی یا لاتین؛ محدودیت endpoint هم رعایت می‌شود.
double? parseFoodLogGrams(String raw) {
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
  if (value == null || !value.isFinite || value <= 0 || value > 5000)
    return null;
  return value;
}

String _persianDigits(String value) =>
    value.replaceAllMapped(RegExp(r'\d'), (match) {
      return '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)];
    });

String _numberText(dynamic value) {
  if (value is! num || !value.isFinite) return 'نامعلوم';
  final number = value.toDouble();
  final text = number == number.roundToDouble()
      ? number.toStringAsFixed(0)
      : number.toStringAsFixed(1);
  return _persianDigits(text);
}

String _dateKey(DateTime date) =>
    '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';

String _mealName(dynamic slot) => switch (slot) {
      'breakfast' => 'صبحانه',
      'lunch' => 'ناهار',
      'dinner' => 'شام',
      'snack' => 'میان‌وعده',
      _ => 'وعدهٔ نامشخص',
    };

class _DailyFoodLog extends ConsumerStatefulWidget {
  const _DailyFoodLog();

  @override
  ConsumerState<_DailyFoodLog> createState() => _DailyFoodLogState();
}

class _DailyFoodLogState extends ConsumerState<_DailyFoodLog> {
  final _searchController = TextEditingController();
  final _gramsController = TextEditingController();
  String? _searchQuery;
  String _mealSlot = 'snack';
  Map<String, dynamic>? _selectedFood;
  bool _saving = false;

  @override
  void dispose() {
    _searchController.dispose();
    _gramsController.dispose();
    super.dispose();
  }

  void _submitSearch() {
    final query = _searchController.text.trim();
    if (query.runes.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('برای جست‌وجو دست‌کم دو نویسه وارد کنید')),
      );
      return;
    }
    setState(() {
      _searchQuery = query;
      _selectedFood = null;
      _gramsController.clear();
    });
  }

  Future<void> _save(int memberId, String day) async {
    final food = _selectedFood;
    final grams = parseFoodLogGrams(_gramsController.text);
    if (food == null || food['id'] is! num) {
      _notify('ابتدا یک خوراکی از نتیجه‌های کاتالوگ انتخاب کنید');
      return;
    }
    if (grams == null) {
      _notify('مقدار معتبر بین ۰ و ۵۰۰۰ گرم وارد کنید');
      return;
    }

    setState(() => _saving = true);
    try {
      final response = await ref.read(apiClientProvider).post(
        '/nutrition/food-logs',
        {
          'member_id': memberId,
          'entries': [
            {
              'food_id': food['id'],
              'grams': grams,
              'meal_slot': _mealSlot,
              'logged_for_date': day,
            },
          ],
        },
      );
      if (response is! Map) {
        throw const FormatException('پاسخ ثبت خوراکی نامعتبر است');
      }
      final result = Map<String, dynamic>.from(response);
      final logged = result['logged'];
      if (logged is num && logged > 0) {
        if (!mounted) return;
        ref.invalidate(foodLogDailyProvider((memberId: memberId, date: day)));
        setState(() {
          _selectedFood = null;
          _gramsController.clear();
        });
        _notify(
          result['reason'] is String
              ? result['reason'] as String
              : 'وعده ثبت شد',
        );
      } else {
        _notify(
          result['reason'] is String
              ? result['reason'] as String
              : 'وعده ثبت نشد',
        );
      }
    } on ApiException catch (error) {
      _notify('ثبت انجام نشد: ${error.message}');
    } catch (_) {
      _notify('ثبت انجام نشد؛ پاسخ سرور قابل‌تأیید نبود');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _notify(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final memberId = ref.watch(authProvider).memberId;
    if (memberId == null) {
      return const GlassCard(
        child: Text(
          'برای دیدن و ثبت غذای روزانه، نشست عضو لازم است.',
          textAlign: TextAlign.center,
        ),
      );
    }

    final day = _dateKey(
      DateTime.now(),
    ); // تاریخ محلی؛ قرارداد food_logs هم محلی است.
    final dailyKey = (memberId: memberId, date: day);
    final daily = ref.watch(foodLogDailyProvider(dailyKey));
    final search = ref.watch(foodSearchProvider(_searchQuery ?? ''));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _dailySummary(daily, dailyKey),
        const SizedBox(height: 12),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'ثبت غذای امروز',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(
                'منبع: Food Finder (MIT)؛ مقدارها برای هر ۱۰۰ گرم‌اند. چربی در منبع مستقیم نیست و در دفتر روزانه نمایش داده نمی‌شود.',
                style: TextStyle(
                  color: MpColors.textSecondary,
                  height: 1.6,
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                key: const Key('food-search-field'),
                controller: _searchController,
                textDirection: TextDirection.rtl,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _submitSearch(),
                decoration: InputDecoration(
                  labelText: 'نام غذا یا مادهٔ غذایی',
                  hintText: 'مثلاً قورمه سبزی یا برنج پخته',
                  suffixIcon: IconButton(
                    tooltip: 'جست‌وجو',
                    onPressed: _submitSearch,
                    icon: const Icon(Icons.search),
                  ),
                ),
              ),
              if (_searchQuery != null) ...[
                const SizedBox(height: 10),
                _searchResults(search),
              ],
              if (_selectedFood != null) ...[
                const SizedBox(height: 12),
                _selectedFoodForm(memberId, day),
              ],
            ],
          ),
        ),
      ],
    );
  }

  Widget _dailySummary(
    AsyncValue<Map<String, dynamic>> daily,
    ({int memberId, String date}) key,
  ) {
    return daily.when(
      loading: () =>
          const GlassCard(child: Center(child: CircularProgressIndicator())),
      error: (_, __) => GlassCard(
        child: Column(
          children: [
            const Text('جمع غذای امروز از سرور دریافت نشد؛ صفر فرض نمی‌شود.'),
            TextButton.icon(
              onPressed: () => ref.invalidate(foodLogDailyProvider(key)),
              icon: const Icon(Icons.refresh),
              label: const Text('تلاش دوباره'),
            ),
          ],
        ),
      ),
      data: (data) {
        if (data['data_state'] == 'nothing_logged') {
          return GlassCard(
            child: Column(
              children: [
                const Text(
                  'مصرف امروز هنوز ثبت نشده است',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 4),
                Text(
                  'صفر یعنی «ثبت نشده»، نه اینکه چیزی نخورده‌اید.',
                  style: TextStyle(color: MpColors.textSecondary),
                ),
              ],
            ),
          );
        }
        if (data['data_state'] != 'logged' ||
            data['totals'] is! Map ||
            data['items'] is! List) {
          return const GlassCard(
            child: Text(
              'پاسخ دفتر غذای روزانه قابل‌تأیید نیست؛ جمعی نمایش داده نشد.',
            ),
          );
        }

        final totals = Map<String, dynamic>.from(data['totals'] as Map);
        final rawItems = data['items'] as List;
        final items = <Map<String, dynamic>>[];
        for (final raw in rawItems) {
          if (raw is! Map) {
            return const GlassCard(
              child: Text('یک ردیف دفتر غذا نامعتبر است؛ جمعی نمایش داده نشد.'),
            );
          }
          items.add(Map<String, dynamic>.from(raw));
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            GlassCard(
              child: Column(
                children: [
                  Text(
                    'جمع ثبت‌شدهٔ امروز',
                    style: TextStyle(color: MpColors.textSecondary),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    '${_numberText(totals['kcal'])} کیلوکالری',
                    key: const Key('food-daily-kcal'),
                    style: const TextStyle(
                      fontSize: 25,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text('${_numberText(totals['protein_g'])} گرم پروتئین'),
                      const SizedBox(width: 14),
                      Text('${_numberText(totals['carbs_g'])} گرم کربوهیدرات'),
                    ],
                  ),
                ],
              ),
            ),
            for (final item in items) ...[
              const SizedBox(height: 8),
              _loggedItem(item),
            ],
          ],
        );
      },
    );
  }

  Widget _loggedItem(Map<String, dynamic> item) {
    final name = item['name_fa'] is String
        ? item['name_fa'] as String
        : 'نام غذا نامعلوم';
    final warning = item['warning'] is String ? item['warning'] as String : '';
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name, style: const TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 3),
          Text(
            '${_mealName(item['meal_slot'])} · ${_numberText(item['grams'])} گرم · ${_numberText(item['kcal'])} کیلوکالری',
            style: TextStyle(color: MpColors.textSecondary, fontSize: 12),
          ),
          if (warning.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              warning,
              style: TextStyle(color: MpColors.accent, fontSize: 11),
            ),
          ],
        ],
      ),
    );
  }

  Widget _searchResults(AsyncValue<List<Map<String, dynamic>>> search) {
    return search.when(
      loading: () => const Padding(
        padding: EdgeInsets.all(12),
        child: Center(child: CircularProgressIndicator()),
      ),
      error: (_, __) =>
          const Text('جست‌وجوی کاتالوگ انجام نشد؛ بعداً دوباره تلاش کنید.'),
      data: (rows) {
        if (rows.isEmpty) {
          return const Text('موردی در کاتالوگ با این نام پیدا نشد.');
        }
        return Column(
          children: [
            for (final food in rows) ...[
              const SizedBox(height: 6),
              GlassCard(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 10,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            food['name_fa'] is String
                                ? food['name_fa'] as String
                                : 'نام نامعلوم',
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          Text(
                            '${food['category'] ?? 'دسته نامعلوم'} · ${_numberText(food['kcal_per_100g'])} کیلوکالری در ۱۰۰ گرم',
                            style: TextStyle(
                              color: MpColors.textSecondary,
                              fontSize: 11,
                            ),
                          ),
                          if (food['dry_or_raw'] == true)
                            Text(
                              'وزن خشک/خام؛ مقدار پخته را با این ردیف یکی نگیرید.',
                              style: TextStyle(
                                color: MpColors.accent,
                                fontSize: 11,
                              ),
                            ),
                        ],
                      ),
                    ),
                    TextButton(
                      onPressed: () => setState(() {
                        _selectedFood = food;
                        _gramsController.clear();
                      }),
                      child: const Text('انتخاب'),
                    ),
                  ],
                ),
              ),
            ],
          ],
        );
      },
    );
  }

  Widget _selectedFoodForm(int memberId, String day) {
    final food = _selectedFood!;
    final name = food['name_fa'] is String
        ? food['name_fa'] as String
        : 'غذای انتخاب‌شده';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'انتخاب‌شده: $name',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        TextField(
          key: const Key('food-grams-field'),
          controller: _gramsController,
          textDirection: TextDirection.rtl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(
            labelText: 'مقدار مصرف‌شده (گرم)',
            hintText: 'مثلاً ۱۵۰',
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _mealSlot,
          decoration: const InputDecoration(labelText: 'وعده'),
          items: const [
            DropdownMenuItem(value: 'breakfast', child: Text('صبحانه')),
            DropdownMenuItem(value: 'lunch', child: Text('ناهار')),
            DropdownMenuItem(value: 'dinner', child: Text('شام')),
            DropdownMenuItem(value: 'snack', child: Text('میان‌وعده')),
          ],
          onChanged: (value) {
            if (value != null) setState(() => _mealSlot = value);
          },
        ),
        const SizedBox(height: 10),
        ElevatedButton.icon(
          key: const Key('food-log-save'),
          onPressed: _saving ? null : () => _save(memberId, day),
          icon: _saving
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(),
                )
              : const Icon(Icons.add),
          label: Text(_saving ? 'در حال ثبت…' : 'ثبت وعده'),
        ),
      ],
    );
  }
}
