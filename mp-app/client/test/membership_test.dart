/// آزمون‌های M72 برای وضعیت اشتراک، مرز انقضا، تاریخ پایان و روزهای باقی‌مانده.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/core/membership.dart';

void main() {
  final now = DateTime.utc(2026, 11, 16, 12, 0, 0);

  test('۲۳ ساعت مانده = ۱ روز، نه ۰ (LEDGER #13)', () {
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

  test('حتی یک میکروثانیه مانده = ۱ روز (گردکردن رو به بالا)', () {
    expect(daysUntilExpiry('2026-11-16T12:00:00.000001Z', now: now), 1);
  });

  test('timestamp بدون timezone مطابق قرارداد SQLite به UTC تعبیر می‌شود', () {
    expect(daysUntilExpiry('2026-11-17T11:00:00', now: now), 1);
  });

  test('اشتراک فعال، تاریخ پایان و وضعیت را از رکورد API می‌گیرد', () {
    final summary = summarizeMemberships([
      {
        'id': 5,
        'status': 'active',
        'plan_name': 'پلن ماهانه',
        'expires_at': '2026-11-17T11:00:00Z',
      },
    ], now: now);

    expect(summary.status, MembershipDisplayStatus.active);
    expect(summary.membership?['plan_name'], 'پلن ماهانه');
    expect(
      summary.expiresAt?.isAtSameMomentAs(DateTime.utc(2026, 11, 17, 11)),
      isTrue,
    );
    expect(summary.daysRemaining, 1);
  });

  test('اشتراک منقضی از وضعیت واقعی API مشخص می‌شود', () {
    final summary = summarizeMemberships([
      {'status': 'expired', 'expires_at': '2026-11-15T12:00:00Z'},
    ], now: now);

    expect(summary.status, MembershipDisplayStatus.expired);
    expect(
      summary.expiresAt?.isAtSameMomentAs(DateTime.utc(2026, 11, 15, 12)),
      isTrue,
    );
  });

  test(
    'مرز expires_at: در همان لحظه منقضی و یک میکروثانیه بعد از شروع فعال',
    () {
      final atBoundary = summarizeMemberships([
        {'status': 'active', 'expires_at': '2026-11-16T12:00:00Z'},
      ], now: now);
      final justAfter = summarizeMemberships([
        {'status': 'active', 'expires_at': '2026-11-16T12:00:00.000001Z'},
      ], now: now);

      expect(atBoundary.status, MembershipDisplayStatus.expired);
      expect(justAfter.status, MembershipDisplayStatus.active);
      expect(justAfter.daysRemaining, 1);
    },
  );

  test('هیچ رکوردی یعنی بدون اشتراک؛ تاریخ/روز ساختگی ندارد', () {
    final summary = summarizeMemberships(const [], now: now);
    expect(summary.status, MembershipDisplayStatus.none);
    expect(summary.expiresAt, isNull);
    expect(summary.daysRemaining, isNull);
  });

  test(
    'تاریخ پایان نامعتبر برای رکورد active به‌جای active/expired، unknown است',
    () {
      final summary = summarizeMemberships([
        {'status': 'active', 'expires_at': 'not-a-date'},
      ], now: now);
      expect(summary.status, MembershipDisplayStatus.unknown);
      expect(summary.expiresAt, isNull);
      expect(summary.daysRemaining, isNull);
    },
  );

  test('نوع نامعتبر expires_at کرش نمی‌کند و به unknown می‌رسد', () {
    final summary = summarizeMemberships([
      {'status': 'active', 'expires_at': 20261117},
    ], now: now);
    expect(summary.status, MembershipDisplayStatus.unknown);
    expect(summary.expiresAt, isNull);
    expect(summary.daysRemaining, isNull);
  });

  test('تاریخ میلادی به جلالی با رقم فارسی تبدیل می‌شود', () {
    expect(formatJalaliDate(DateTime(2026, 3, 21)), '۱ فروردین ۱۴۰۵');
    expect(formatJalaliDate(DateTime(2026, 12, 10)), '۱۹ آذر ۱۴۰۵');
  });
}
