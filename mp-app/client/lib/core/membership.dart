/// محاسبهٔ «چند روز اعتبار مانده» — یک تابع، یک تست.
///
/// چرا فایل جدا: LEDGER #13 همین‌جا ثبت شده است — `timedelta.days` (و معادل
/// Dartش `.inDays`) کف می‌گیرد، پس ۰٫۹ روز مانده «۰ روز» یعنی «همین حالا تمام
/// شد» نمایش داده می‌شد. این تابع `ceil` می‌کند و حالت‌های مرزی را صریح
/// برمی‌گرداند تا UI مجبور نباشد حدس بزند.
library;

/// روزهای باقی‌مانده تا [iso]، با گردکردن به **بالا**.
///
/// - null یا تاریخ نامعتبر → `null` («نامعلوم»، نه صفر — قاعدهٔ «نامعلوم ≠ صفر»)
/// - تاریخ گذشته یا همین لحظه → `0`
///
/// [now] فقط برای تست تزریق می‌شود.
int? daysUntilExpiry(String? iso, {DateTime? now}) {
  if (iso == null || iso.isEmpty) return null;
  final expires = DateTime.tryParse(iso);
  if (expires == null) return null;
  final seconds = expires.difference(now ?? DateTime.now()).inSeconds;
  if (seconds <= 0) return 0;
  return (seconds / 86400).ceil();
}
