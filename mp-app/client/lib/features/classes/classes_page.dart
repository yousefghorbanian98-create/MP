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

  Future<void> _book(Map<String, dynamic> cls) async {
    final auth = ref.read(authProvider);
    try {
      final api = ref.read(apiClientProvider);
      final r = await api.post('/classes/book', {
        'class_id': cls['id'],
        'member_id': auth.memberId,
      });
      setState(() =>
          _message = '✅ رزرو شد (${r['status'] == 'waitlisted' ? 'لیست انتظار' : 'تأییدشده'})');
      ref.invalidate(classesProvider);
    } catch (e) {
      setState(() => _message = '⚠ $e');
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
                      _ClassTile(cls: list[i] as Map<String, dynamic>, onBook: _book)
                          .animate()
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
  const _ClassTile({required this.cls, required this.onBook});

  final Map<String, dynamic> cls;
  final void Function(Map<String, dynamic>) onBook;

  @override
  Widget build(BuildContext context) {
    final seats = (cls['seats_left'] as num? ?? 0).toInt();
    final full = seats <= 0;
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
                    '${cls['schedule_text'] ?? ''} — ${full ? 'ظرفیت تکمیل' : '$seats صندلی خالی'}',
                    style: TextStyle(fontSize: 12, color: MpColors.textSecondary),
                  ),
                ],
              ),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                  backgroundColor:
                      full ? MpColors.surface : MpColors.primary),
              onPressed: full ? null : () => onBook(cls),
              child: Text(full ? 'کامل' : 'رزرو'),
            ),
          ],
        ),
      ),
    );
  }
}
