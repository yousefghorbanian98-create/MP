/// ارزیابی ۱۴ توانایی — providers (M37).
///
/// داده از API: ماتریس درصد + تصمیم چهارگانه. قانون M18: کلاینت فقط نمایش/ثبت ورودی؛
/// محاسبه در backend (engine) انجام می‌شود — هیچ نمره‌ای در کلاینت ساخته نمی‌شود.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';

/// ماتریس آخرین ارزیابی عضو — null یعنی هنوز ارزیابی ثبت نشده.
final axisMatrixProvider = FutureProvider<Map<String, dynamic>?>((ref) async {
  final api = ref.watch(apiClientProvider);
  final auth = ref.watch(authProvider);
  final memberId = auth.memberId;
  if (memberId == null) return null;
  try {
    final history = await api.get('/axis-assessments/member/$memberId');
    if (history is List && history.isNotEmpty) {
      final latestId = history.first['assessment_id'];
      final matrix = await api.get('/axis-assessments/$latestId/matrix');
      if (matrix is Map<String, dynamic>) return matrix;
    }
    return null;
  } catch (_) {
    return null;
  }
});

/// ارسال آزمون‌های جدید — تابع قابل override برای تست.
final submitAxisTestsProvider =
    Provider<Future<bool> Function(List<Map<String, dynamic>>)>((ref) {
      return (tests) async {
        final api = ref.read(apiClientProvider);
        final auth = ref.read(authProvider);
        final memberId = auth.memberId;
        if (memberId == null) return false;
        final r = await api.post('/axis-assessments', {
          'member_id': memberId,
          'tests': tests,
        });
        if (r is Map<String, dynamic>) {
          ref.invalidate(axisMatrixProvider);
          return true;
        }
        return false;
      };
    });

/// برچسب فارسی آزمون‌های میدانی برای فرم ورود.
const Map<String, String> testLabelsFa = {
  'sit_and_reach': 'نشست و رسیدن (سانتی‌متر)',
  'pushup_1min': 'شنای سوئدی یک دقیقه‌ای (تکرار)',
  'grip_kg': 'قدرت گرفتن دست (کیلوگرم)',
  'cooper_1_5mile_sec': 'دوی ۱٫۵ مایل (ثانیه)',
  'plank_secs': 'پلانک (ثانیه)',
  'rubric_balance': 'تعادل (امتیاز ۰ تا ۱۰۰)',
  'rubric_posture': 'وضعیت بدنی (امتیاز ۰ تا ۱۰۰)',
  'rubric_coordination': 'هماهنگی (امتیاز ۰ تا ۱۰۰)',
  'rubric_lifting': 'مکانیک بلند کردن بار (امتیاز ۰ تا ۱۰۰)',
  'rubric_breath': 'کنترل تنفس (امتیاز ۰ تا ۱۰۰)',
  'rubric_recovery': 'بازیابی و خواب (امتیاز ۰ تا ۱۰۰)',
  'rubric_body_awareness': 'آگاهی بدن (امتیاز ۰ تا ۱۰۰)',
  'rubric_foundational': 'مهارت‌های پایه (امتیاز ۰ تا ۱۰۰)',
};
