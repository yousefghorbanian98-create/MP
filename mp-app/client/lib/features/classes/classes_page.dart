/// کلاس‌های واقعی — لیست/ظرفیت/رزرو از API (M32).
library;

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class ClassesPage extends ConsumerStatefulWidget {
  const ClassesPage({super.key});

  @override
  ConsumerState<ClassesPage> createState() => _ClassesPageState();
}

class _ClassesPageState extends ConsumerState<ClassesPage> {
  String? _message;
  final Set<int> _busyClassIds = {};

  Future<void> _book(Map<String, dynamic> cls) async {
    final memberId = ref.read(authProvider).memberId;
    final classId = (cls['id'] as num?)?.toInt();
    if (memberId == null || classId == null) {
      setState(() => _message = 'اطلاعات نشست یا کلاس برای رزرو نامعتبر است');
      return;
    }
    if (_busyClassIds.contains(classId)) return;
    setState(() => _busyClassIds.add(classId));
    try {
      final r = await ref.read(apiClientProvider).post('/classes/book', {
        'class_id': classId,
        'member_id': memberId,
      });
      if (!mounted) return;
      setState(() => _message =
          '✅ رزرو شد (${r is Map && r['status'] == 'waitlisted' ? 'لیست انتظار' : 'تأییدشده'})');
      ref.invalidate(classesProvider);
    } catch (e) {
      if (!mounted) return;
      setState(() => _message = '⚠ $e');
      ref.invalidate(classesProvider);
    } finally {
      if (mounted) setState(() => _busyClassIds.remove(classId));
    }
  }

  Future<void> _cancel(Map<String, dynamic> cls) async {
    final memberId = ref.read(authProvider).memberId;
    final classId = (cls['id'] as num?)?.toInt();
    if (memberId == null || classId == null) {
      setState(() => _message = 'اطلاعات نشست یا کلاس برای لغو رزرو نامعتبر است');
      return;
    }
    if (_busyClassIds.contains(classId)) return;
    setState(() => _busyClassIds.add(classId));
    try {
      final response = await ref.read(apiClientProvider).post('/classes/cancel', {
        'class_id': classId,
        'member_id': memberId,
      });
      if (!mounted) return;
      final status = response is Map ? response['status'] : null;
      setState(() => _message = status == 'cancelled' ? '✅ رزرو لغو شد' : '✅ درخواست لغو ثبت شد');
      ref.invalidate(classesProvider);
    } catch (e) {
      if (!mounted) return;
      setState(() => _message = '⚠ لغو انجام نشد: $e');
      // رزرو ممکن است از نشست دیگری لغو شده باشد؛ از API وضعیت تازه بگیر.
      ref.invalidate(classesProvider);
    } finally {
      if (mounted) setState(() => _busyClassIds.remove(classId));
    }
  }

  @override
  Widget build(BuildContext context) {
    final classes = ref.watch(classesProvider);
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () async => ref.invalidate(classesProvider),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Text(_message!,
                    style: const TextStyle(color: MpColors.primaryLight)),
              ),
            classes.when(
              loading: () => const Center(
                  child: Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              )),
              error: (e, _) => GlassCard(
                  child: Text('خطا در دریافت کلاس‌ها: $e',
                      textAlign: TextAlign.center)),
              data: (list) {
                if (list.isEmpty) {
                  return const GlassCard(
                      child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('کلاسی ثبت نشده است',
                        textAlign: TextAlign.center),
                  ));
                }
                return Column(
                  children: [
                    for (var i = 0; i < list.length; i++)
                      _ClassTile(
                        cls: list[i] as Map<String, dynamic>,
                        onBook: _book,
                        onCancel: _cancel,
                        isBusy: _busyClassIds.contains(
                          ((list[i] as Map<String, dynamic>)['id'] as num?)?.toInt(),
                        ),
                      ).animate()
                          .fadeIn(delay: (70 * i).ms)
                          .slideY(begin: 0.1),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ClassTile extends StatelessWidget {
  const _ClassTile({
    required this.cls,
    required this.onBook,
    required this.onCancel,
    required this.isBusy,
  });

  final Map<String, dynamic> cls;
  final void Function(Map<String, dynamic>) onBook;
  final void Function(Map<String, dynamic>) onCancel;
  final bool isBusy;

  @override
  Widget build(BuildContext context) {
    final seats = (cls['seats_left'] as num? ?? 0).toInt();
    final full = seats <= 0;
    final bookingStatus = cls['member_booking_status'];
    final booked = bookingStatus == 'confirmed' || bookingStatus == 'waitlisted';
    final details = <String>[
      if (cls['schedule_text'] is String && (cls['schedule_text'] as String).isNotEmpty)
        cls['schedule_text'] as String,
      full ? 'ظرفیت تکمیل' : '$seats صندلی خالی',
      if (bookingStatus == 'confirmed') 'رزرو شما تأیید شده',
      if (bookingStatus == 'waitlisted') 'شما در لیست انتظار هستید',
    ].join(' · ');
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        child: Row(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: MpColors.primary.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.groups, color: MpColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(cls['name'] as String? ?? 'کلاس',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 3),
                  Text(
                    details,
                    style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
                  ),
                ],
              ),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: booked
                    ? MpColors.accent
                    : full
                        ? MpColors.surface
                        : MpColors.primary,
              ),
              onPressed: isBusy
                  ? null
                  : booked
                      ? () => onCancel(cls)
                      : full
                          ? null
                          : () => onBook(cls),
              child: Text(
                isBusy
                    ? 'در حال…'
                    : booked
                        ? bookingStatus == 'waitlisted'
                            ? 'لغو انتظار'
                            : 'لغو رزرو'
                        : full
                            ? 'کامل'
                            : 'رزرو',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
