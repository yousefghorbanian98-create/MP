/// وضعیت مشترک داده‌های واقعی — برنامه/کیف‌پول/کلاس‌ها از API (M32).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'session.dart';

/// برنامه‌های عضو (آخرین برنامه مبنا است).
final myProgramsProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) return [];
  final r = await api.get('/programs/member/$memberId');
  if (r is List) return r;
  if (r is Map && r['programs'] is List) return r['programs'] as List<dynamic>;
  return [];
});

/// آخرین برنامهٔ تأییدشده/پیش‌نویس.
final activeProgramProvider = Provider<Map<String, dynamic>?>((ref) {
  final list = ref.watch(myProgramsProvider).value;
  if (list == null || list.isEmpty) return null;
  return list.first as Map<String, dynamic>;
});

/// تمرین‌های امروز (هفتهٔ ۱، روز بر اساس روز هفته).
final todayExercisesProvider = Provider<List<Map<String, dynamic>>>((ref) {
  final program = ref.watch(activeProgramProvider);
  if (program == null) return [];
  final weeks = (program['weeks'] as List?) ?? const [];
  if (weeks.isEmpty) return [];
  final w0 = weeks.first as Map<String, dynamic>;
  final exercises = (w0['exercises'] as List?) ?? const [];
  final day = DateTime.now().weekday; // ۱..۷
  final today = exercises
      .where((e) => (e as Map<String, dynamic>)['day'] == day)
      .map((e) => e as Map<String, dynamic>)
      .toList();
  // اگر امروز جلسه نیست، روز اول برنامه نمایش داده می‌شود (هرگز خالی بی‌دلیل نه)
  if (today.isNotEmpty) return today;
  return exercises
      .where((e) => (e as Map<String, dynamic>)['day'] == 1)
      .map((e) => e as Map<String, dynamic>)
      .toList();
});

/// ماندهٔ کیف‌پول.
final walletProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) return {'balance_rial': 0};
  final r = await api.get('/payments/wallet/$memberId');
  return Map<String, dynamic>.from(r as Map);
});

/// کلاس‌های باشگاه.
final classesProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/classes');
  if (r is List) return r;
  return [];
});

/// برنامهٔ غذایی فعال عضو.
final nutritionProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) return null;
  try {
    final r = await api.get('/nutrition/plans/member/$memberId');
    if (r is List && r.isNotEmpty) return Map<String, dynamic>.from(r.first as Map);
    return null;
  } catch (_) {
    return null;
  }
});
