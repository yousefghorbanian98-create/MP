/// تست‌های کنترلر «برنامهٔ امروز» (اجرا در CI — D-002).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:mp_client/features/today/today_controller.dart';

void main() {
  test('progress starts at zero and updates on toggle', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final initial = container.read(todayControllerProvider);
    expect(initial.status, 'approved');
    expect(initial.progress, 0);

    container.read(todayControllerProvider.notifier).toggle(0);
    final after = container.read(todayControllerProvider);
    expect(after.exercises[0].done, true);
    expect(after.progress, closeTo(0.25, 0.001));
  });

  test('G8: exercises carry numeric load from rule engine fields only', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    for (final ex in container.read(todayControllerProvider).exercises) {
      expect(ex.loadPct, inInclusiveRange(1, 100));
      expect(ex.sets, greaterThan(0));
    }
  });
}
