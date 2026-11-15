/// تست‌های کنترلر «برنامهٔ امروز» واقعی (اجرا در CI — D-002).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mp_client/features/today/today_controller.dart';

void main() {
  test('progress starts at zero and updates on toggle', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final initial = container.read(todayControllerProvider);
    expect(initial.done, isEmpty);
    expect(initial.progress(4), 0);

    container.read(todayControllerProvider.notifier).toggle(0);
    final after = container.read(todayControllerProvider);
    expect(after.done, {0});
    expect(after.progress(4), closeTo(0.25, 0.001));

    // toggle دوباره = برگشت به حالت انجام‌نشده
    container.read(todayControllerProvider.notifier).toggle(0);
    expect(container.read(todayControllerProvider).done, isEmpty);
  });

  test('progress handles zero-total safely (no division by zero)', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    expect(container.read(todayControllerProvider).progress(0), 0);
  });

  test('reset clears done set', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    container.read(todayControllerProvider.notifier).toggle(1);
    container.read(todayControllerProvider.notifier).reset();
    expect(container.read(todayControllerProvider).done, isEmpty);
  });
}
