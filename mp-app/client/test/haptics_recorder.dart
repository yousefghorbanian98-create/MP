/// فیک `MpHaptics` برای تست‌های ویجت (M98).
///
/// چرا فایل جدا: سه صفحه (بازخورد ست، کلاس‌ها، فروشگاه) باید «پالس ارسال شد یا
/// نه» را بسنجند؛ کپی‌کردن کلاس فیک در هر تست همان الگویی است که در `core`
/// حذفش کردیم. تست‌ها روی ترتیب و تعداد اتفاق توافق می‌کنند، نه روی نام کانال.
library;

import 'package:mp_client/core/haptics.dart';

class RecordingHaptics implements MpHaptics {
  final List<String> events = [];

  int count(String kind) => events.where((e) => e == kind).length;

  @override
  Future<void> select() async => events.add('select');

  @override
  Future<void> success() async => events.add('success');

  @override
  Future<void> warning() async => events.add('warning');
}
