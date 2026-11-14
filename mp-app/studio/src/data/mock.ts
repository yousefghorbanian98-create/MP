/** داده‌های نمایشی (تا اتصال API در M08+) — ساختار هم‌شکل با خروجی /api/v1 */
export interface Kpi {
  id: string;
  label: string;
  value: number;
  unit: string;
  deltaPct: number;
  spark: number[];
}

export interface MemberRow {
  id: number;
  name: string;
  phone: string;
  goal: string;
  status: "active" | "expiring" | "expired";
  daysLeft: number;
  lastSeen: string;
  avatarHue: number;
}

export interface ScheduleItem {
  id: number;
  time: string;
  title: string;
  member: string;
  kind: "assessment" | "workout" | "renewal";
}

export const kpis: Kpi[] = [
  { id: "revenue", label: "درآمد ماه (میلیون ریال)", value: 482, unit: "", deltaPct: 12.4, spark: [30, 38, 32, 45, 42, 55, 61, 58, 70] },
  { id: "attendance", label: "حضور امروز", value: 86, unit: "نفر", deltaPct: 5.2, spark: [40, 44, 52, 48, 60, 58, 66, 72, 86] },
  { id: "retention", label: "نرخ نگه‌داشت", value: 92, unit: "٪", deltaPct: 1.8, spark: [85, 86, 88, 87, 89, 90, 91, 91, 92] },
  { id: "newMembers", label: "اعضای جدید", value: 23, unit: "نفر", deltaPct: -3.1, spark: [18, 22, 25, 21, 28, 26, 24, 25, 23] },
];

export const attendanceSeries = [
  { day: "شنبه", visits: 120, checkins: 108 },
  { day: "یکشنبه", visits: 132, checkins: 121 },
  { day: "دوشنبه", visits: 101, checkins: 94 },
  { day: "سه‌شنبه", visits: 145, checkins: 133 },
  { day: "چهارشنبه", visits: 160, checkins: 149 },
  { day: "پنجشنبه", visits: 178, checkins: 166 },
  { day: "جمعه", visits: 90, checkins: 80 },
];

export const members: MemberRow[] = [
  { id: 1, name: "علی رضایی", phone: "0912 123 4567", goal: "حجم‌سازی", status: "active", daysLeft: 42, lastSeen: "امروز، ۱۷:۴۰", avatarHue: 150 },
  { id: 2, name: "سارا محمدی", phone: "0935 222 8890", goal: "کاهش وزن", status: "expiring", daysLeft: 5, lastSeen: "دیروز، ۱۹:۱۰", avatarHue: 40 },
  { id: 3, name: "رضا کریمی", phone: "0919 555 1122", goal: "آمادگی جسمانی", status: "active", daysLeft: 88, lastSeen: "۲ روز پیش", avatarHue: 210 },
  { id: 4, name: "مریم احمدی", phone: "0903 777 3344", goal: "سلامت عمومی", status: "expired", daysLeft: -3, lastSeen: "۱۰ روز پیش", avatarHue: 330 },
  { id: 5, name: "امیر حسینی", phone: "0912 888 9900", goal: "قدرتی", status: "active", daysLeft: 21, lastSeen: "امروز، ۰۸:۱۵", avatarHue: 265 },
  { id: 6, name: "نگار صادقی", phone: "0990 444 6655", goal: "کاهش وزن", status: "expiring", daysLeft: 7, lastSeen: "۳ روز پیش", avatarHue: 95 },
];

export const schedule: ScheduleItem[] = [
  { id: 1, time: "۰۸:۰۰", title: "ارزیابی ۱۴ دامنه", member: "امیر حسینی", kind: "assessment" },
  { id: 2, time: "۱۰:۳۰", title: "تأیید برنامهٔ تمرین", member: "علی رضایی", kind: "workout" },
  { id: 3, time: "۱۲:۰۰", title: "تمدید اشتراک", member: "سارا محمدی", kind: "renewal" },
  { id: 4, time: "۱۶:۰۰", title: "برنامهٔ هفتگی", member: "رضا کریمی", kind: "workout" },
  { id: 5, time: "۱۸:۳۰", title: "اندازه‌گیری JP7", member: "نگار صادقی", kind: "assessment" },
];
