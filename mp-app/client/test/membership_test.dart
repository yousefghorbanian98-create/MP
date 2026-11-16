/// تست محاسبهٔ روز باقی‌ماندهٔ اشتراک — همان باگ LEDGER #13.
///
/// چرا: `inDays` کف می‌گیرد. با ۲۳ ساعت مانده، کاربر «۰ روز» می‌دید، یعنی
/// «اشتراکت تمام شد» — در حالی که تا فردا وقت داشت و می‌توانست چک‌این کند.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/membership.dart';

void main() {
  final now = DateTime.utc(2026, 11, 16, 12, 0, 0);

  test('۲۳ ساعت مانده = ۱ روز، نه ۰ (همان باگ LEDGER #13)', () {
    expect(daysUntilExpiry('2026-11-17T11:00:00Z', now: now), 1);
  });

  test('۲۴ روز کامل = ۲۴', () {
    expect(daysUntilExpiry('2026-12-10T12:00:00Z', now: now), 24);
  });

  test('دقیقاً همین لحظه = ۰', () {
    expect(daysUntilExpiry('2026-11-16T12:00:00Z', now: now), 0);
  });

  test('گذشته = ۰، نه منفی', () {
    expect(daysUntilExpiry('2026-11-01T12:00:00Z', now: now), 0);
  });

  test('null و رشتهٔ نامعتبر = null («نامعلوم»، نه صفر)', () {
    expect(daysUntilExpiry(null, now: now), isNull);
    expect(daysUntilExpiry('', now: now), isNull);
    expect(daysUntilExpiry('not-a-date', now: now), isNull);
  });

  test('۱ ثانیه مانده = ۱ روز (سقف، نه صفر)', () {
    expect(daysUntilExpiry('2026-11-16T12:00:01Z', now: now), 1);
  });
}
