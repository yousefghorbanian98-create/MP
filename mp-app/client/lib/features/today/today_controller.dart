/// کنترلر «برنامهٔ امروز» — Riverpod.
/// قانون G8: اعداد بار/ست/تکرار فقط از API (موتور قواعد) می‌آیند؛ LLM هرگز عدد نمی‌سازد.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

class ExerciseItem {
  const ExerciseItem({
    required this.title,
    required this.sets,
    required this.reps,
    required this.loadPct,
    required this.restSeconds,
    this.done = false,
  });

  final String title;
  final int sets;
  final String reps;
  final int loadPct;
  final int restSeconds;
  final bool done;

  ExerciseItem copyWith({bool? done}) => ExerciseItem(
        title: title,
        sets: sets,
        reps: reps,
        loadPct: loadPct,
        restSeconds: restSeconds,
        done: done ?? this.done,
      );
}

class TodayState {
  const TodayState({required this.exercises, required this.status});

  final List<ExerciseItem> exercises;

  /// draft | approved | pending — فقط approved نمایش داده می‌شود (US-104)
  final String status;

  double get progress {
    if (exercises.isEmpty) return 0;
    return exercises.where((e) => e.done).length / exercises.length;
  }

  TodayState copyWith({List<ExerciseItem>? exercises, String? status}) => TodayState(
        exercises: exercises ?? this.exercises,
        status: status ?? this.status,
      );
}

class TodayController extends Notifier<TodayState> {
  @override
  TodayState build() {
    // دادهٔ نمونه — در نسخهٔ متصل به API از /api/v1/programs می‌آید
    return const TodayState(
      status: 'approved',
      exercises: [
        ExerciseItem(title: 'اسکوات هالتر', sets: 4, reps: '۸-۱۰', loadPct: 70, restSeconds: 90),
        ExerciseItem(title: 'پرس سینه هالتر', sets: 4, reps: '۸-۱۲', loadPct: 65, restSeconds: 90),
        ExerciseItem(title: 'زیربغل سیم‌کش', sets: 3, reps: '۱۰-۱۲', loadPct: 60, restSeconds: 75),
        ExerciseItem(title: 'پرس سرشانه', sets: 3, reps: '۱۰-۱۲', loadPct: 55, restSeconds: 75),
      ],
    );
  }

  void toggle(int index) {
    final list = [...state.exercises];
    list[index] = list[index].copyWith(done: !list[index].done);
    state = state.copyWith(exercises: list);
  }
}

final todayControllerProvider =
    NotifierProvider<TodayController, TodayState>(TodayController.new);
