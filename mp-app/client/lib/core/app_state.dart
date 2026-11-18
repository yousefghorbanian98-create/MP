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
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن کیف‌پول در نشست موجود نیست');
  }
  final r = await api.get('/payments/wallet/$memberId');
  return Map<String, dynamic>.from(r as Map);
});

/// تاریخچهٔ پرداخت‌های من — G1 از ممیزی رقابتی.
///
/// پیش از این، عضو هیچ‌جا نمی‌دید پولش کجا رفته است: استودیو گزارش مالی داشت
/// ولی اپ عضو هیچ صفحه‌ای نداشت، در حالی که `GET /payments` از قبل وجود داشت
/// (و سمت سرور عضو را مجبور می‌کند فقط پرداخت‌های خودش را ببیند).
final myPaymentsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/payments');
  if (r is List) return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  return const [];
});

/// اشتراک‌های عضو — منبع «چقدر اعتبار دارم؟».
///
/// M61/D5: بنر خانه متنی ثابت بود («تولدت مبارک! ۲۰٪ تخفیف تمدید») که هیچ
/// پشتوانه‌ای نداشت — نه کوپنی وجود دارد، نه منطق تولدی. اکنون همان بنر از
/// دادهٔ واقعی اشتراک ساخته می‌شود و اگر اشتراکی نباشد، همین را می‌گوید.
/// سرور با `ensure_member_scope` تضمین می‌کند عضو فقط اشتراک خودش را ببیند.
final myMembershipsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن اشتراک در نشست موجود نیست');
  }
  final r = await api.get('/members/$memberId/memberships');
  if (r is! List) {
    throw const FormatException('پاسخ تاریخچهٔ اشتراک عضو باید یک فهرست باشد');
  }
  return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
});

/// فروشگاه واقعی — کاتالوگ از API (M59). پیش‌تر چهار محصول hardcode بود.
final shopProductsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/products');
  if (r is List) return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  return const [];
});

/// دسته‌های فروشگاه (مکمل/تجهیزات/پوشاک).
final shopCategoriesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/categories');
  if (r is List) return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  return const [];
});

/// سبد خرید من — مبلغ از سرور می‌آید، نه از کلاینت.
final cartProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/cart');
  return Map<String, dynamic>.from(r as Map);
});

/// سفارش‌های من.
final shopOrdersProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/orders');
  if (r is List) return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  return const [];
});

/// درگاه‌های فعال و شمارهٔ کارت (ماسک‌شده) — خواندن برای همه مجاز است.
final gatewaysProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/gateways');
  if (r is List) return r.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  return const [];
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

/// جستجوی غذای موجود در کاتالوگ MP؛ بدون fallback به غذای فرضی/محلی.
final foodSearchProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String>((ref, query) async {
  final normalized = query.trim();
  if (normalized.length < 2) return const [];
  final api = ref.watch(apiClientProvider);
  final r = await api.get(
    '/nutrition/foods?q=${Uri.encodeQueryComponent(normalized)}&limit=25',
  );
  if (r is! List) {
    throw const FormatException('پاسخ جستجوی غذا باید یک فهرست باشد');
  }
  return r.map((row) {
    if (row is! Map) throw const FormatException('ردیف غذای دریافتی نامعتبر است');
    return Map<String, dynamic>.from(row);
  }).toList();
});

/// جمع روزانه و ثبت‌های واقعی، عضو-محور و بر اساس تاریخ محلی باشگاه.
final foodLogDailyProvider =
    FutureProvider.family<Map<String, dynamic>, ({int memberId, String date})>(
  (ref, key) async {
    final api = ref.watch(apiClientProvider);
    final r = await api.get(
      '/nutrition/food-logs/member/${key.memberId}/daily?date=${Uri.encodeQueryComponent(key.date)}',
    );
    if (r is! Map) {
      throw const FormatException('پاسخ جمع غذای روزانه باید یک شیء باشد');
    }
    return Map<String, dynamic>.from(r);
  },
);

/// صندوق اعلان عضو جاری؛ هویت از نشست می‌آید و payload نامعتبر خطای صریح است.
final myNotificationsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final memberId = ref.watch(authProvider).memberId;
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن اعلان‌ها در نشست موجود نیست');
  }
  final r = await ref.watch(apiClientProvider).get('/notifications/member/$memberId');
  if (r is! List) {
    throw const FormatException('پاسخ اعلان‌های عضو باید یک فهرست باشد');
  }
  return r.map((row) {
    if (row is! Map) throw const FormatException('اعلان دریافتی نامعتبر است');
    final notification = Map<String, dynamic>.from(row);
    if (notification['id'] is! num || notification['title'] is! String) {
      throw const FormatException('شناسه یا عنوان اعلان دریافتی نامعتبر است');
    }
    final createdAt = notification['created_at'];
    if (createdAt is! String || DateTime.tryParse(createdAt) == null) {
      throw const FormatException('زمان ثبت اعلان دریافتی نامعتبر است');
    }
    return notification;
  }).toList();
});

/// شمارش unread از پاسخ واقعی inbox؛ خطای شبکه را به شمارش ساختگی تبدیل نمی‌کند.
final myUnreadNotificationsCountProvider = Provider<int>((ref) {
  final notifications = ref.watch(myNotificationsProvider);
  return notifications.maybeWhen(
    data: (rows) => rows.where((row) => row['read_at'] == null).length,
    orElse: () => 0,
  );
});

/// آمادگی از endpoint واقعی عضو؛ score فقط وقتی ساختار پاسخ معتبر است نمایش داده می‌شود.
final readinessProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final memberId = ref.watch(authProvider).memberId;
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن آمادگی در نشست موجود نیست');
  }
  final raw = await ref.watch(apiClientProvider).get('/programs/member/$memberId/readiness');
  if (raw is! Map) throw const FormatException('پاسخ آمادگی باید یک شیء باشد');
  final report = Map<String, dynamic>.from(raw);
  if (report['member_id'] != memberId || report['reason'] is! String) {
    throw const FormatException('مالک یا دلیل پاسخ آمادگی نامعتبر است');
  }
  final rawReadiness = report['readiness'];
  if (rawReadiness == null) return report;
  if (rawReadiness is! Map) throw const FormatException('ساختار امتیاز آمادگی نامعتبر است');
  final readiness = Map<String, dynamic>.from(rawReadiness);
  if (readiness['band'] is! String ||
      readiness['recommendation'] is! String ||
      readiness['reason'] is! String ||
      (readiness['score'] != null && readiness['score'] is! num) ||
      readiness['signals'] is! List ||
      readiness['missing_signals'] is! List) {
    throw const FormatException('سیگنال‌ها یا امتیاز آمادگی نامعتبر است');
  }
  for (final rawSignal in readiness['signals'] as List) {
    if (rawSignal is! Map ||
        rawSignal['name'] is! String ||
        rawSignal['reason'] is! String ||
        (rawSignal['score'] != null && rawSignal['score'] is! num)) {
      throw const FormatException('یک سیگنال آمادگی نامعتبر است');
    }
  }
  if ((readiness['missing_signals'] as List).any((signal) => signal is! String)) {
    throw const FormatException('فهرست سیگنال‌های ناموجود نامعتبر است');
  }
  return report;
});

/// گزارش هفتگی حجم هر عضله از API عضو؛ دادهٔ نامعتبر نباید به حجم صفر تبدیل شود.
final volumeProvider = FutureProvider.family<Map<String, dynamic>, String>((ref, level) async {
  const levels = {'beginner', 'intermediate', 'advanced'};
  if (!levels.contains(level)) throw ArgumentError.value(level, 'level');
  final memberId = ref.watch(authProvider).memberId;
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن حجم هفتگی در نشست موجود نیست');
  }
  final raw = await ref.watch(apiClientProvider).get(
    '/programs/member/$memberId/volume?level=$level',
  );
  if (raw is! Map) throw const FormatException('پاسخ حجم هفتگی باید یک شیء باشد');
  final report = Map<String, dynamic>.from(raw);
  if (report['member_id'] != memberId || report['reason'] is! String || report['muscles'] is! List) {
    throw const FormatException('مالک یا فهرست عضله‌های گزارش نامعتبر است');
  }
  for (final rawRow in report['muscles'] as List) {
    if (rawRow is! Map) throw const FormatException('ردیف حجم عضله نامعتبر است');
    final row = Map<String, dynamic>.from(rawRow);
    if (row['muscle'] is! String ||
        row['status'] is! String ||
        row['data_state'] is! String ||
        row['source_of_number'] is! String ||
        ['planned_sets', 'effective_sets', 'hard_sets', 'soft_sets', 'unknown_rir_sets']
            .any((key) => row[key] is! num) ||
        row['landmarks'] is! Map ||
        row['suggestion'] is! Map) {
      throw const FormatException('مقادیر حجم عضله ناقص یا نامعتبر است');
    }
    final landmarks = Map<String, dynamic>.from(row['landmarks'] as Map);
    if (['mv', 'mev', 'mav_min', 'mav_max', 'mrv', 'hard_set_max_rir']
            .any((key) => landmarks[key] is! num) ||
        landmarks['source'] is! String) {
      throw const FormatException('نشانگرهای MV/MEV/MAV/MRV نامعتبر است');
    }
    final suggestion = Map<String, dynamic>.from(row['suggestion'] as Map);
    if (suggestion['delta_sets'] is! num || suggestion['reason'] is! String) {
      throw const FormatException('پیشنهاد حجم هفتگی نامعتبر است');
    }
  }
  return report;
});

/// TDEE و پیشنهاد کالری از گزارش سازگار موجود؛ ناکافی بودن داده صریح می‌ماند.
final adaptiveNutritionProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final memberId = ref.watch(authProvider).memberId;
  if (memberId == null) {
    throw StateError('شناسهٔ عضو برای خواندن تخمین تغذیه در نشست موجود نیست');
  }
  final raw = await ref.watch(apiClientProvider).get('/nutrition/member/$memberId/adaptive');
  if (raw is! Map) throw const FormatException('پاسخ تغذیهٔ سازگار باید یک شیء باشد');
  final report = Map<String, dynamic>.from(raw);
  if (report['member_id'] != memberId || report['estimate'] is! Map || report['suggestion'] is! Map) {
    throw const FormatException('مالک یا ساختار گزارش تغذیهٔ سازگار نامعتبر است');
  }
  final estimate = Map<String, dynamic>.from(report['estimate'] as Map);
  final suggestion = Map<String, dynamic>.from(report['suggestion'] as Map);
  if ((estimate['tdee_kcal'] != null && estimate['tdee_kcal'] is! num) ||
      (estimate['mean_intake_kcal'] != null && estimate['mean_intake_kcal'] is! num) ||
      estimate['confidence'] is! String ||
      estimate['reason'] is! String ||
      estimate['trend'] is! Map ||
      suggestion['action'] is! String ||
      suggestion['delta_kcal'] is! num ||
      suggestion['reason'] is! String ||
      (suggestion['suggested_target_kcal'] != null && suggestion['suggested_target_kcal'] is! num) ||
      report['data_counts'] is! Map ||
      report['goal'] is! String) {
    throw const FormatException('مقادیر تخمین یا پیشنهاد کالری نامعتبر است');
  }
  final trend = Map<String, dynamic>.from(estimate['trend'] as Map);
  if ((trend['slope_kg_per_week'] != null && trend['slope_kg_per_week'] is! num) ||
      (trend['notes'] != null && trend['notes'] is! List)) {
    throw const FormatException('روند وزن در گزارش نامعتبر است');
  }
  final counts = Map<String, dynamic>.from(report['data_counts'] as Map);
  if (counts['weight_entries'] is! num || counts['intake_days'] is! num) {
    throw const FormatException('شمار داده‌های ورودی نامعتبر است');
  }
  if ((report['current_target_kcal'] != null && report['current_target_kcal'] is! num) ||
      (report['latest_weight_kg'] != null && report['latest_weight_kg'] is! num)) {
    throw const FormatException('هدف یا وزن آخر گزارش نامعتبر است');
  }
  return report;
});

/// رسید یک سفارش — `GET /shop/orders/{id}/receipt` (M90).
///
/// endpoint از M60/R5 مالکیت‌محور است (عضو فقط سفارش خودش؛ تست backend در
/// `tests/integration/test_m60_shop.py`)؛ این provider همان مرز را در کلاینت هم
/// نگه می‌دارد و پاسخ نامطابق را نمایش نمی‌دهد. هیچ مبلغی به سرور فرستاده نمی‌شود:
/// مسیر `GET` است و جمع‌ها از همان پاسخ خوانده می‌شوند.
final orderReceiptProvider =
    FutureProvider.autoDispose.family<Map<String, dynamic>, int>((ref, orderId) async {
  final api = ref.watch(apiClientProvider);
  final r = await api.get('/shop/orders/$orderId/receipt');
  if (r is! Map) {
    throw const FormatException('پاسخ رسید باید یک شیء باشد');
  }
  final receipt = Map<String, dynamic>.from(r);
  if (receipt['order_id'] != orderId) {
    throw const FormatException('رسید به سفارش دیگری تعلق دارد');
  }
  final memberId = ref.watch(authProvider).memberId;
  if (memberId != null && receipt['member_id'] != memberId) {
    throw const FormatException('رسید متعلق به عضو این نشست نیست');
  }
  final lines = receipt['lines'];
  if (lines is! List) {
    throw const FormatException('اقلام رسید باید یک فهرست باشند');
  }
  for (final line in lines) {
    if (line is! Map) {
      throw const FormatException('یک قلم از رسید ساختار معتبر ندارد');
    }
    if (line['unit_price_rial'] is! num ||
        line['qty'] is! num ||
        line['line_total_rial'] is! num) {
      throw const FormatException('مبلغ/تعداد یک قلم از رسید نامعتبر است');
    }
  }
  if (receipt['total_rial'] is! num) {
    throw const FormatException('مبلغ کل رسید نامعتبر است');
  }
  final status = receipt['status'];
  if (status != null && status is! String) {
    throw const FormatException('وضعیت سفارش نامعتبر است');
  }
  return receipt;
});
