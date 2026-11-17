/// اشتراک عضو: اعتبارسنجی تاریخ پایان و تبدیل وضعیت برای نمایش خانه.
library;

enum MembershipDisplayStatus { active, expired, none, unknown }

class MembershipSummary {
  const MembershipSummary({
    required this.status,
    this.membership,
    this.expiresAt,
    this.daysRemaining,
  });

  final MembershipDisplayStatus status;
  final Map<String, dynamic>? membership;
  final DateTime? expiresAt;
  final int? daysRemaining;
}

/// Timestamp سرور را به instant UTC تبدیل می‌کند.
///
/// DB SQLite ممکن است offset را حذف کند؛ timestamp بدون timezone در قرارداد
/// membership به UTC تعبیر می‌شود، نه timezone تصادفی دستگاه.
DateTime? parseMembershipExpiry(String? iso) {
  if (iso == null || iso.trim().isEmpty) return null;
  var value = iso.trim();
  if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(value)) {
    value = '${value}T00:00:00Z';
  } else if (!RegExp(r'(?:[zZ]|[+-]\d{2}:?\d{2})$').hasMatch(value)) {
    value = '${value}Z';
  }
  return DateTime.tryParse(value)?.toUtc();
}

/// روزهای باقی‌مانده تا پایان اشتراک، با گردکردن به بالا.
///
/// null یا تاریخ نامعتبر = «نامعلوم»، تاریخ گذشته/همین لحظه = صفر.
/// [now] برای تست تزریق می‌شود.
int? daysUntilExpiry(String? iso, {DateTime? now}) {
  final expires = parseMembershipExpiry(iso);
  if (expires == null) return null;
  final remainingMicros = expires.difference((now ?? DateTime.now()).toUtc()).inMicroseconds;
  if (remainingMicros <= 0) return 0;
  const microsPerDay = 86400000000;
  return (remainingMicros + microsPerDay - 1) ~/ microsPerDay;
}

DateTime? _membershipExpiry(Map<String, dynamic> row) {
  final value = row['expires_at'];
  return parseMembershipExpiry(value is String ? value : null);
}

/// وضعیت را از تاریخچهٔ واقعی API می‌سازد؛ متن یا روز ساختگی تولید نمی‌کند.
MembershipSummary summarizeMemberships(
  List<Map<String, dynamic>> rows, {
  DateTime? now,
}) {
  final nowUtc = (now ?? DateTime.now()).toUtc();
  final activeRows = <MapEntry<Map<String, dynamic>, DateTime>>[];
  Map<String, dynamic>? unparseableActiveRow;

  for (final row in rows) {
    if (row['status'] != 'active') continue;
    final expiry = _membershipExpiry(row);
    if (expiry == null) {
      unparseableActiveRow ??= row;
    } else if (expiry.isAfter(nowUtc)) {
      activeRows.add(MapEntry(row, expiry));
    }
  }

  // اگر چند رکورد active برگشت، رکورد دارای بیشترین اعتبار آینده نمایش داده شود.
  if (activeRows.isNotEmpty) {
    activeRows.sort((a, b) => b.value.compareTo(a.value));
    final current = activeRows.first;
    return MembershipSummary(
      status: MembershipDisplayStatus.active,
      membership: current.key,
      expiresAt: current.value,
      daysRemaining: daysUntilExpiry(current.value.toIso8601String(), now: nowUtc),
    );
  }

  // رکورد active با تاریخ نامعتبر ممکن است معتبر باشد؛ آن را اشتباه «منقضی» نکن.
  if (unparseableActiveRow != null) {
    return MembershipSummary(
      status: MembershipDisplayStatus.unknown,
      membership: unparseableActiveRow,
    );
  }

  final expiredRows = <MapEntry<Map<String, dynamic>, DateTime?>>[];
  for (final row in rows) {
    final status = row['status'];
    final expiry = _membershipExpiry(row);
    if (status == 'expired' || (status == 'active' && expiry != null)) {
      expiredRows.add(MapEntry(row, expiry));
    }
  }
  if (expiredRows.isNotEmpty) {
    expiredRows.sort((a, b) {
      if (a.value == null) return b.value == null ? 0 : 1;
      if (b.value == null) return -1;
      return b.value!.compareTo(a.value!);
    });
    final latest = expiredRows.first;
    return MembershipSummary(
      status: MembershipDisplayStatus.expired,
      membership: latest.key,
      expiresAt: latest.value,
    );
  }

  if (rows.isEmpty || rows.every((row) => row['status'] == 'cancelled')) {
    return const MembershipSummary(status: MembershipDisplayStatus.none);
  }
  return const MembershipSummary(status: MembershipDisplayStatus.unknown);
}

/// تاریخ میلادی محلی را با تقویم جلالی و رقم‌های فارسی نمایش می‌دهد.
String formatJalaliDate(DateTime date) {
  final (year, month, day) = _toJalali(date.year, date.month, date.day);
  final label = '$day ${_jalaliMonths[month - 1]} $year';
  return label.replaceAllMapped(RegExp(r'\d'), (match) {
    return _persianDigits[int.parse(match.group(0)!)];
  });
}

const _persianDigits = '۰۱۲۳۴۵۶۷۸۹';
const _jalaliMonths = <String>[
  'فروردین',
  'اردیبهشت',
  'خرداد',
  'تیر',
  'مرداد',
  'شهریور',
  'مهر',
  'آبان',
  'آذر',
  'دی',
  'بهمن',
  'اسفند',
];

(int, int, int) _toJalali(int gy, int gm, int gd) {
  const gDayMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  final gy2 = gm > 2 ? gy + 1 : gy;
  var days =
      355666 +
      (365 * gy) +
      ((gy2 + 3) ~/ 4) -
      ((gy2 + 99) ~/ 100) +
      ((gy2 + 399) ~/ 400) +
      gd +
      gDayMonth[gm - 1];

  var jy = -1595 + 33 * (days ~/ 12053);
  days %= 12053;
  jy += 4 * (days ~/ 1461);
  days %= 1461;
  if (days > 365) {
    jy += (days - 1) ~/ 365;
    days = (days - 1) % 365;
  }

  if (days < 186) {
    final jm = 1 + days ~/ 31;
    final jd = 1 + days % 31;
    return (jy, jm, jd);
  }
  final jm = 7 + (days - 186) ~/ 30;
  final jd = 1 + (days - 186) % 30;
  return (jy, jm, jd);
}
