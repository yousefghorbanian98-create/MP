/// «برنامهٔ امروز» واقعی — تمرین‌های روز از برنامهٔ موتور + ثبت انجام‌شده‌ها.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';

class TodayState {
  const TodayState({this.done = const {}});
  final Set<int> done;
  double progress(int total) => total == 0 ? 0 : done.length / total;
  TodayState copyWith({Set<int>? done}) => TodayState(done: done ?? this.done);
}

class TodayController extends StateNotifier<TodayState> {
  TodayController(this.ref) : super(const TodayState());
  final Ref ref;

  void toggle(int index) {
    final s = Set<int>.from(state.done);
    s.contains(index) ? s.remove(index) : s.add(index);
    state = TodayState(done: s);
  }

  void reset() => state = const TodayState();
}

final todayControllerProvider =
    StateNotifierProvider<TodayController, TodayState>((ref) => TodayController(ref));

/// تمرین‌های امروز از برنامهٔ واقعی.
final todayWorkoutProvider = Provider<List<Map<String, dynamic>>>((ref) {
  return ref.watch(todayExercisesProvider);
});
