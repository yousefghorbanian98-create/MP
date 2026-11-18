/// ارقام فارسی و قالب مبلغ — قرارداد مشترک کلاینت (M90).
///
/// پیش‌تر این دو تابع داخل `features/shop/shop_page.dart` بودند و هر صفحهٔ دیگر
/// (chat، wallet، bodycomp) نسخهٔ خصوصی خودش را داشت. رسید سفارش هم همین قالب
/// را لازم داشت، پس منطق به `core` منتقل شد تا «صفحهٔ جدید = کپی‌کردن regex»
/// تکرار نشود. ارقام لاتین در UI فارسی هنوز دیده می‌شوند؛ هر صفحهٔ تازه باید از
/// همین‌جا وارد شود (بازنویسی صفحات قدیمی در دامنهٔ همین loop نیست، تا رگرسیون
/// بصری ناخواسته نسازیم).
library;

/// 1234 ← ۱۲۳۴
String faDigits(Object value) {
  const latin = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
  const persian = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  var out = value.toString();
  for (var i = 0; i < 10; i++) {
    out = out.replaceAll(latin[i], persian[i]);
  }
  return out;
}

/// مبلغ با جداکنندهٔ هزارگان فارسی: 2500000 ← ۲٬۵۰۰٬۰۰۰ ریال
///
/// `unit` برای جاهایی است که واحد دیگری نمایش داده می‌شود؛ مبلغ هرگز در کلاینت
/// محاسبه یا تصحیح نمی‌شود — فقط قالب‌بندی می‌شود (قیمت از سرور می‌آید).
String rial(num amount, {String unit = 'ریال'}) {
  // JSON می‌تواند 5000000.0 بدهد (نه 5000000)؛ «۵٬۰۰۰٬۰۰۰٫۰ ریال» در رسید فقط
  // نویز است، پس عدد صحیحِ double به همان شکل صحیح قالب‌بندی می‌شود.
  final value = amount is! int && amount == amount.roundToDouble() ? amount.toInt() : amount;
  final grouped =
      value.toString().replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]}٬');
  final text = faDigits(grouped);
  return unit.isEmpty ? text : '$text $unit';
}
